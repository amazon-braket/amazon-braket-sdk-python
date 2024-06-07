from braket.default_simulator.openqasm.program_context import AbstractProgramContext
from pytket.circuit import (
    Circuit, 
    OpType, 
    Unitary1qBox,
    Unitary2qBox, 
    Unitary3qBox
)
from pytket.unit_id import Qubit, Bit
from typing import Optional, Union, Any
from sympy import Expr
from braket.emulators.pytket_translator.translations import (
    QASM_TO_PYTKET, 
    COMPOSED_GATES
)
import numpy as np
from sympy import Symbol, pi


class PytketProgramContext(AbstractProgramContext):
    def __init__(self, circuit: Optional[Circuit] = None):
        """Inits a `PytketProgramContext`.

        Args:
            circuit (Optional[Circuit]): A partially-built Pytket circuit to continue building with this
                context. Default: None.
        """
        super().__init__()
        self._circuit = circuit or Circuit()
        self._qubits_set = set()

    @property
    def circuit(self) -> Circuit:
            """Returns the Pytket circuit being built in this context."""
            return self._circuit

    def is_builtin_gate(self, name: str) -> bool: 
        user_defined_gate = self.is_user_defined_gate(name)
        result = (name in QASM_TO_PYTKET or COMPOSED_GATES) and not user_defined_gate
        return result

    def add_gate_instruction(
        self, gate_name: str, target: tuple[int, ...], params, ctrl_modifiers: list[int], power: int
    ): 
        self._check_and_update_qubits(target)
        # Convert from Braket's radians to TKET's half-turns
        params = [param / pi for param in params]
        if gate_name in QASM_TO_PYTKET:
            op = QASM_TO_PYTKET[gate_name]
            if len(params) > 0:
                self._circuit.add_gate(op, *params, target)
            else:
                self._circuit.add_gate(op, target)
        elif gate_name in COMPOSED_GATES:
            COMPOSED_GATES[gate_name](self._circuit, *params, target)
        else:
            raise ValueError(f"Gate {gate_name} is not supported in pytket translations.")
            
        
    def _check_and_update_qubits(self, target: tuple[int, ...]):
        for qubit in target: 
            if qubit not in self._qubits_set:
                new_qubit = Qubit(index=qubit)
                self._qubits_set.add(qubit)
                self._circuit.add_qubit(new_qubit)

    def add_phase_instruction(self, target, phase_value):
        self.add_gate_instruction("gphase", target, phase_value)

    def add_measure(self, target: tuple[int]):
        if len(target) == 0: 
            return
        self._check_and_update_qubits(target)
        for index, qubit in enumerate(target):
            self._circuit.add_bit(Bit(qubit))
            self._circuit.Measure(qubit, qubit)

    def add_custom_unitary(
        self,
        unitary: np.ndarray,
        target: tuple[int, ...],
    ): 
        num_targets = len(target)
        if not (1 <= num_targets <= 3):
            raise ValueError("At most 3 qubit gates are supported for custom unitary operations.")

        operator_qubit_count = int(np.log2(unitary.shape[0]))
        if operator_qubit_count != num_targets:
            raise ValueError(
                f"Operator qubit count {operator_qubit_count} must be equal to size of target qubit set {target}"
            )

        self._check_and_update_qubits(target)
        if num_targets == 1: 
            unitary_box = Unitary1qBox(unitary)
            self._circuit.add_unitary1qbox(unitary_box, *target)
        elif num_targets == 2:
            unitary_box = Unitary2qBox(unitary)
            self._circuit.add_unitary2qbox(unitary_box, *target)
        elif num_targets == 3:
            unitary_box = Unitary3qBox(unitary)
            self._circuit.add_unitary3qbox(unitary_box, *target)


    def handle_parameter_value(self, value: Union[float, Expr]) -> Any:
        if isinstance(value, Expr):
            return value.evalf()
        return value