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

from typing import Callable, Dict, Iterable, List, Tuple, TypeVar, Union

from braket.circuits.ascii_circuit_diagram import AsciiCircuitDiagram
from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
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
        self._result_types: Dict[ResultType] = {}
        self._qubit_observable_mapping: Dict[Union[int, Circuit._ALL_QUBITS], Observable] = {}
        self._qubit_target_mapping: Dict[int, Tuple[int]] = {}
        self._qubit_observable_set = set()

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
        return list(self._result_types.keys())

    @property
    def basis_rotation_instructions(self) -> List[Instruction]:
        """List[Instruction]: Get a list of basis rotation instructions in the circuit.
        These basis rotation instructions are added if result types are requested for
        an observable other than Pauli-Z.
        """
        # Note that basis_rotation_instructions can change each time a new instruction
        # is added to the circuit because `self._moments.qubits` would change
        basis_rotation_instructions = []
        all_qubit_observable = self._qubit_observable_mapping.get(Circuit._ALL_QUBITS)
        if all_qubit_observable:
            for target in self.qubits:
                basis_rotation_instructions += Circuit._observable_to_instruction(
                    all_qubit_observable, target
                )
            return basis_rotation_instructions

        target_lists = sorted(list(set(self._qubit_target_mapping.values())))
        for target_list in target_lists:
            observable = self._qubit_observable_mapping[target_list[0]]
            basis_rotation_instructions += Circuit._observable_to_instruction(
                observable, target_list
            )
        return basis_rotation_instructions

    @staticmethod
    def _observable_to_instruction(observable: Observable, target_list: List[int]):
        return [Instruction(gate, target_list) for gate in observable.basis_rotation_gates]

    @property
    def moments(self) -> Moments:
        """Moments: Get the `moments` for this circuit. Note that this includes observables."""
        return self._moments

    @property
    def qubit_count(self) -> int:
        """Get the qubit count for this circuit. Note that this includes observables."""
        all_qubits = self._moments.qubits.union(self._qubit_observable_set)
        return len(all_qubits)

    @property
    def qubits(self) -> QubitSet:
        """QubitSet: Get a copy of the qubits for this circuit."""
        return QubitSet(self._moments.qubits.union(self._qubit_observable_set))

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
        the attribute `target`. The result_type will be appended to the end of the dict keys of
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
            self._add_to_qubit_observable_mapping(result_type_to_add)
            self._add_to_qubit_observable_set(result_type_to_add)
            # using dict as an ordered set, value is arbitrary
            self._result_types[result_type_to_add] = None
        return self

    def _add_to_qubit_observable_mapping(self, result_type: ResultType) -> None:
        if isinstance(result_type, ResultType.Probability):
            observable = Observable.Z()  # computational basis
        elif isinstance(result_type, ObservableResultType):
            observable = result_type.observable
        else:
            return

        targets = result_type.target or list(self._qubit_observable_set)
        all_qubits_observable = self._qubit_observable_mapping.get(Circuit._ALL_QUBITS)
        for i in range(len(targets)):
            target = targets[i]
            tensor_product_dict = (
                Circuit._tensor_product_index_dict(observable)
                if isinstance(observable, TensorProduct)
                else None
            )
            new_observable = tensor_product_dict[i][0] if tensor_product_dict else observable
            current_observable = all_qubits_observable or self._qubit_observable_mapping.get(target)

            add_observable = Circuit._validate_observable_to_add_for_qubit(
                current_observable, new_observable, target
            )

            if result_type.target:
                new_targets = (
                    tuple(
                        result_type.target[
                            tensor_product_dict[i][1][0] : tensor_product_dict[i][1][1]
                        ]
                    )
                    if tensor_product_dict
                    else tuple(result_type.target)
                )
                if add_observable:
                    self._qubit_target_mapping[target] = new_targets
                    self._qubit_observable_mapping[target] = new_observable
                elif new_observable.qubit_count > 1 and new_observable != Observable.I():
                    current_target = self._qubit_target_mapping.get(target)
                    if current_target and current_target != new_targets:
                        raise ValueError(
                            f"Target order {current_target} of existing result type with"
                            f" observable {current_observable} conflicts with order {targets}"
                            " of new result type"
                        )

        if not result_type.target:
            if all_qubits_observable and all_qubits_observable != observable:
                raise ValueError(
                    f"Existing result type for observable {all_qubits_observable} for all qubits"
                    f" conflicts with observable {observable} for new result type"
                )
            self._qubit_observable_mapping[Circuit._ALL_QUBITS] = observable

    @staticmethod
    def _validate_observable_to_add_for_qubit(current_observable, new_observable, target):
        identity = Observable.I()
        add_observable = False
        if not current_observable or (
            current_observable == identity and new_observable != identity
        ):
            add_observable = True
        elif (
            current_observable != identity
            and new_observable != identity
            and current_observable != new_observable
        ):
            raise ValueError(
                f"Observable {new_observable} specified for target {target} conflicts with"
                + f" existing observable {current_observable} on this target."
            )
        return add_observable

    @staticmethod
    def _tensor_product_index_dict(observable: TensorProduct) -> Dict[int, Observable]:
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
                obj_dict[i] = (factors[0], (total - factors[0].qubit_count, total))
            i += 1
        return obj_dict

    def _add_to_qubit_observable_set(self, result_type: ResultType) -> None:
        if isinstance(result_type, ObservableResultType) and result_type.target:
            self._qubit_observable_set.update(result_type.target)

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
                and self.result_types == other.result_types
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
