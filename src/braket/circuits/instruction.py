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

from typing import Any

from braket.circuits.basis_state import BasisState, BasisStateInput
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.operator import Operator
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.serialization import IRType, SerializationProperties
from braket.registers.qubit import QubitInput
from braket.registers.qubit_set import QubitSet, QubitSetInput

# InstructionOperator is a type alias, and it can be expanded to include other operators
InstructionOperator = Operator


class Instruction:
    """An instruction is a quantum directive that describes the quantum task to perform on a quantum
    device.
    """

    def __init__(
        self,
        operator: InstructionOperator,
        target: QubitSetInput | None = None,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        """InstructionOperator includes objects of type `Gate` and `Noise` only.

        Args:
            operator (InstructionOperator): Operator for the instruction.
            target (Optional[QubitSetInput]): Target qubits that the operator is applied to.
                Default is None.
            control (Optional[QubitSetInput]): Target qubits that the operator is controlled on.
                Default is None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Raises:
            ValueError: If `operator` is empty or any integer in `target` does not meet the `Qubit`
                or `QubitSet` class requirements. Also, if operator qubit count does not equal
                the size of the target qubit set.
            TypeError: If a `Qubit` class can't be constructed from `target` due to an incorrect
                `typing`.

        Examples:
            >>> Instruction(Gate.CNot(), [0, 1])
            Instruction('operator': CNOT, 'target': QubitSet(Qubit(0), Qubit(1)))
            >>> instr = Instruction(Gate.CNot()), QubitSet([0, 1])])
            Instruction('operator': CNOT, 'target': QubitSet(Qubit(0), Qubit(1)))
            >>> instr = Instruction(Gate.H(), 0)
            Instruction('operator': H, 'target': QubitSet(Qubit(0),))
            >>> instr = Instruction(Gate.Rx(0.12), 0)
            Instruction('operator': Rx, 'target': QubitSet(Qubit(0),))
            >>> instr = Instruction(Gate.Rx(0.12, control=1), 0)
            Instruction(
                'operator': Rx,
                'target': QubitSet(Qubit(0),),
                'control': QubitSet(Qubit(1),),
            )
        """
        if not operator:
            raise ValueError("Operator cannot be empty")
        target_set = QubitSet(target)
        control_set = QubitSet(control)
        if isinstance(operator, QuantumOperator) and len(target_set) != operator.qubit_count:
            raise ValueError(
                f"Operator qubit count {operator.qubit_count} must be equal to"
                f" size of target qubit set {target_set}"
            )
        self._operator = operator
        self._target = target_set
        self._control = control_set
        self._control_state = BasisState(
            (1,) * len(control_set) if control_state is None else control_state,
            len(control_set),
        )
        self._power = power

    @property
    def operator(self) -> InstructionOperator:
        """Operator: The operator for the instruction, for example, `Gate`."""
        return self._operator

    @property
    def target(self) -> QubitSet:
        """QubitSet: Target qubits that the operator is applied to."""
        return self._target

    @property
    def control(self) -> QubitSet:
        """QubitSet: Target qubits that the operator is controlled on."""
        return self._control

    @property
    def control_state(self) -> BasisState:
        """BasisState: Quantum state that the operator is controlled to."""
        return self._control_state

    @property
    def power(self) -> float:
        """float: Power that the operator is raised to."""
        return self._power

    def adjoint(self) -> list[Instruction]:
        """Returns a list of Instructions implementing adjoint of this instruction's own operator

        This operation only works on Gate operators and compiler directives.

        Returns:
            list[Instruction]: A list of new instructions that comprise the adjoint of this operator

        Raises:
            NotImplementedError: If `operator` is not of type `Gate` or `CompilerDirective`
        """
        operator = self._operator
        if isinstance(operator, Gate):
            return [
                Instruction(
                    gate,
                    self._target,
                    control=self._control,
                    control_state=self._control_state,
                    power=self._power,
                )
                for gate in operator.adjoint()
            ]
        if isinstance(operator, CompilerDirective):
            return [Instruction(operator.counterpart(), self._target)]
        raise NotImplementedError(f"Adjoint not supported for {operator}")

    def to_ir(
        self,
        ir_type: IRType = IRType.JAQCD,
        serialization_properties: SerializationProperties | None = None,
    ) -> Any:
        """Converts the operator into the canonical intermediate representation.
        If the operator is passed in a request, this method is called before it is passed.

        Args:
            ir_type(IRType) : The IRType to use for converting the instruction object to its
                IR representation.
            serialization_properties (SerializationProperties | None): The serialization properties
                to use while serializing the object to the IR representation. The serialization
                properties supplied must correspond to the supplied `ir_type`. Defaults to None.

        Returns:
            Any: IR object of the instruction.
        """
        kwargs = {}
        if self.control:
            kwargs["control"] = self.control
            kwargs["control_state"] = self.control_state
        if self.power != 1:
            kwargs["power"] = self.power
        return self._operator.to_ir(
            [int(qubit) for qubit in self._target],
            ir_type=ir_type,
            serialization_properties=serialization_properties,
            **kwargs,
        )

    @property
    def ascii_symbols(self) -> tuple[str, ...]:
        """tuple[str, ...]: Returns the ascii symbols for the instruction's operator."""
        return self._operator.ascii_symbols

    def copy(
        self,
        target_mapping: dict[QubitInput, QubitInput] | None = None,
        target: QubitSetInput | None = None,
        control_mapping: dict[QubitInput, QubitInput] | None = None,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        """Return a shallow copy of the instruction.

        Note:
            If `target_mapping` is specified, then `self.target` is mapped to the specified
            qubits. This is useful apply an instruction to a circuit and change the target qubits.
            Same relationship holds for `control_mapping`.

        Args:
            target_mapping (Optional[dict[QubitInput, QubitInput]]): A dictionary of
                qubit mappings to apply to the target. Key is the qubit in this `target` and the
                value is what the key is changed to. Default = `None`.
            target (Optional[QubitSetInput]): Target qubits for the new instruction.
                Default is None.
            control_mapping (Optional[dict[QubitInput, QubitInput]]): A dictionary of
                qubit mappings to apply to the control. Key is the qubit in this `control` and the
                value is what the key is changed to. Default = `None`.
            control (Optional[QubitSetInput]): Control qubits for the new instruction.
                Default is None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: A shallow copy of the instruction.

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.

        Examples:
            >>> instr = Instruction(Gate.H(), 0)
            >>> new_instr = instr.copy()
            >>> new_instr.target
            QubitSet(Qubit(0))
            >>> new_instr = instr.copy(target_mapping={0: 5})
            >>> new_instr.target
            QubitSet(Qubit(5))
            >>> new_instr = instr.copy(target=[5])
            >>> new_instr.target
            QubitSet(Qubit(5))
        """
        if target_mapping and target is not None:
            raise TypeError("Only 'target_mapping' or 'target' can be supplied, but not both.")
        if control_mapping and control is not None:
            raise TypeError("Only 'control_mapping' or 'control' can be supplied, but not both.")

        new_target = self._target.map(target_mapping or {}) if target is None else target
        new_control = self._control.map(control_mapping or {}) if control is None else control
        new_control_state = self._control_state if control_state is None else control_state

        return Instruction(
            self._operator,
            new_target,
            control=new_control,
            control_state=new_control_state,
            power=power,
        )

    def __repr__(self):
        return (
            f"Instruction('operator': {self._operator}, "
            f"'target': {self._target}, "
            f"'control': {self._control}, "
            f"'control_state': {self._control_state.as_tuple}, "
            f"'power': {self.power})"
        )

    def __eq__(self, other: Instruction):
        if isinstance(other, Instruction):
            return (
                self._operator,
                self._target,
                self._control,
                self._control_state,
                self._power,
            ) == (
                other._operator,
                other._target,
                other._control,
                other._control_state,
                other._power,
            )
        return NotImplemented

    def __pow__(self, power: float, modulo: float | None = None):
        new_power = self.power * power
        if modulo is not None:
            new_power %= modulo
        return self.copy(power=new_power)
