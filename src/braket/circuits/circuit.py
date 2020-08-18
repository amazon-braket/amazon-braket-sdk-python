# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from typing import Callable, Dict, Iterable, List, TypeVar, Union

from braket.circuits.ascii_circuit_diagram import AsciiCircuitDiagram
from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.noise import Noise
from braket.circuits.noise_helpers import _add_noise
from braket.circuits.observable import Observable
from braket.circuits.observables import TensorProduct
from braket.circuits.qubit import QubitInput
from braket.circuits.qubit_set import QubitSet, QubitSetInput
from braket.circuits.result_type import ObservableResultType, ResultType
from braket.ir.jaqcd import Program

SubroutineReturn = TypeVar(
    "SubroutineReturn", Iterable[Instruction], Instruction, ResultType, Iterable[ResultType]
)
SubroutineCallable = TypeVar("SubroutineCallable", bound=Callable[..., SubroutineReturn])
AddableTypes = TypeVar("AddableTypes", SubroutineReturn, SubroutineCallable)


class Circuit:
    """
    A representation of a quantum circuit that contains the instructions to be performed on a
    quantum device and the requested result types.

    See :mod:`braket.circuits.gates` module for all of the supported instructions.

    See :mod:`braket.circuits.result_types` module for all of the supported result types.

    `AddableTypes` are `Instruction`, iterable of `Instruction`, `ResultType`,
    iterable of `ResultType`, or `SubroutineCallable`
    """

    _ALL_QUBITS = "ALL"  # Flag to indicate all qubits in _qubit_observable_mapping

    @classmethod
    def register_subroutine(cls, func: SubroutineCallable) -> None:
        """
        Register the subroutine `func` as an attribute of the `Circuit` class. The attribute name
        is the name of `func`.

        Args:
            func (Callable[..., Union[Instruction, Iterable[Instruction], ResultType,
                Iterable[ResultType]]): The function of the subroutine to add to the class.

        Examples:
            >>> def h_on_all(target):
            ...     circ = Circuit()
            ...     for qubit in target:
            ...         circ += Instruction(Gate.H(), qubit)
            ...     return circ
            ...
            >>> Circuit.register_subroutine(h_on_all)
            >>> circ = Circuit().h_on_all(range(2))
            >>> for instr in circ.instructions:
            ...     print(instr)
            ...
            Instruction('operator': 'H', 'target': QubitSet(Qubit(0),))
            Instruction('operator': 'H', 'target': QubitSet(Qubit(1),))
        """

        def method_from_subroutine(self, *args, **kwargs) -> SubroutineReturn:
            return self.add(func, *args, **kwargs)

        function_name = func.__name__
        setattr(cls, function_name, method_from_subroutine)

        function_attr = getattr(cls, function_name)
        setattr(function_attr, "__doc__", func.__doc__)

    def __init__(self, addable: AddableTypes = None, *args, **kwargs):
        """
        Args:
            addable (AddableTypes): The item(s) to add to self.
                Default = None.
            *args: Variable length argument list. Supports any arguments that `add()` offers.
            **kwargs: Arbitrary keyword arguments. Supports any keyword arguments that `add()`
                offers.

        Raises:
            TypeError: If `addable` is an unsupported type.

        Examples:
            >>> circ = Circuit([Instruction(Gate.H(), 4), Instruction(Gate.CNot(), [4, 5])])
            >>> circ = Circuit().h(0).cnot(0, 1)
            >>> circ = Circuit().h(0).cnot(0, 1).probability([0, 1])

            >>> @circuit.subroutine(register=True)
            >>> def bell_pair(target):
            ...     return Circ().h(target[0]).cnot(target[0:2])
            ...
            >>> circ = Circuit(bell_pair, [4,5])
            >>> circ = Circuit().bell_pair([4,5])

        """
        self._moments: Moments = Moments()
        self._result_types: List[ResultType] = []
        self._qubit_observable_mapping: Dict[Union[int, Circuit._ALL_QUBITS], Observable] = {}
        self._qubit_target_mapping: Dict[int, List[int]] = {}

        if addable is not None:
            self.add(addable, *args, **kwargs)

    @property
    def depth(self) -> int:
        """int: Get the circuit depth."""
        return self._moments.depth

    @property
    def instructions(self) -> Iterable[Instruction]:
        """Iterable[Instruction]: Get an `iterable` of instructions in the circuit."""
        return self._moments.values()

    @property
    def result_types(self) -> List[ResultType]:
        """List[ResultType]: Get a list of requested result types in the circuit."""
        return self._result_types

    @property
    def basis_rotation_instructions(self) -> List[Instruction]:
        """List[Instruction]: Get a list of basis rotation instructions in the circuit.
        These basis rotation instructions are added if result types are requested for
        an observable other than Pauli-Z.
        """
        # Note that basis_rotation_instructions can change each time a new instruction
        # is added to the circuit because `self._moments.qubits` would change
        basis_rotation_instructions = []
        observable_return_types = (
            result_type
            for result_type in self._result_types
            if isinstance(result_type, ObservableResultType)
        )

        added_observables_targets = set()
        for return_type in observable_return_types:
            observable: Observable = return_type.observable
            targets: List[List[int]] = [list(return_type.target)] if return_type.target else [
                list([qubit]) for qubit in self._moments.qubits
            ]

            for target in targets:
                # only add gates for observables and targets that
                # have not been processed
                str_observables_target = f"{observable}; {target}"
                if str_observables_target in added_observables_targets:
                    continue
                added_observables_targets.add(str_observables_target)
                basis_rotation_instructions += Circuit._observable_to_instruction(
                    observable, target
                )
        return basis_rotation_instructions

    @staticmethod
    def _observable_to_instruction(observable: Observable, target_list: List[int]):
        if isinstance(observable, TensorProduct):
            instructions = []
            for factor in observable.factors:
                target = [target_list.pop(0) for _ in range(factor.qubit_count)]
                instructions += Circuit._observable_to_instruction(factor, target)
            return instructions
        else:
            return [Instruction(gate, target_list) for gate in observable.basis_rotation_gates]

    @property
    def moments(self) -> Moments:
        """Moments: Get the `moments` for this circuit."""
        return self._moments

    @property
    def qubit_count(self) -> int:
        """Get the qubit count for this circuit."""
        return self._moments.qubit_count

    @property
    def qubits(self) -> QubitSet:
        """QubitSet: Get a copy of the qubits for this circuit."""
        return QubitSet(self._moments.qubits)

    def add_result_type(
        self,
        result_type: ResultType,
        target: QubitSetInput = None,
        target_mapping: Dict[QubitInput, QubitInput] = {},
    ) -> Circuit:
        """
        Add a requested result type to `self`, returns `self` for chaining ability.

        Args:
            result_type (ResultType): `ResultType` to add into `self`.
            target (int, Qubit, or iterable of int / Qubit, optional): Target qubits for the
                `result_type`.
                Default = `None`.
            target_mapping (dictionary[int or Qubit, int or Qubit], optional): A dictionary of
                qubit mappings to apply to the `result_type.target`. Key is the qubit in
                `result_type.target` and the value is what the key will be changed to.
                Default = `{}`.


        Note: target and target_mapping will only be applied to those requested result types with
        the attribute `target`. The result_type will be appended to the end of the list of
        `circuit.result_types` only if it does not already exist in `circuit.result_types`

        Returns:
            Circuit: self

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.
            ValueError: If the observable specified for a qubit is different from what is
                specified by the result types already added to the circuit. Only one observable
                is allowed for a qubit.

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
            self._add_to_qubit_observable_mapping(result_type)
            self._result_types.append(result_type_to_add)
        return self

    def _add_to_qubit_observable_mapping(self, result_type: ResultType) -> None:
        if isinstance(result_type, ResultType.Probability):
            observable = Observable.Z()  # computational basis
        elif isinstance(result_type, ObservableResultType):
            observable = result_type.observable
        else:
            return

        targets = result_type.target or self._qubit_observable_mapping.keys()
        all_qubits_observable = self._qubit_observable_mapping.get(Circuit._ALL_QUBITS)

        for target in targets:
            current_observable = all_qubits_observable or self._qubit_observable_mapping.get(target)
            current_target = self._qubit_target_mapping.get(target)
            if current_observable and current_observable != observable:
                raise ValueError(
                    f"Existing result type for observable {current_observable} for target {target}"
                    f" conflicts with observable {observable} for new result type"
                )

            if result_type.target:
                # The only way this can happen is if the observables (acting on multiple target
                # qubits) and target qubits are the same, but the new target is the wrong order;
                if current_target and current_target != targets:
                    raise ValueError(
                        f"Target order {current_target} of existing result type with observable"
                        f" {current_observable} conflicts with order {targets} of new result type"
                    )
                self._qubit_observable_mapping[target] = observable
                self._qubit_target_mapping[target] = targets

        if not result_type.target:
            self._qubit_observable_mapping[Circuit._ALL_QUBITS] = observable

    def add_instruction(
        self,
        instruction: Instruction,
        target: QubitSetInput = None,
        target_mapping: Dict[QubitInput, QubitInput] = {},
    ) -> Circuit:
        """
        Add an instruction to `self`, returns `self` for chaining ability.

        Args:
            instruction (Instruction): `Instruction` to add into `self`.
            target (int, Qubit, or iterable of int / Qubit, optional): Target qubits for the
                `instruction`. If a single qubit gate, an instruction is created for every index
                in `target`.
                Default = `None`.
            target_mapping (dictionary[int or Qubit, int or Qubit], optional): A dictionary of
                qubit mappings to apply to the `instruction.target`. Key is the qubit in
                `instruction.target` and the value is what the key will be changed to.
                Default = `{}`.

        Returns:
            Circuit: self

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.

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

        self._moments.add(instructions_to_add)

        return self

    def add_circuit(
        self,
        circuit: Circuit,
        target: QubitSetInput = None,
        target_mapping: Dict[QubitInput, QubitInput] = {},
    ) -> Circuit:
        """
        Add a `circuit` to self, returns self for chaining ability.

        Args:
            circuit (Circuit): Circuit to add into self.
            target (int, Qubit, or iterable of int / Qubit, optional): Target qubits for the
                supplied circuit. This is a macro over `target_mapping`; `target` is converted to
                a `target_mapping` by zipping together a sorted `circuit.qubits` and `target`.
                Default = `None`.
            target_mapping (dictionary[int or Qubit, int or Qubit], optional): A dictionary of
                qubit mappings to apply to the qubits of `circuit.instructions`. Key is the qubit
                to map, and the value is what to change it to. Default = `{}`.

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
            >>> widget = Circuit().h(0).cnot([0, 1])
            >>> circ = Circuit().add_circuit(widget)
            >>> print(circ.instructions[0])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(0),))
            >>> print(circ.instructions[1])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(0), Qubit(1)))

            >>> widget = Circuit().h(0).cnot([0, 1])
            >>> circ = Circuit().add_circuit(widget, target_mapping={0: 10, 1: 11})
            >>> print(circ.instructions[0])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(10),))
            >>> print(circ.instructions[1])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))

            >>> widget = Circuit().h(0).cnot([0, 1])
            >>> circ = Circuit().add_circuit(widget, target=[10, 11])
            >>> print(circ.instructions[0])
            Instruction('operator': 'H', 'target': QubitSet(Qubit(10),))
            >>> print(circ.instructions[1])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))
        """
        if target_mapping and target is not None:
            raise TypeError("Only one of 'target_mapping' or 'target' can be supplied.")
        elif target is not None:
            keys = sorted(circuit.qubits)
            values = target
            target_mapping = dict(zip(keys, values))

        for instruction in circuit.instructions:
            self.add_instruction(instruction, target_mapping=target_mapping)

        for result_type in circuit.result_types:
            self.add_result_type(result_type, target_mapping=target_mapping)

        return self

    def add_noise(
        self,
        noise: Noise,
        target_gates: Union[str, List[str]] = None,
        target_qubits: QubitSetInput = None,
        target_times: Union[int, List[int]] = None,
        insert_strategy: str = "inclusive",
    ) -> Circuit:
        """
        Add the provided `noise` to gates, qubits and time specified by `target_gates`,
         `target_qubits` and `target_times`. When `target_gates`=None, `noise` is added
        to the specified qubits and time. When `target_qubits`=None, `noise` is added to
        the specified gates and time at all qubits. When `target_times`=None, `noise` is
        added to the specified gates and qubits at all time. If all `target_gates`,
        `target_qubits` and `target_times` are None, `noise` is added to every qubit at
        every time in a circuit.

        When `target_gates` is not None and `noise.qubit_count`>1, `noise.qubit_count`
        must be the same as `qubit_count` of gates specified by `target_gates`. When
        `noise.qubit_count`==1, ie. `noise` is a single-qubit noise, `noise` is added
        to all qubits in `target_qubits` that interact with the target gates.

        Args:
            noise (Noise): Noise to be added to the circuit. When `noise.qubit_count`>1,
                `noise.qubit_count` must be the same as `qubit_count` of gates specified by
                `target_gates`.
            targer_gates (Union[str, List[str]): Name or List of name of gates which
                `noise` is added to. If None, `noise` is added only according to
                `target_qubits` and `target_times`. None should be used when users want
                to add `noise` to a ciruit moment that has no gate.
            target_qubits (QubitSetInput): Index or indices of qubit(s). When `target_gates`
                is not None, the usage of `target_qubits` is determined by `insert_strategy`.
                Default=None.
            target_times (Union[int, List[int]]): Index of indices of time which `noise`
                is added to. Default=None.
            insert_strategy (str): Rule of how `target_qubit` is used. `insert_strategy`
                is usded only when `target_gates` is not None. Default="inclusive".
                Options:
                    "strict": Insert noise to a gate when `gate.target` exactly matches
                        `target_qubits`. Sensitive to the order of qubits.
                    "inclusive": Insert noise to a gate when `gate.target` is a subset
                        of `target_qubits`.

        Returns:
            Circuit: self

        Raises:
                TypeError: If `noise` is not Noise type, `target_gates` is not str,
                List[str] or None, `target_times` is not int or List[int].

        Example:
        >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
        >>> print(circ)
            T  : |0|1|2|
            q0 : -X-Z-C-
                      |
            q1 : -Y-X-X-
            T  : |0|1|2|
        >>> noise = Noise.Bit_Flip(prob=0.1)
        >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
        >>> print(circ.add_noise(noise, target_gates = 'X'))
            T  : |    0    |    1    |2|
            q0 : -X-NB(0.1)-Z---------C-
                                      |
            q1 : -Y---------X-NB(0.1)-X-
            T  : |    0    |    1    |2|
        >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
        >>> print(circ.add_noise(noise, target_qubits = 1))
            T  : |    0    |    1    |    2    |
            q0 : -X---------Z---------C---------
                                      |
            q1 : -Y-NB(0.1)-X-NB(0.1)-X-NB(0.1)-
            T  : |    0    |    1    |    2    |
        >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
        >>> print(circ.add_noise(noise, target_gates = 'X', target_qubits = 1))
            T  : |0|    1    |2|
            q0 : -X-Z---------C-
                              |
            q1 : -Y-X-NB(0.1)-X-
            T  : |0|    1    |2|
        >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
        >>> print(circ.add_noise(noise, target_gates = ['X','Y'], target_qubits = [0,1]))
            T  : |    0    |    1    |2|
            q0 : -X-NB(0.1)-Z---------C-
                                      |
            q1 : -Y-NB(0.1)-X-NB(0.1)-X-
            T  : |    0    |    1    |2|
        >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
        >>> print(circ.add_noise(noise, target_times=[0,2]))
            T  : |    0    |1|    2    |
            q0 : -X-NB(0.1)-Z-C-NB(0.1)-
                              |
            q1 : -Y-NB(0.1)-X-X-NB(0.1)-
            T  : |    0    |1|    2    |
        >>> circ = Circuit().x(0).y(1).z(0).x(1).cnot(0,1)
        >>> print(circ.add_noise(noise,
        ...                      target_gates = ['X','Y'],
        ...                      target_qubits = [0,1],
        ...                      target_times=1)
        ... )
            T  : |0|    1    |2|
            q0 : -X-Z---------C-
                              |
            q1 : -Y-X-NB(0.1)-X-
            T  : |0|    1    |2|

        """

        if isinstance(target_gates, str):
            target_gates = [target_gates]
        if target_qubits is None:
            target_qubits = QubitSet(range(self.qubit_count))
        else:
            target_qubits = QubitSet(target_qubits)
        if target_times is None:
            target_times = range(self.depth)
        if isinstance(target_times, int):
            target_times = [target_times]

        if not isinstance(noise, Noise):
            raise TypeError("noise must be a Noise class")
        if target_gates and not all(isinstance(s, str) for s in target_gates):
            raise TypeError(f"all elements in {target_gates} must be str")
        if not all(isinstance(time, int) for time in target_times):
            raise TypeError("target_times must be int or List[int]")

        return _add_noise(self, noise, target_gates, target_qubits, target_times, insert_strategy)

    def add(self, addable: AddableTypes, *args, **kwargs) -> Circuit:
        """
        Generic add method for adding item(s) to self. Any arguments that
        `add_circuit()` and / or `add_instruction()` and / or `add_result_type`
        supports are supported by this method. If adding a subroutine,
        check with that subroutines documentation to determine what input it
        allows.

        Args:
            addable (AddableTypes): The item(s) to add to self. Default = `None`.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

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
            ...     return Circuit().h(target[0]).cnot(target[0: 2])
            ...
            >>> circ = Circuit().add(bell_pair, [4,5])
        """

        def _flatten(addable):
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

    def diagram(self, circuit_diagram_class=AsciiCircuitDiagram) -> str:
        """
        Get a diagram for the current circuit.

        Args:
            circuit_diagram_class (Class, optional): A `CircuitDiagram` class that builds the
                diagram for this circuit. Default = `AsciiCircuitDiagram`.

        Returns:
            str: An ASCII string circuit diagram.
        """
        return circuit_diagram_class.build_diagram(self)

    def to_ir(self) -> Program:
        """
        Converts the circuit into the canonical intermediate representation.
        If the circuit is sent over the wire, this method is called before it is sent.

        Returns:
            (Program): An AWS quantum circuit description program in JSON format.
        """
        ir_instructions = [instr.to_ir() for instr in self.instructions]
        ir_results = [result_type.to_ir() for result_type in self.result_types]
        ir_basis_rotation_instructions = [
            instr.to_ir() for instr in self.basis_rotation_instructions
        ]
        return Program.construct(
            instructions=ir_instructions,
            results=ir_results,
            basis_rotation_instructions=ir_basis_rotation_instructions,
        )

    def _copy(self) -> Circuit:
        copy = Circuit().add(self.instructions)
        copy.add(self.result_types)
        return copy

    def copy(self) -> Circuit:
        """
        Return a shallow copy of the circuit.

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
            return f"Circuit('instructions': {list(self.instructions)})"
        else:
            return (
                f"Circuit('instructions': {list(self.instructions)}"
                + f"result_types': {self.result_types})"
            )

    def __str__(self):
        return self.diagram(AsciiCircuitDiagram)

    def __eq__(self, other):
        if isinstance(other, Circuit):
            return (
                list(self.instructions) == list(other.instructions)
                and self.result_types == self.result_types
            )
        return NotImplemented


def subroutine(register=False):
    """
    Subroutine is a function that returns instructions, result types, or circuits.

    Args:
        register (bool, optional): If `True`, adds this subroutine into the `Circuit` class.
            Default = `False`.

    Examples:
        >>> @circuit.subroutine(register=True)
        >>> def bell_circuit():
        ...     return Circuit().h(0).cnot(0, 1)
        ...
        >>> circ = Circuit().bell_circuit()
        >>> for instr in circ.instructions:
        ...     print(instr)
        ...
        Instruction('operator': 'H', 'target': QubitSet(Qubit(0),))
        Instruction('operator': 'H', 'target': QubitSet(Qubit(1),))
    """

    def subroutine_function_wrapper(func: Callable[..., SubroutineReturn]) -> SubroutineReturn:
        if register:
            Circuit.register_subroutine(func)
        return func

    return subroutine_function_wrapper
