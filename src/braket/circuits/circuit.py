# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from numbers import Number
from typing import Any, TypeVar

import numpy as np
import oqpy
from sympy import Expr

from braket.circuits import compiler_directives
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.measure import Measure
from braket.circuits.moments import Moments, MomentType
from braket.circuits.noise import Noise
from braket.circuits.noise_helpers import (
    apply_noise_to_gates,
    apply_noise_to_moments,
    check_noise_target_gates,
    check_noise_target_qubits,
    check_noise_target_unitary,
    wrap_with_list,
)
from braket.circuits.observable import Observable
from braket.circuits.observables import TensorProduct
from braket.circuits.parameterizable import Parameterizable
from braket.circuits.result_type import (
    ObservableParameterResultType,
    ObservableResultType,
    ResultType,
)
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
    SerializationProperties,
)
from braket.circuits.text_diagram_builders.unicode_circuit_diagram import UnicodeCircuitDiagram
from braket.circuits.unitary_calculation import calculate_unitary_big_endian
from braket.default_simulator.openqasm.interpreter import Interpreter
from braket.ir.jaqcd import Program as JaqcdProgram
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.ir.openqasm.program_v1 import io_type
from braket.pulse.ast.qasm_parser import ast_to_qasm
from braket.pulse.frame import Frame
from braket.pulse.pulse_sequence import PulseSequence, _validate_uniqueness
from braket.pulse.waveforms import Waveform
from braket.registers.qubit import QubitInput
from braket.registers.qubit_set import QubitSet, QubitSetInput

SubroutineReturn = TypeVar(
    "SubroutineReturn", Iterable[Instruction], Instruction, ResultType, Iterable[ResultType]
)
SubroutineCallable = TypeVar("SubroutineCallable", bound=Callable[..., SubroutineReturn])
AddableTypes = TypeVar("AddableTypes", SubroutineReturn, SubroutineCallable)


class Circuit:  # noqa: PLR0904
    """A representation of a quantum circuit that contains the instructions to be performed on a
    quantum device and the requested result types.

    See :mod:`braket.circuits.gates` module for all of the supported instructions.

    See :mod:`braket.circuits.result_types` module for all of the supported result types.

    `AddableTypes` are `Instruction`, iterable of `Instruction`, `ResultType`,
    iterable of `ResultType`, or `SubroutineCallable`
    """

    _ALL_QUBITS = "ALL"  # Flag to indicate all qubits in _qubit_observable_mapping

    @classmethod
    def register_subroutine(cls, func: SubroutineCallable) -> None:
        """Register the subroutine `func` as an attribute of the `Circuit` class. The attribute name
        is the name of `func`.

        Args:
            func (SubroutineCallable): The function of the subroutine to add to the class.

        Examples:
            >>> def h_on_all(target):
            ...     circ = Circuit()
            ...     for qubit in target:
            ...         circ += Instruction(Gate.H(), qubit)
            ...     return circ
            >>> Circuit.register_subroutine(h_on_all)
            >>> circ = Circuit().h_on_all(range(2))
            >>> for instr in circ.instructions:
            ...     print(instr)
            Instruction('operator': 'H', 'target': QubitSet(Qubit(0),))
            Instruction('operator': 'H', 'target': QubitSet(Qubit(1),))
        """

        def method_from_subroutine(self, *args, **kwargs) -> SubroutineReturn:  # noqa: ANN001
            return self.add(func, *args, **kwargs)

        function_name = func.__name__
        setattr(cls, function_name, method_from_subroutine)

        function_attr = getattr(cls, function_name)
        function_attr.__doc__ = func.__doc__

    def __init__(self, addable: AddableTypes | None = None, *args, **kwargs):
        """Inits a `Circuit`.

        Args:
            addable (AddableTypes | None): The item(s) to add to self.
                Default = None.

        Raises:
            TypeError: If `addable` is an unsupported type.

        Examples:
            >>> circ = Circuit([Instruction(Gate.H(), 4), Instruction(Gate.CNot(), [4, 5])])
            >>> circ = Circuit().h(0).cnot(0, 1)
            >>> circ = Circuit().h(0).cnot(0, 1).probability([0, 1])

            >>> @circuit.subroutine(register=True)
            >>> def bell_pair(target):
            ...     return Circ().h(target[0]).cnot(target[0:2])
            >>> circ = Circuit(bell_pair, [4, 5])
            >>> circ = Circuit().bell_pair([4, 5])

        """
        self._moments: Moments = Moments()
        self._result_types: dict[ResultType] = {}
        self._qubit_observable_mapping: dict[int | Circuit._ALL_QUBITS, Observable] = {}
        self._qubit_observable_target_mapping: dict[int, tuple[int]] = {}
        self._qubit_observable_set = set()
        self._parameters = set()
        self._observables_simultaneously_measurable = True
        self._has_compiler_directives = False
        self._measure_targets = None

        if addable is not None:
            self.add(addable, *args, **kwargs)

    @property
    def depth(self) -> int:
        """int: Get the circuit depth."""
        return self._moments.depth

    @property
    def global_phase(self) -> float:
        """float: Get the global phase of the circuit."""
        return sum(
            instr.operator.angle
            for moment, instr in self._moments.items()
            if moment.moment_type == MomentType.GLOBAL_PHASE
        )

    @property
    def instructions(self) -> list[Instruction]:
        """Iterable[Instruction]: Get an `iterable` of instructions in the circuit."""
        return list(self._moments.values())

    @property
    def result_types(self) -> list[ResultType]:
        """list[ResultType]: Get a list of requested result types in the circuit."""
        return list(self._result_types.keys())

    @property
    def basis_rotation_instructions(self) -> list[Instruction]:
        """Gets a list of basis rotation instructions.

        Returns:
            list[Instruction]: Get a list of basis rotation instructions in the circuit.
            These basis rotation instructions are added if result types are requested for
            an observable other than Pauli-Z.

            This only makes sense if all observables are simultaneously measurable;
            if not, this method will return an empty list.
        """
        # Note that basis_rotation_instructions can change each time a new instruction
        # is added to the circuit because `self._moments.qubits` would change
        basis_rotation_instructions = []
        if all_qubit_observable := self._qubit_observable_mapping.get(Circuit._ALL_QUBITS):
            for target in self.qubits:
                basis_rotation_instructions += Circuit._observable_to_instruction(
                    all_qubit_observable, target
                )
            return basis_rotation_instructions

        target_lists = sorted(set(self._qubit_observable_target_mapping.values()))
        for target_list in target_lists:
            observable = self._qubit_observable_mapping[target_list[0]]
            basis_rotation_instructions += Circuit._observable_to_instruction(
                observable, target_list
            )
        return basis_rotation_instructions

    @staticmethod
    def _observable_to_instruction(
        observable: Observable, target_list: list[int]
    ) -> list[Instruction]:
        return [Instruction(gate, target_list) for gate in observable.basis_rotation_gates]

    @property
    def moments(self) -> Moments:
        """Moments: Get the `moments` for this circuit. Note that this includes observables."""
        return self._moments

    @property
    def qubit_count(self) -> int:
        """Get the qubit count for this circuit. Note that this includes observables.

        Returns:
            int: The qubit count for this circuit.
        """
        all_qubits = self._moments.qubits.union(self._qubit_observable_set)
        return len(all_qubits)

    @property
    def qubits(self) -> QubitSet:
        """QubitSet: Get a copy of the qubits for this circuit."""
        return QubitSet(self._moments.qubits.union(self._qubit_observable_set))

    @property
    def parameters(self) -> set[FreeParameter]:
        """Gets a set of the parameters in the Circuit.

        Returns:
            set[FreeParameter]: The `FreeParameters` in the Circuit.
        """
        return self._parameters

    def add_result_type(
        self,
        result_type: ResultType,
        target: QubitSetInput | None = None,
        target_mapping: dict[QubitInput, QubitInput] | None = None,
    ) -> Circuit:
        """Add a requested result type to `self`, returns `self` for chaining ability.

        Args:
            result_type (ResultType): `ResultType` to add into `self`.
            target (QubitSetInput | None): Target qubits for the
                `result_type`.
                Default = `None`.
            target_mapping (dict[QubitInput, QubitInput] | None): A dictionary of
                qubit mappings to apply to the `result_type.target`. Key is the qubit in
                `result_type.target` and the value is what the key will be changed to.
                Default = `None`.


        Returns:
            Circuit: self

        Note:
            Target and target_mapping will only be applied to those requested result types with
            the attribute `target`. The result_type will be appended to the end of the dict keys of
            `circuit.result_types` only if it does not already exist in `circuit.result_types`

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.
            ValueError: If a measure instruction exists on the current circuit.

        Examples:
            >>> result_type = ResultType.Probability(target=[0, 1])
            >>> circ = Circuit().add_result_type(result_type)
            >>> print(circ.result_types[0])
            Probability(target=QubitSet([Qubit(0), Qubit(1)]))

            >>> result_type = ResultType.Probability(target=[0, 1])
            >>> circ = Circuit().add_result_type(result_type, target_mapping={0: 10, 1: 11})
            >>> print(circ.result_types[0])
            Probability(target=QubitSet([Qubit(10), Qubit(11)]))

            >>> result_type = ResultType.Probability(target=[0, 1])
            >>> circ = Circuit().add_result_type(result_type, target=[10, 11])
            >>> print(circ.result_types[0])
            Probability(target=QubitSet([Qubit(10), Qubit(11)]))

            >>> result_type = ResultType.StateVector()
            >>> circ = Circuit().add_result_type(result_type)
            >>> print(circ.result_types[0])
            StateVector()
        """
        if target_mapping and target is not None:
            raise TypeError("Only one of 'target_mapping' or 'target' can be supplied.")

        if self._measure_targets:
            raise ValueError(
                "cannot add a result type to a circuit which already contains a "
                "measure instruction."
            )

        if not target_mapping and not target:
            # Nothing has been supplied, add result_type
            result_type_to_add = result_type
        elif target_mapping:
            # Target mapping has been supplied, copy result_type
            result_type_to_add = result_type.copy(target_mapping=target_mapping)
        else:
            # ResultType with target
            result_type_to_add = result_type.copy(target=target)

        if result_type_to_add not in self._result_types:
            observable = Circuit._extract_observable(result_type_to_add)
            # We can skip this for now for AdjointGradient (the only subtype of this
            # type) because AdjointGradient can only be used when `shots=0`, and the
            # qubit_observable_mapping is used to generate basis rotation instructions
            # and make sure the observables mutually commute for `shots>0` mode.
            supports_basis_rotation_instructions = not isinstance(
                result_type_to_add, ObservableParameterResultType
            )
            if (
                observable
                and self._observables_simultaneously_measurable
                and supports_basis_rotation_instructions
            ):
                # Only check if all observables can be simultaneously measured
                self._add_to_qubit_observable_mapping(observable, result_type_to_add.target)

            self._add_to_qubit_observable_set(result_type_to_add)
            # using dict as an ordered set, value is arbitrary
            self._result_types[result_type_to_add] = None
        return self

    @staticmethod
    def _extract_observable(result_type: ResultType) -> Observable | None:
        if isinstance(result_type, ResultType.Probability):
            return Observable.Z()  # computational basis
        if isinstance(result_type, ObservableResultType):
            return result_type.observable
        return None

    def _add_to_qubit_observable_mapping(
        self, observable: Observable, observable_target: QubitSet
    ) -> None:
        targets = observable_target or list(self._qubit_observable_set)
        all_qubits_observable = self._qubit_observable_mapping.get(Circuit._ALL_QUBITS)
        tensor_product_dict = (
            Circuit._tensor_product_index_dict(observable, observable_target)
            if isinstance(observable, TensorProduct)
            else None
        )
        identity = Observable.I()
        for i in range(len(targets)):
            target = targets[i]
            new_observable = tensor_product_dict[i][0] if tensor_product_dict else observable
            current_observable = all_qubits_observable or self._qubit_observable_mapping.get(target)

            add_observable = not current_observable or (
                current_observable == identity and new_observable != identity
            )
            if (
                not add_observable  # noqa: PLR1714
                and identity != current_observable
                and identity != new_observable
                and current_observable != new_observable
            ):
                return self._encounter_noncommuting_observable()

            if observable_target:
                new_targets = (
                    tensor_product_dict[i][1] if tensor_product_dict else tuple(observable_target)
                )

                if add_observable:
                    self._qubit_observable_target_mapping[target] = new_targets
                    self._qubit_observable_mapping[target] = new_observable
                elif new_observable.qubit_count > 1:
                    current_target = self._qubit_observable_target_mapping.get(target)
                    if current_target and current_target != new_targets:
                        return self._encounter_noncommuting_observable()

        if not observable_target and observable != identity:
            if all_qubits_observable and all_qubits_observable != observable:
                return self._encounter_noncommuting_observable()
            self._qubit_observable_mapping[Circuit._ALL_QUBITS] = observable
        return None

    @staticmethod
    def _tensor_product_index_dict(
        observable: TensorProduct, observable_target: QubitSet
    ) -> dict[int, tuple[Observable, tuple[int, ...]]]:
        obj_dict = {}
        i = 0
        factors = list(observable.factors)
        total = factors[0].qubit_count
        while factors:
            if i >= total:
                factors.pop(0)
                if factors:
                    total += factors[0].qubit_count
            if factors:
                first = total - factors[0].qubit_count
                obj_dict[i] = (factors[0], tuple(observable_target[first:total]))
            i += 1
        return obj_dict

    def _add_to_qubit_observable_set(self, result_type: ResultType) -> None:
        if isinstance(result_type, ObservableResultType) and result_type.target:
            self._qubit_observable_set.update(result_type.target)

    def _check_if_qubit_measured(
        self,
        instruction: Instruction,
        target: QubitSetInput | None = None,
        target_mapping: dict[QubitInput, QubitInput] | None = None,
    ) -> None:
        """Checks if the target qubits are measured. If the qubit is already measured
        the instruction will not be added to the Circuit.

        Args:
            instruction (Instruction): `Instruction` to add into `self`.
            target (QubitSetInput | None): Target qubits for the
                `instruction`. If a single qubit gate, an instruction is created for every index
                in `target`.
                Default = `None`.
            target_mapping (dict[QubitInput, QubitInput] | None): A dictionary of
                qubit mappings to apply to the `instruction.target`. Key is the qubit in
                `instruction.target` and the value is what the key will be changed to.
                Default = `None`.

        Raises:
            ValueError: If adding a gate or noise operation after a measure instruction.
        """
        if self._measure_targets:
            measure_on_target_mapping = target_mapping and any(
                targ in self._measure_targets for targ in target_mapping.values()
            )
            if (
                # check if there is a measure instruction on the targeted qubit(s)
                measure_on_target_mapping
                or any(tar in self._measure_targets for tar in QubitSet(target))
                or any(tar in self._measure_targets for tar in QubitSet(instruction.target))
            ):
                raise ValueError("cannot apply instruction to measured qubits.")

    def add_instruction(
        self,
        instruction: Instruction,
        target: QubitSetInput | None = None,
        target_mapping: dict[QubitInput, QubitInput] | None = None,
    ) -> Circuit:
        """Add an instruction to `self`, returns `self` for chaining ability.

        Args:
            instruction (Instruction): `Instruction` to add into `self`.
            target (QubitSetInput | None): Target qubits for the
                `instruction`. If a single qubit gate, an instruction is created for every index
                in `target`.
                Default = `None`.
            target_mapping (dict[QubitInput, QubitInput] | None): A dictionary of
                qubit mappings to apply to the `instruction.target`. Key is the qubit in
                `instruction.target` and the value is what the key will be changed to.
                Default = `None`.

        Returns:
            Circuit: self

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.
            ValueError: If adding a gate or noise after a measure instruction.

        Examples:
            >>> instr = Instruction(Gate.CNot(), [0, 1])
            >>> circ = Circuit().add_instruction(instr)
            >>> print(circ.instructions[0])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(0), Qubit(1)))

            >>> instr = Instruction(Gate.CNot(), [0, 1])
            >>> circ = Circuit().add_instruction(instr, target_mapping={0: 10, 1: 11})
            >>> print(circ.instructions[0])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))

            >>> instr = Instruction(Gate.CNot(), [0, 1])
            >>> circ = Circuit().add_instruction(instr, target=[10, 11])
            >>> print(circ.instructions[0])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))

            >>> instr = Instruction(Gate.H(), 0)
            >>> circ = Circuit().add_instruction(instr, target=[10, 11])
            >>> print(circ.instructions[0])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(10),))
            >>> print(circ.instructions[1])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(11),))
        """
        if target_mapping and target is not None:
            raise TypeError("Only one of 'target_mapping' or 'target' can be supplied.")

        # Check if there is a measure instruction on the circuit
        self._check_if_qubit_measured(instruction, target, target_mapping)

        # Update measure targets if instruction is a measurement
        if isinstance(instruction.operator, Measure):
            measure_target = target or instruction.target[0]
            self._measure_targets = (self._measure_targets or []) + [measure_target]

        if not target_mapping and not target:
            # Nothing has been supplied, add instruction
            instructions_to_add = [instruction]
        elif target_mapping:
            # Target mapping has been supplied, copy instruction
            instructions_to_add = [instruction.copy(target_mapping=target_mapping)]
        elif hasattr(instruction.operator, "qubit_count") and instruction.operator.qubit_count == 1:
            # single qubit operator with target, add an instruction for each target
            instructions_to_add = [instruction.copy(target=qubit) for qubit in target]
        else:
            # non single qubit operator with target, add instruction with target
            instructions_to_add = [instruction.copy(target=target)]

        if self._check_for_params(instruction):
            for param in instruction.operator.parameters:
                if isinstance(param, FreeParameterExpression) and isinstance(
                    param.expression, Expr
                ):
                    free_params = param.expression.free_symbols
                    for parameter in free_params:
                        self._parameters.add(FreeParameter(parameter.name))
        self._moments.add(instructions_to_add)

        return self

    def _check_for_params(self, instruction: Instruction) -> bool:
        """This checks for free parameters in an :class:{Instruction}. Checks children classes of
        :class:{Parameterizable}.

        Args:
            instruction (Instruction): The instruction to check for a
                :class:{FreeParameterExpression}.

        Returns:
            bool: Whether an object is parameterized.
        """
        return issubclass(type(instruction.operator), Parameterizable) and any(
            issubclass(type(param), FreeParameterExpression)
            for param in instruction.operator.parameters
        )

    def add_circuit(
        self,
        circuit: Circuit,
        target: QubitSetInput | None = None,
        target_mapping: dict[QubitInput, QubitInput] | None = None,
    ) -> Circuit:
        """Add a `Circuit` to `self`, returning `self` for chaining ability.

        Args:
            circuit (Circuit): Circuit to add into self.
            target (QubitSetInput | None): Target qubits for the
                supplied circuit. This is a macro over `target_mapping`; `target` is converted to
                a `target_mapping` by zipping together a sorted `circuit.qubits` and `target`.
                Default = `None`.
            target_mapping (dict[QubitInput, QubitInput] | None): A dictionary of
                qubit mappings to apply to the qubits of `circuit.instructions`. Key is the qubit
                to map, and the value is what to change it to. Default = `None`.

        Returns:
            Circuit: self

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.

        Note:
            Supplying `target` sorts `circuit.qubits` to have deterministic behavior since
            `circuit.qubits` ordering is based on how instructions are inserted.
            Use caution when using this with circuits that with a lot of qubits, as the sort
            can be resource-intensive. Use `target_mapping` to use a linear runtime to remap
            the qubits.

            Requested result types of the circuit that will be added will be appended to the end
            of the list for the existing requested result types. A result type to be added that is
            equivalent to an existing requested result type will not be added.

        Examples:
            >>> widget = Circuit().h(0).cnot(0, 1)
            >>> circ = Circuit().add_circuit(widget)
            >>> instructions = list(circ.instructions)
            >>> print(instructions[0])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(0),))
            >>> print(instructions[1])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(0), Qubit(1)))

            >>> widget = Circuit().h(0).cnot(0, 1)
            >>> circ = Circuit().add_circuit(widget, target_mapping={0: 10, 1: 11})
            >>> instructions = list(circ.instructions)
            >>> print(instructions[0])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(10),))
            >>> print(instructions[1])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))

            >>> widget = Circuit().h(0).cnot(0, 1)
            >>> circ = Circuit().add_circuit(widget, target=[10, 11])
            >>> instructions = list(circ.instructions)
            >>> print(instructions[0])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(10),))
            >>> print(instructions[1])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))
        """
        if target_mapping and target is not None:
            raise TypeError("Only one of 'target_mapping' or 'target' can be supplied.")
        if target is not None:
            keys = sorted(circuit.qubits)
            values = target
            target_mapping = dict(zip(keys, values))

        for instruction in circuit.instructions:
            self.add_instruction(instruction, target_mapping=target_mapping)

        for result_type in circuit.result_types:
            self.add_result_type(result_type, target_mapping=target_mapping)

        return self

    def add_verbatim_box(
        self,
        verbatim_circuit: Circuit,
        target: QubitSetInput | None = None,
        target_mapping: dict[QubitInput, QubitInput] | None = None,
    ) -> Circuit:
        """Add a verbatim `Circuit` to `self`, ensuring that the circuit is not modified in
        any way by the compiler.

        Args:
            verbatim_circuit (Circuit): Circuit to add into self.
            target (QubitSetInput | None): Target qubits for the
                supplied circuit. This is a macro over `target_mapping`; `target` is converted to
                a `target_mapping` by zipping together a sorted `circuit.qubits` and `target`.
                Default = `None`.
            target_mapping (dict[QubitInput, QubitInput] | None): A dictionary of
                qubit mappings to apply to the qubits of `circuit.instructions`. Key is the qubit
                to map, and the value is what to change it to. Default = `None`.

        Returns:
            Circuit: self

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.
            ValueError: If `circuit` has result types attached

        Examples:
            >>> widget = Circuit().h(0).h(1)
            >>> circ = Circuit().add_verbatim_box(widget)
            >>> print(list(circ.instructions))
            [Instruction('operator': StartVerbatimBox, 'target': QubitSet([])),
             Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)])),
             Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(1)])),
             Instruction('operator': EndVerbatimBox, 'target': QubitSet([]))]

            >>> widget = Circuit().h(0).cnot(0, 1)
            >>> circ = Circuit().add_verbatim_box(widget, target_mapping={0: 10, 1: 11})
            >>> print(list(circ.instructions))
            [Instruction('operator': StartVerbatimBox, 'target': QubitSet([])),
             Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(10)])),
             Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(11)])),
             Instruction('operator': EndVerbatimBox, 'target': QubitSet([]))]

            >>> widget = Circuit().h(0).cnot(0, 1)
            >>> circ = Circuit().add_verbatim_box(widget, target=[10, 11])
            >>> print(list(circ.instructions))
            [Instruction('operator': StartVerbatimBox, 'target': QubitSet([])),
             Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(10)])),
             Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(11)])),
             Instruction('operator': EndVerbatimBox, 'target': QubitSet([]))]
        """
        if target_mapping and target is not None:
            raise TypeError("Only one of 'target_mapping' or 'target' can be supplied.")
        if target is not None:
            keys = sorted(verbatim_circuit.qubits)
            values = target
            target_mapping = dict(zip(keys, values))

        if verbatim_circuit.result_types:
            raise ValueError("Verbatim subcircuit is not measured and cannot have result types")

        if verbatim_circuit._measure_targets:
            raise ValueError("cannot measure a subcircuit inside a verbatim box.")

        if verbatim_circuit.instructions:
            self.add_instruction(Instruction(compiler_directives.StartVerbatimBox()))
            for instruction in verbatim_circuit.instructions:
                self.add_instruction(instruction, target_mapping=target_mapping)
            self.add_instruction(Instruction(compiler_directives.EndVerbatimBox()))
            self._has_compiler_directives = True
        return self

    def _add_measure(self, target_qubits: QubitSetInput) -> None:
        """Adds a measure instruction to the the circuit

        Args:
            target_qubits (QubitSetInput): target qubits to measure.
        """
        for idx, target in enumerate(target_qubits):
            num_qubits_measured = (
                len(self._measure_targets)
                if self._measure_targets and len(target_qubits) == 1
                else 0
            )
            self.add_instruction(
                Instruction(
                    operator=Measure(index=idx + num_qubits_measured),
                    target=target,
                )
            )

    def measure(self, target_qubits: QubitSetInput) -> Circuit:
        """
        Add a `measure` operator to `self` ensuring only the target qubits are measured.

        Args:
            target_qubits (QubitSetInput): target qubits to measure.

        Returns:
            Circuit: self

        Raises:
            IndexError: If `self` has no qubits.
            IndexError: If target qubits are not within the range of the current circuit.
            ValueError: If the current circuit contains any result types.
            ValueError: If the target qubit is already measured.

        Examples:
            >>> circ = Circuit.h(0).cnot(0, 1).measure([0])
            >>> circ.print(list(circ.instructions))
            [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)]),
            Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0),
                Qubit(1)]),
            Instruction('operator': Measure, 'target': QubitSet([Qubit(0)])]
        """
        if not isinstance(target_qubits, Iterable):
            target_qubits = QubitSet(target_qubits)

        # Check if result types are added on the circuit
        if self.result_types:
            raise ValueError("a circuit cannot contain both measure instructions and result types.")

        # Check if there are repeated qubits in the same measurement
        if len(target_qubits) != len(set(target_qubits)):
            intersection = [qubit for qubit, count in Counter(target_qubits).items() if count > 1]
            raise ValueError(
                f"cannot repeat qubit(s) {', '.join(map(str, intersection))} "
                "in the same measurement."
            )
        self._add_measure(target_qubits=target_qubits)

        return self

    def apply_gate_noise(
        self,
        noise: type[Noise] | Iterable[type[Noise]],
        target_gates: type[Gate] | Iterable[type[Gate]] | None = None,
        target_unitary: np.ndarray | None = None,
        target_qubits: QubitSetInput | None = None,
    ) -> Circuit:
        """Apply `noise` to the circuit according to `target_gates`, `target_unitary` and
        `target_qubits`.

        For any parameter that is None, that specification is ignored (e.g. if `target_gates`
        is None then the noise is applied after every gate in `target_qubits`).
        If `target_gates` and `target_qubits` are both None, then `noise` is
        applied to every qubit after every gate.

        Noise is either applied to `target_gates` or `target_unitary`, so they cannot be
        provided at the same time.

        When `noise.qubit_count` == 1, ie. `noise` is single-qubit, `noise` is added to all
        qubits in `target_gates` or `target_unitary` (or to all qubits in `target_qubits`
        if `target_gates` is None).

        When `noise.qubit_count` > 1 and `target_gates` is not None, the number of qubits of
        any gate in `target_gates` must be the same as `noise.qubit_count`.

        When `noise.qubit_count` > 1, `target_gates` and `target_unitary` is None, noise is
        only applied to gates with the same qubit_count in target_qubits.

        Args:
            noise (Union[type[Noise], Iterable[type[Noise]]]): Noise channel(s) to be applied
                to the circuit.
            target_gates (Optional[Union[type[Gate], Iterable[type[Gate]]]]): Gate class or
                List of Gate classes which `noise` is applied to. Default=None.
            target_unitary (Optional[ndarray]): matrix of the target unitary gates. Default=None.
            target_qubits (Optional[QubitSetInput]): Index or indices of qubit(s).
                Default=None.

        Returns:
            Circuit: self

        Raises:
            TypeError:
                If `noise` is not Noise type.
                If `target_gates` is not a Gate type, Iterable[Gate].
                If `target_unitary` is not a np.ndarray type.
                If `target_qubits` has non-integers or negative integers.
            IndexError:
                If applying noise to an empty circuit.
                If `target_qubits` is out of range of circuit.qubits.
            ValueError:
                If both `target_gates` and `target_unitary` are provided.
                If `target_unitary` is not a unitary.
                If `noise` is multi-qubit noise and `target_gates` contain gates
                with the number of qubits not the same as `noise.qubit_count`.

        Warning:
                If `noise` is multi-qubit noise while there is no gate with the same
                number of qubits in `target_qubits` or in the whole circuit when
                `target_qubits` is not given.
                If no `target_gates` or  `target_unitary` exist in `target_qubits` or
                in the whole circuit when they are not given.

        Examples:
        ::
            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
            >>> print(circ)
            T  : |0|1|2|

            q0 : -X-Z-C-
                      |
            q1 : -Y-X-X-

            T  : |0|1|2|

            >>> noise = Noise.Depolarizing(probability=0.1)
            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
            >>> print(circ.apply_gate_noise(noise, target_gates = Gate.X))
            T  : |     0     |     1     |2|

            q0 : -X-DEPO(0.1)-Z-----------C-
                                          |
            q1 : -Y-----------X-DEPO(0.1)-X-

            T  : |     0     |     1     |2|

            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
            >>> print(circ.apply_gate_noise(noise, target_qubits = 1))
            T  : |     0     |     1     |     2     |

            q0 : -X-----------Z-----------C-----------
                                          |
            q1 : -Y-DEPO(0.1)-X-DEPO(0.1)-X-DEPO(0.1)-

            T  : |     0     |     1     |     2     |

            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
            >>> print(circ.apply_gate_noise(noise,
            ...                             target_gates = [Gate.X,Gate.Y],
            ...                             target_qubits = [0,1])
            ... )
            T  : |     0     |     1     |2|

            q0 : -X-DEPO(0.1)-Z-----------C-
                                          |
            q1 : -Y-DEPO(0.1)-X-DEPO(0.1)-X-

            T  : |     0     |     1     |2|

        """
        # check whether gate noise is applied to an empty circuit
        if not self.qubits:
            raise IndexError("Gate noise cannot be applied to an empty circuit.")

        # check if target_gates and target_unitary are both given
        if (target_unitary is not None) and (target_gates is not None):
            raise ValueError("target_unitary and target_gates cannot be input at the same time.")

        # check target_qubits
        target_qubits = check_noise_target_qubits(self, target_qubits)
        if any(qubit not in self.qubits for qubit in target_qubits):
            raise IndexError("target_qubits must be within the range of the current circuit.")

        # Check if there is a measure instruction on the circuit
        self._check_if_qubit_measured(instruction=noise, target=target_qubits)

        # make noise a list
        noise = wrap_with_list(noise)

        # make target_gates a list
        if target_gates is not None:
            target_gates = wrap_with_list(target_gates)
            # remove duplicate items
            target_gates = list(dict.fromkeys(target_gates))

        for noise_channel in noise:
            if not isinstance(noise_channel, Noise):
                raise TypeError("Noise must be an instance of the Noise class")
                # check whether target_gates is valid
            if target_gates is not None:
                check_noise_target_gates(noise_channel, target_gates)
            if target_unitary is not None:
                check_noise_target_unitary(noise_channel, target_unitary)

        if target_unitary is not None:
            return apply_noise_to_gates(self, noise, target_unitary, target_qubits)
        return apply_noise_to_gates(self, noise, target_gates, target_qubits)

    def apply_initialization_noise(
        self,
        noise: type[Noise] | Iterable[type[Noise]],
        target_qubits: QubitSetInput | None = None,
    ) -> Circuit:
        """Apply `noise` at the beginning of the circuit for every qubit (default) or
        target_qubits`.

        Only when `target_qubits` is given can the noise be applied to an empty circuit.

        When `noise.qubit_count` > 1, the number of qubits in target_qubits must be equal
        to `noise.qubit_count`.

        Args:
            noise (Union[type[Noise], Iterable[type[Noise]]]): Noise channel(s) to be applied
                to the circuit.
            target_qubits (Optional[QubitSetInput]): Index or indices of qubit(s).
                Default=None.

        Returns:
            Circuit: self

        Raises:
            TypeError:
                If `noise` is not Noise type.
                If `target_qubits` has non-integers or negative integers.
            IndexError:
                If applying noise to an empty circuit when `target_qubits` is not given.
            ValueError:
                If `noise.qubit_count` > 1 and the number of qubits in target_qubits is
                not the same as `noise.qubit_count`.

        Examples:
            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0, 1)
            >>> print(circ)

            >>> noise = Noise.Depolarizing(probability=0.1)
            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0, 1)
            >>> print(circ.apply_initialization_noise(noise))

            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0, 1)
            >>> print(circ.apply_initialization_noise(noise, target_qubits=1))

            >>> circ = Circuit()
            >>> print(circ.apply_initialization_noise(noise, target_qubits=[0, 1]))

        """
        if (len(self.qubits) == 0) and (target_qubits is None):
            raise IndexError(
                "target_qubits must be provided in order to"
                " apply the initialization noise to an empty circuit."
            )

        target_qubits = check_noise_target_qubits(self, target_qubits)

        # make noise a list
        noise = wrap_with_list(noise)
        for noise_channel in noise:
            if not isinstance(noise_channel, Noise):
                raise TypeError("Noise must be an instance of the Noise class")
            if noise_channel.qubit_count > 1 and noise_channel.qubit_count != len(target_qubits):
                raise ValueError(
                    "target_qubits needs to be provided for this multi-qubit noise channel,"
                    " and the number of qubits in target_qubits must be the same as defined by"
                    " the multi-qubit noise channel."
                )

        return apply_noise_to_moments(self, noise, target_qubits, "initialization")

    def make_bound_circuit(self, param_values: dict[str, Number], strict: bool = False) -> Circuit:
        """Binds `FreeParameter`s based upon their name and values passed in. If parameters
        share the same name, all the parameters of that name will be set to the mapped value.

        Args:
            param_values (dict[str, Number]):  A mapping of FreeParameter names
                to a value to assign to them.
            strict (bool): If True, raises a ValueError if any of the FreeParameters
                in param_values do not appear in the circuit. False by default.

        Returns:
            Circuit: Returns a circuit with all present parameters fixed to their respective
            values.
        """
        if strict:
            self._validate_parameters(param_values)
        return self._use_parameter_value(param_values)

    def _validate_parameters(self, parameter_values: dict[str, Number]) -> None:
        """Checks that the parameters are in the `Circuit`.

        Args:
            parameter_values (dict[str, Number]):  A mapping of FreeParameter names
                to a value to assign to them.

        Raises:
            ValueError: If there are no parameters that match the key for the arg
                param_values.
        """
        parameter_strings = {str(parameter) for parameter in self.parameters}
        for param in parameter_values:
            if param not in parameter_strings:
                raise ValueError(f"No parameter in the circuit named: {param}")

    def _use_parameter_value(self, param_values: dict[str, Number]) -> Circuit:
        """Creates a `Circuit` that uses the parameter values passed in.

        Args:
            param_values (dict[str, Number]): A mapping of FreeParameter names
                to a value to assign to them.

        Returns:
            Circuit: A Circuit with specified parameters swapped for their
            values.

        """
        fixed_circ = Circuit()
        for val in param_values.values():
            self._validate_parameter_value(val)
        for instruction in self.instructions:
            if self._check_for_params(instruction):
                fixed_circ.add(
                    Instruction(
                        instruction.operator.bind_values(**param_values), target=instruction.target
                    )
                )
            else:
                fixed_circ.add(instruction)
        fixed_circ.add(self.result_types)
        return fixed_circ

    @staticmethod
    def _validate_parameter_value(val: Any) -> None:
        """Validates the value being used is a `Number`.

        Args:
            val (Any): The value be verified.

        Raises:
            ValueError: If the value is not a Number
        """
        if not isinstance(val, Number):
            raise TypeError(
                f"Parameters can only be assigned numeric values. Invalid inputs: {val}"
            )

    def apply_readout_noise(
        self,
        noise: type[Noise] | Iterable[type[Noise]],
        target_qubits: QubitSetInput | None = None,
    ) -> Circuit:
        """Apply `noise` right before measurement in every qubit (default) or target_qubits`.

        Only when `target_qubits` is given can the noise be applied to an empty circuit.

        When `noise.qubit_count` > 1, the number of qubits in target_qubits must be equal
        to `noise.qubit_count`.

        Args:
            noise (Union[type[Noise], Iterable[type[Noise]]]): Noise channel(s) to be applied
                to the circuit.
            target_qubits (Optional[QubitSetInput]): Index or indices of qubit(s).
                Default=None.

        Returns:
            Circuit: self

        Raises:
            TypeError:
                If `noise` is not Noise type.
                If `target_qubits` has non-integers.
            IndexError:
                If applying noise to an empty circuit.
            ValueError:
                If `target_qubits` has negative integers.
                If `noise.qubit_count` > 1 and the number of qubits in target_qubits is
                not the same as `noise.qubit_count`.

        Examples:
            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0, 1)
            >>> print(circ)

            >>> noise = Noise.Depolarizing(probability=0.1)
            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0, 1)
            >>> print(circ.apply_initialization_noise(noise))

            >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0, 1)
            >>> print(circ.apply_initialization_noise(noise, target_qubits=1))

            >>> circ = Circuit()
            >>> print(circ.apply_initialization_noise(noise, target_qubits=[0, 1]))

        """
        if (len(self.qubits) == 0) and (target_qubits is None):
            raise IndexError(
                "target_qubits must be provided in order to"
                " apply the readout noise to an empty circuit."
            )

        if target_qubits is None:
            target_qubits = self.qubits
        else:
            if not isinstance(target_qubits, list):
                target_qubits = [target_qubits]
            if not all(isinstance(q, int) for q in target_qubits):
                raise TypeError("target_qubits must be integer(s)")
            if any(q < 0 for q in target_qubits):
                raise ValueError("target_qubits must contain only non-negative integers.")
            target_qubits = QubitSet(target_qubits)

        # make noise a list
        noise = wrap_with_list(noise)
        for noise_channel in noise:
            if not isinstance(noise_channel, Noise):
                raise TypeError("Noise must be an instance of the Noise class")
            if noise_channel.qubit_count > 1 and noise_channel.qubit_count != len(target_qubits):
                raise ValueError(
                    "target_qubits needs to be provided for this multi-qubit noise channel,"
                    " and the number of qubits in target_qubits must be the same as defined by"
                    " the multi-qubit noise channel."
                )

        return apply_noise_to_moments(self, noise, target_qubits, "readout")

    def add(self, addable: AddableTypes, *args, **kwargs) -> Circuit:
        """Generic add method for adding item(s) to self. Any arguments that
        `add_circuit()` and / or `add_instruction()` and / or `add_result_type`
        supports are supported by this method. If adding a
        subroutine, check with that subroutines documentation to determine what
        input it allows.

        Args:
            addable (AddableTypes): The item(s) to add to self. Default = `None`.

        Returns:
            Circuit: self

        Raises:
            TypeError: If `addable` is an unsupported type

        See Also:
            `add_circuit()`

            `add_instruction()`

            `add_result_type()`

        Examples:
            >>> circ = Circuit().add([Instruction(Gate.H(), 4), Instruction(Gate.CNot(), [4, 5])])
            >>> circ = Circuit().add([ResultType.StateVector()])

            >>> circ = Circuit().h(4).cnot([4, 5])

            >>> @circuit.subroutine()
            >>> def bell_pair(target):
            ...     return Circuit().h(target[0]).cnot(target[0:2])
            >>> circ = Circuit().add(bell_pair, [4, 5])
        """

        def _flatten(addable: Iterable | AddableTypes) -> AddableTypes:
            if isinstance(addable, Iterable):
                for item in addable:
                    yield from _flatten(item)
            else:
                yield addable

        for item in _flatten(addable):
            if isinstance(item, Instruction):
                self.add_instruction(item, *args, **kwargs)
            elif isinstance(item, ResultType):
                self.add_result_type(item, *args, **kwargs)
            elif isinstance(item, Circuit):
                self.add_circuit(item, *args, **kwargs)
            elif callable(item):
                self.add(item(*args, **kwargs))
            else:
                raise TypeError(f"Cannot add a '{type(item)}' to a Circuit")

        return self

    def adjoint(self) -> Circuit:
        """Returns the adjoint of this circuit.

        This is the adjoint of every instruction of the circuit, in reverse order. Result types,
        and consequently basis rotations will stay in the same order at the end of the circuit.

        Returns:
            Circuit: The adjoint of the circuit.
        """
        circ = Circuit()
        for instr in reversed(self.instructions):
            circ.add(instr.adjoint())
        for result_type in self._result_types:
            circ.add_result_type(result_type)
        return circ

    def diagram(self, circuit_diagram_class: type = UnicodeCircuitDiagram) -> str:
        """Get a diagram for the current circuit.

        Args:
            circuit_diagram_class (type): A `CircuitDiagram` class that builds the
                diagram for this circuit. Default = `AsciiCircuitDiagram`.

        Returns:
            str: An ASCII string circuit diagram.
        """
        return circuit_diagram_class.build_diagram(self)

    def to_ir(
        self,
        ir_type: IRType = IRType.JAQCD,
        serialization_properties: SerializationProperties | None = None,
        gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence] | None = None,
    ) -> OpenQasmProgram | JaqcdProgram:
        """Converts the circuit into the canonical intermediate representation.
        If the circuit is sent over the wire, this method is called before it is sent.

        Args:
            ir_type (IRType): The IRType to use for converting the circuit object to its
                IR representation.
            serialization_properties (SerializationProperties | None): The serialization
                properties to use while serializing the object to the IR representation. The
                serialization properties supplied must correspond to the supplied `ir_type`.
                Defaults to None.
            gate_definitions (dict[tuple[Gate, QubitSet], PulseSequence] | None): The
                calibration data for the device. default: None.

        Returns:
            Union[OpenQasmProgram, JaqcdProgram]: A representation of the circuit in the
            `ir_type` format.

        Raises:
            ValueError: If the supplied `ir_type` is not supported, or if the supplied serialization
                properties don't correspond to the `ir_type`.
        """
        gate_definitions = gate_definitions or {}
        if ir_type == IRType.JAQCD:
            return self._to_jaqcd()
        if ir_type == IRType.OPENQASM:
            if serialization_properties and not isinstance(
                serialization_properties, OpenQASMSerializationProperties
            ):
                raise ValueError(
                    "serialization_properties must be of type OpenQASMSerializationProperties "
                    "for IRType.OPENQASM."
                )
            return self._to_openqasm(
                serialization_properties or OpenQASMSerializationProperties(),
                gate_definitions.copy(),
            )
        raise ValueError(f"Supplied ir_type {ir_type} is not supported.")

    @staticmethod
    def from_ir(source: str | OpenQasmProgram, inputs: dict[str, io_type] | None = None) -> Circuit:
        """Converts an OpenQASM program to a Braket Circuit object.

        Args:
            source (Union[str, OpenQasmProgram]): OpenQASM string.
            inputs (Optional[dict[str, io_type]]): Inputs to the circuit.

        Returns:
            Circuit: Braket Circuit implementing the OpenQASM program.
        """
        if isinstance(source, OpenQasmProgram):
            if inputs:
                inputs_copy = source.inputs.copy() if source.inputs is not None else {}
                inputs_copy.update(inputs)
                inputs = inputs_copy
            source = source.source
        from braket.circuits.braket_program_context import BraketProgramContext  # noqa: PLC0415

        return Interpreter(BraketProgramContext()).build_circuit(
            source=source,
            inputs=inputs,
            is_file=False,
        )

    def _to_jaqcd(self) -> JaqcdProgram:
        jaqcd_ir_type = IRType.JAQCD
        ir_instructions = [instr.to_ir(ir_type=jaqcd_ir_type) for instr in self.instructions]
        ir_results = [result_type.to_ir(ir_type=jaqcd_ir_type) for result_type in self.result_types]
        ir_basis_rotation_instructions = [
            instr.to_ir(ir_type=jaqcd_ir_type) for instr in self.basis_rotation_instructions
        ]
        return JaqcdProgram.construct(
            instructions=ir_instructions,
            results=ir_results,
            basis_rotation_instructions=ir_basis_rotation_instructions,
        )

    def _to_openqasm(
        self,
        serialization_properties: OpenQASMSerializationProperties,
        gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence],
    ) -> OpenQasmProgram:
        ir_instructions = self._create_openqasm_header(serialization_properties, gate_definitions)
        openqasm_ir_type = IRType.OPENQASM
        ir_instructions.extend([
            instruction.to_ir(
                ir_type=openqasm_ir_type, serialization_properties=serialization_properties
            )
            for instruction in self.instructions
        ])

        if self.result_types:
            ir_instructions.extend([
                result_type.to_ir(
                    ir_type=openqasm_ir_type, serialization_properties=serialization_properties
                )
                for result_type in self.result_types
            ])
        # measure all the qubits if a measure instruction is not provided
        elif self._measure_targets is None:
            qubits = (
                sorted(self.qubits)
                if serialization_properties.qubit_reference_type == QubitReferenceType.VIRTUAL
                else self.qubits
            )
            for idx, qubit in enumerate(qubits):
                qubit_target = serialization_properties.format_target(int(qubit))
                ir_instructions.append(f"b[{idx}] = measure {qubit_target};")

        return OpenQasmProgram.construct(source="\n".join(ir_instructions), inputs={})

    def _create_openqasm_header(
        self,
        serialization_properties: OpenQASMSerializationProperties,
        gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence],
    ) -> list[str]:
        ir_instructions = ["OPENQASM 3.0;"]
        frame_wf_declarations = self._generate_frame_wf_defcal_declarations(gate_definitions)
        ir_instructions.extend(f"input float {parameter};" for parameter in self.parameters)
        if not self.result_types:
            bit_count = (
                len(self._measure_targets)
                if self._measure_targets is not None
                else self.qubit_count
            )
            ir_instructions.append(f"bit[{bit_count}] b;")

        if serialization_properties.qubit_reference_type == QubitReferenceType.VIRTUAL:
            total_qubits = max(self.qubits).real + 1
            ir_instructions.append(f"qubit[{total_qubits}] q;")
        elif serialization_properties.qubit_reference_type != QubitReferenceType.PHYSICAL:
            raise ValueError(
                f"Invalid qubit_reference_type "
                f"{serialization_properties.qubit_reference_type} supplied."
            )

        if frame_wf_declarations:
            ir_instructions.append(frame_wf_declarations)
        return ir_instructions

    def _validate_gate_calibrations_uniqueness(
        self,
        gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence],
        frames: dict[str, Frame],
        waveforms: dict[str, Waveform],
    ) -> None:
        for calibration in gate_definitions.values():
            for frame in calibration._frames.values():
                _validate_uniqueness(frames, frame)
                frames[frame.id] = frame
            for waveform in calibration._waveforms.values():
                _validate_uniqueness(waveforms, waveform)
                waveforms[waveform.id] = waveform

    def _generate_frame_wf_defcal_declarations(
        self, gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence] | None
    ) -> str | None:
        """Generates the header where frames, waveforms and defcals are declared.

        It also adds any FreeParameter of the calibrations to the circuit parameter set.

        Args:
            gate_definitions (dict[tuple[Gate, QubitSet], PulseSequence] | None): The
                calibration data for the device.

        Returns:
            str | None: An OpenQASM string
        """

        program = oqpy.Program(None, simplify_constants=False)

        frames, waveforms = self._get_frames_waveforms_from_instrs(gate_definitions)

        self._validate_gate_calibrations_uniqueness(gate_definitions, frames, waveforms)

        # Declare the frames and waveforms across all pulse sequences
        declarable_frames = [f for f in frames.values() if not f.is_predefined]
        if declarable_frames or waveforms or gate_definitions:
            frame_wf_to_declare = [f._to_oqpy_expression() for f in declarable_frames]
            frame_wf_to_declare += [wf._to_oqpy_expression() for wf in waveforms.values()]
            program.declare(frame_wf_to_declare, encal=True)

            for key, calibration in gate_definitions.items():
                gate, qubits = key

                # Ignoring parametric gates
                # Corresponding defcals with fixed arguments have been added
                # in _get_frames_waveforms_from_instrs
                if isinstance(gate, Parameterizable) and any(
                    not isinstance(parameter, (float, int, complex))
                    for parameter in gate.parameters
                ):
                    continue

                gate_name = gate._qasm_name
                arguments = gate.parameters if isinstance(gate, Parameterizable) else []

                for param in calibration.parameters:
                    self._parameters.add(param)
                arguments = [
                    param._to_oqpy_expression() if isinstance(param, FreeParameter) else param
                    for param in arguments
                ]

                with oqpy.defcal(
                    program, [oqpy.PhysicalQubits[int(k)] for k in qubits], gate_name, arguments
                ):
                    program += calibration._program

            ast = program.to_ast(encal=False, include_externs=False)
            return ast_to_qasm(ast)

        return None

    def _get_frames_waveforms_from_instrs(
        self, gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence]
    ) -> tuple[dict[str, Frame], dict[str, Waveform]]:
        from braket.circuits.gates import PulseGate  # noqa: PLC0415

        frames = {}
        waveforms = {}
        for instruction in self.instructions:
            if isinstance(instruction.operator, PulseGate):
                for frame in instruction.operator.pulse_sequence._frames.values():
                    _validate_uniqueness(frames, frame)
                    frames[frame.id] = frame
                for waveform in instruction.operator.pulse_sequence._waveforms.values():
                    _validate_uniqueness(waveforms, waveform)
                    waveforms[waveform.id] = waveform
            # this will change with full parametric calibration support
            elif isinstance(instruction.operator, Parameterizable):
                fixed_argument_calibrations = self._add_fixed_argument_calibrations(
                    gate_definitions, instruction
                )
                gate_definitions |= fixed_argument_calibrations
        return frames, waveforms

    def _add_fixed_argument_calibrations(
        self,
        gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence],
        instruction: Instruction,
    ) -> dict[tuple[Gate, QubitSet], PulseSequence]:
        """Adds calibrations with arguments set to the instruction parameter values

        Given the collection of parameters in instruction.operator, this function looks for matching
        parametric calibrations that have free parameters. If such a calibration is found and the
        number N of its free parameters equals the number of instruction parameters, we can bind
        the arguments of the calibration and add it to the calibration dictionary.

        If N is smaller, it is probably impossible to assign the instruction parameter values to the
        corresponding calibration parameters so we raise an error.
        If N=0, we ignore it as it will not be removed by _generate_frame_wf_defcal_declarations.

        Args:
            gate_definitions (dict[tuple[Gate, QubitSet], PulseSequence]): a dictionary of
                calibrations
            instruction (Instruction): a Circuit instruction

        Returns:
            dict[tuple[Gate, QubitSet], PulseSequence]: additional calibrations

        Raises:
            NotImplementedError: in two cases: (i) if the instruction contains unbound parameters
                and the calibration dictionary contains a parametric calibration applicable to this
                instructions; (ii) if the calibration is defined with a partial number of unbound
                parameters.
        """
        additional_calibrations = {}
        for key, calibration in gate_definitions.items():
            gate = key[0]
            target = key[1]
            if target != instruction.target:
                continue
            if isinstance(gate, type(instruction.operator)) and len(
                instruction.operator.parameters
            ) == len(gate.parameters):
                free_parameter_number = sum(
                    isinstance(p, FreeParameterExpression) for p in gate.parameters
                )
                if free_parameter_number == 0:
                    continue
                if free_parameter_number < len(gate.parameters):
                    raise NotImplementedError(
                        "Calibrations with a partial number of fixed parameters are not supported."
                    )
                if any(
                    isinstance(p, FreeParameterExpression) for p in instruction.operator.parameters
                ):
                    raise NotImplementedError(
                        "Parametric calibrations cannot be attached with parametric circuits."
                    )
                bound_key = (
                    type(instruction.operator)(*instruction.operator.parameters),
                    instruction.target,
                )
                additional_calibrations[bound_key] = calibration(**{
                    p.name if isinstance(p, FreeParameterExpression) else p: v
                    for p, v in zip(gate.parameters, instruction.operator.parameters)
                })
        return additional_calibrations

    def to_unitary(self) -> np.ndarray:
        """Returns the unitary matrix representation of the entire circuit.

        Note:
            The performance of this method degrades with qubit count. It might be slow for
            `qubit count` > 10.

        Returns:
            np.ndarray: A numpy array with shape (2 :sup:`qubit_count`, 2 :sup:`qubit_count`)
            representing the circuit as a unitary. For an empty circuit, an empty numpy array
            is returned (`array([], dtype=complex)`)

        Raises:
            TypeError: If circuit is not composed only of `Gate` instances,
                i.e. a circuit with `Noise` operators will raise this error.

        Examples:
            >>> circ = Circuit().h(0).cnot(0, 1)
            >>> circ.to_unitary()
            array([[ 0.70710678+0.j,  0.        +0.j,  0.70710678+0.j,
                     0.        +0.j],
                   [ 0.        +0.j,  0.70710678+0.j,  0.        +0.j,
                     0.70710678+0.j],
                   [ 0.        +0.j,  0.70710678+0.j,  0.        +0.j,
                    -0.70710678+0.j],
                   [ 0.70710678+0.j,  0.        +0.j, -0.70710678+0.j,
                     0.        +0.j]])
        """
        if qubits := self.qubits:
            return calculate_unitary_big_endian(self.instructions, qubits)
        return np.zeros(0, dtype=complex)

    @property
    def qubits_frozen(self) -> bool:
        """bool: Whether the circuit's qubits are frozen, that is, cannot be remapped.

        This may happen because the circuit contains compiler directives preventing compilation
        of a part of the circuit, which consequently means that none of the other qubits can be
        rewired either for the program to still make sense.
        """
        return self._has_compiler_directives

    @property
    def observables_simultaneously_measurable(self) -> bool:
        """bool: Whether the circuit's observables are simultaneously measurable

        If this is False, then the circuit can only be run when shots = 0, as sampling (shots > 0)
        measures the circuit in the observables' shared eigenbasis.
        """
        return self._observables_simultaneously_measurable

    def _encounter_noncommuting_observable(self) -> None:
        self._observables_simultaneously_measurable = False
        # No longer simultaneously measurable, so no need to track
        self._qubit_observable_mapping.clear()
        self._qubit_observable_target_mapping.clear()

    def _copy(self) -> Circuit:
        copy = Circuit().add(self.instructions)
        copy.add(self.result_types)
        return copy

    def copy(self) -> Circuit:
        """Return a shallow copy of the circuit.

        Returns:
            Circuit: A shallow copy of the circuit.
        """
        return self._copy()

    def __iadd__(self, addable: AddableTypes) -> Circuit:
        return self.add(addable)

    def __add__(self, addable: AddableTypes) -> Circuit:
        new = self._copy()
        new.add(addable)
        return new

    def __repr__(self) -> str:
        if not self.result_types:
            return f"Circuit('instructions': {self.instructions})"
        return f"Circuit('instructions': {self.instructions}, 'result_types': {self.result_types})"

    def __str__(self):
        return self.diagram()

    def __eq__(self, other: Circuit):
        if isinstance(other, Circuit):
            return (
                self.instructions == other.instructions and self.result_types == other.result_types
            )
        return NotImplemented

    def __call__(self, arg: Any | None = None, **kwargs: Any) -> Circuit:
        """Implements the call function to easily make a bound Circuit.

        Args:
            arg (Any | None): A value to bind to all parameters. Defaults to None and
                can be overridden if the parameter is in kwargs.
            **kwargs (Any): The parameter and valued to be bound.

        Returns:
            Circuit: A circuit with the specified parameters bound.
        """
        param_values = {}
        if arg is not None:
            for param in self.parameters:
                param_values[str(param)] = arg
        for key, val in kwargs.items():
            param_values[str(key)] = val
        return self.make_bound_circuit(param_values)


def subroutine(register: bool = False) -> Callable:
    """Subroutine is a function that returns instructions, result types, or circuits.

    Args:
        register (bool): If `True`, adds this subroutine into the `Circuit` class.
            Default = `False`.

    Returns:
        Callable: The subroutine function.

    Examples:
        >>> @circuit.subroutine(register=True)
        >>> def bell_circuit():
        ...     return Circuit().h(0).cnot(0, 1)
        >>> circ = Circuit().bell_circuit()
        >>> for instr in circ.instructions:
        ...     print(instr)
        Instruction('operator': 'H', 'target': QubitSet(Qubit(0),))
        Instruction('operator': 'H', 'target': QubitSet(Qubit(1),))
    """

    def _subroutine_function_wrapper(func: Callable[..., SubroutineReturn]) -> SubroutineReturn:
        if register:
            Circuit.register_subroutine(func)
        return func

    return _subroutine_function_wrapper
