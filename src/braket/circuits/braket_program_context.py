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

from typing import List, Optional, Tuple, Type, Union

import numpy as np

from braket.circuits import Circuit, Instruction
from braket.circuits.gates import Unitary
from braket.circuits.noises import Kraus
from braket.circuits.translations import (
    BRAKET_GATES,
    braket_result_to_result_type,
    one_prob_noise_map,
)
from braket.default_simulator.openqasm._helpers.casting import LiteralType
from braket.default_simulator.openqasm.parser.openqasm_ast import ClassicalType, Identifier
from braket.default_simulator.openqasm.program_context import AbstractProgramContext
from braket.ir.jaqcd.program_v1 import Results
from braket.parametric import FreeParameter


class BraketProgramContext(AbstractProgramContext):
    def __init__(self, circuit: Optional[Circuit] = None):
        """
        Args:
            circuit (Optional[Circuit]): A partially-built circuit to continue building with this
                context. Default: None.
        """
        super().__init__()
        self._circuit = circuit or Circuit()

    @property
    def circuit(self) -> Circuit:
        """The circuit being built in this context."""
        return self._circuit

    def add_parameter(
        self, name: str, type: Union[ClassicalType, Type[LiteralType], Type[Identifier]]
    ) -> None:
        self.declare_variable(name, type, FreeParameter(name))

    def is_builtin_gate(self, name: str) -> bool:
        """Whether the gate is currently in scope as a built-in Braket gate.

        Args:
            name (str): name of the built-in Braket gate

        Returns:
            bool: return TRUE if it is a built-in gate else FALSE.
        """
        user_defined_gate = self.is_user_defined_gate(name)
        return name in BRAKET_GATES and not user_defined_gate

    def add_phase_instruction(self, target: Tuple[int], phase_value: int) -> None:
        raise NotImplementedError

    def add_gate_instruction(
        self, gate_name: str, target: Tuple[int], *params, ctrl_modifiers: List[int], power: float
    ) -> None:
        """Add Braket gate to the circuit.

        Args:
            gate_name (str): name of the built-in Braket gate.
            target (Tuple[int]): control_qubits + target_qubits.
            ctrl_modifiers (List[int]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control-qubits` in target. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state.
            power(float): Integer or fractional power to raise the gate to.
        """
        target_qubits = target[len(ctrl_modifiers) :]
        control_qubits = target[: len(ctrl_modifiers)]
        instruction = Instruction(
            BRAKET_GATES[gate_name](*params[0]),
            target=target_qubits,
            control=control_qubits,
            control_state=ctrl_modifiers,
            power=power,
        )
        self._circuit.add_instruction(instruction)

    def add_custom_unitary(
        self,
        unitary: np.ndarray,
        target: Tuple[int],
    ) -> None:
        """Add a custom Unitary instruction to the circuit

        Args:
            unitary (np.ndarray): unitary matrix
            target (Tuple[int]): control_qubits + target_qubits
        """
        instruction = Instruction(Unitary(unitary), target)
        self._circuit.add_instruction(instruction)

    def add_noise_instruction(
        self, noise_instruction: str, target: List[int], probabilities: List[float]
    ) -> None:
        """Method to add a noise instruction to the circuit

        Args:
            noise_instruction (str): The name of the noise operation
            target (List[int]): The target qubit or qubits to which the noise operation is applied.
            probabilities (List[float]): The probabilities associated with each possible outcome
                of the noise operation.
        """
        instruction = Instruction(
            one_prob_noise_map[noise_instruction](*probabilities), target=target
        )
        self._circuit.add_instruction(instruction)

    def add_kraus_instruction(self, matrices: List[np.ndarray], target: List[int]) -> None:
        """Method to add a Kraus instruction to the circuit

        Args:
            matrices (List[ndarray]): The matrices defining the Kraus operation
            target (List[int]): The target qubit or qubits to which the Kraus operation is applied.
        """
        instruction = Instruction(Kraus(matrices), target)
        self._circuit.add_instruction(instruction)

    def add_result(self, result: Results) -> None:
        """
        Abstract method to add result type to the circuit

        Args:
            result (Results): The result object representing the measurement results
        """
        self._circuit.add_result_type(braket_result_to_result_type(result))
