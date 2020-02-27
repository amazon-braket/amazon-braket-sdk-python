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

from typing import Callable, Dict, Iterable, TypeVar

from braket.circuits.ascii_circuit_diagram import AsciiCircuitDiagram
from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.qubit import QubitInput
from braket.circuits.qubit_set import QubitSet, QubitSetInput
from braket.ir.jaqcd import Program

SubroutineReturn = TypeVar("SubroutineReturn", Iterable[Instruction], Instruction)
SubroutineCallable = TypeVar("SubroutineCallable", bound=Callable[..., SubroutineReturn])
AddableTypes = TypeVar("AddableTypes", SubroutineReturn, SubroutineCallable)

# TODO: Add parameterization


class Circuit:
    """
    A representation of a quantum circuit that contains the instructions to be performed on a
    quantum device. See :mod:`braket.circuits.gates` module for all of the supported instructions.
    """

    @classmethod
    def register_subroutine(cls, func: SubroutineCallable) -> None:
        """
        Register the subroutine `func` as an attribute of the `Circuit` class. The attribute name
        is the name of `func`.

        Args:
            func (Callable[..., Union[Instruction, Iterable[Instruction]]]): The function of the
                subroutine to add to the class.

        Examples:
            >>> def h_on_all(target):
            ...     circ = Circuit()
            ...     for qubit in target:
            ...         circ += Instruction(Gate.H, qubit)
            ...         return circ
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
            addable (Instruction, iterable of `Instruction`, or `SubroutineCallable`, optional): The
                instruction-like item(s) to add to self. Default = None.
            *args: Variable length argument list. Supports any arguments that `add()` offers.
            **kwargs: Arbitrary keyword arguments. Supports any keyword arguments that `add()`
                offers.

        Raises:
            TypeError: If `addable` is an unsupported type.

        Examples:
            >>> circ = Circuit([Instruction(Gate.H, 4), Instruction(Gate.CNot, [4, 5])])
            >>> circ = Circuit().h(0).cnot(0, 1)

            >>> @circuit.subroutine(register=True)
            >>> def bell_pair(target):
            ...     return Circ().h(target[0]).cnot(target[0:2])
            ...
            >>> circ = Circuit(bell_pair, [4,5])
            >>> circ = Circuit().bell_pair([4,5])
        """
        self._moments: Moments = Moments()

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

    def add_instruction(
        self,
        instruction: Instruction,
        target: QubitSetInput = None,
        target_mapping: Dict[QubitInput, QubitInput] = {},
    ) -> "Circuit":
        """
        Add an instruction to `self`, returns `self` for chaining ability.

        Args:
            instruction (Instruction): `Instruction` to add into `self`.
            target (int, Qubit, or iterable of int / Qubit, optional): Target qubits for the
                `instruction`. If a single qubit gate, an instruction is created for every index
                in `target`.
                Default = None.
            target_mapping (dictionary[int or Qubit, int or Qubit], optional): A dictionary of
                qubit mappings to apply to the `instruction.target`. Key is the qubit in
                `instruction.target` and the value is what the key will be changed to. Default = {}.

        Returns:
            Circuit: self

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.

        Examples:
            >>> instr = Instruction(Gate.CNot, [0, 1])
            >>> circ = Circuit().add_instruction(instr)
            >>> print(circ.instructions[0])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(0), Qubit(1)))

            >>> instr = Instruction(Gate.CNot, [0, 1])
            >>> circ = Circuit().add_instruction(instr, target_mapping={0: 10, 1: 11})
            >>> print(circ.instructions[0])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))

            >>> instr = Instruction(Gate.CNot, [0, 1])
            >>> circ = Circuit().add_instruction(instr, target=[10, 11])
            >>> print(circ.instructions[0])
            Instruction('operator': 'CNOT', 'target': QubitSet(Qubit(10), Qubit(11)))

            >>> instr = Instruction(Gate.H, 0)
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
        circuit: "Circuit",
        target: QubitSetInput = None,
        target_mapping: Dict[QubitInput, QubitInput] = {},
    ) -> "Circuit":
        """
        Add a `circuit` to self, returns self for chaining ability. This is a composite form of
        `add_instruction()` since it adds all of the instructions of `circuit` to this circuit.

        Args:
            circuit (Circuit): Circuit to add into self.
            target (int, Qubit, or iterable of int / Qubit, optional): Target qubits for the
                supplied circuit. This is a macro over `target_mapping`; `target` is converted to
                a `target_mapping` by zipping together a sorted `circuit.qubits` and `target`.
                Default = None.
            target_mapping (dictionary[int or Qubit, int or Qubit], optional): A dictionary of
                qubit mappings to apply to the qubits of `circuit.instructions`. Key is the qubit
                to map, and the Value is what to change it to. Default = {}.

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

        return self

    def add(self, addable: AddableTypes, *args, **kwargs) -> "Circuit":
        """
        Generic add method for adding instruction-like item(s) to self. Any arguments that
        `add_circuit()` and / or `add_instruction()` supports are supported by this method.
        If adding a subroutine, check with that subroutines documentation to determine what input it
        allows.

        Args:
            addable (Instruction, iterable of Instruction, or SubroutineCallable, optional): The
                instruction-like item(s) to add to self. Default = None.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Circuit: self

        Raises:
            TypeError: If `addable` is an unsupported type

        See Also:
            `add_circuit()`

            `add_instruction()`

        Examples:
            >>> circ = Circuit().add([Instruction(Gate.H, 4), Instruction(Gate.CNot, [4, 5])])

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
                diagram for this circuit. Default = AsciiCircuitDiagram.

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
        return Program(instructions=ir_instructions)

    def _copy(self) -> "Circuit":
        """
        Return a shallow copy of the circuit.

        Returns:
            Circuit: A shallow copy of the circuit.
        """
        return Circuit().add(self.instructions)

    def __iadd__(self, addable: AddableTypes) -> "Circuit":
        return self.add(addable)

    def __add__(self, addable: AddableTypes) -> "Circuit":
        new = self._copy()
        new.add(addable)
        return new

    def __repr__(self):
        return f"Circuit('instructions': {list(self.instructions)})"

    def __str__(self):
        return self.diagram(AsciiCircuitDiagram)

    def __eq__(self, other):
        if isinstance(other, Circuit):
            return list(self.instructions) == list(other.instructions)
        return NotImplemented


def subroutine(register=False):
    """
    Subroutine is a function that returns instructions or circuits.

    Args:
        register (bool, optional): If `True`, adds this subroutine into the `Circuit` class.
            Default = False.

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
