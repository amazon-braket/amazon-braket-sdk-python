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

from collections.abc import Iterable
from typing import Optional, Union

import numpy as np
from sympy import Expr, Number

from braket.circuits import Circuit, Instruction
from braket.circuits.gates import Unitary
from braket.circuits.measure import Measure
from braket.circuits.noises import Kraus
from braket.circuits.translations import (
    BRAKET_GATES,
    braket_result_to_result_type,
    one_prob_noise_map,
)
from braket.default_simulator.openqasm.program_context import AbstractProgramContext
from braket.ir.jaqcd.program_v1 import Results
from braket.parametric import FreeParameterExpression


class BraketProgramContext(AbstractProgramContext):
    def __init__(self, circuit: Optional[Circuit] = None):
        """Inits a `BraketProgramContext`.

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

    def is_builtin_gate(self, name: str) -> bool:
        """Whether the gate is currently in scope as a built-in Braket gate.

        Args:
            name (str): name of the built-in Braket gate

        Returns:
            bool: return TRUE if it is a built-in gate else FALSE.
        """
        user_defined_gate = self.is_user_defined_gate(name)
        return name in BRAKET_GATES and not user_defined_gate

    def add_phase_instruction(self, target: tuple[int], phase_value: float) -> None:
        """Add a global phase to the circuit.

        Args:
            target (tuple[int]): Unused
            phase_value (float): The phase value to be applied
        """
        instruction = Instruction(BRAKET_GATES["gphase"](phase_value))
        self._circuit.add_instruction(instruction)

    def add_gate_instruction(
        self, gate_name: str, target: tuple[int], *params, ctrl_modifiers: list[int], power: float
    ) -> None:
        """Add Braket gate to the circuit.

        Args:
            gate_name (str): name of the built-in Braket gate.
            target (tuple[int]): control_qubits + target_qubits.
            ctrl_modifiers (list[int]): Quantum state on which to control the
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
        target: tuple[int],
    ) -> None:
        """Add a custom Unitary instruction to the circuit

        Args:
            unitary (np.ndarray): unitary matrix
            target (tuple[int]): control_qubits + target_qubits
        """
        instruction = Instruction(Unitary(unitary), target)
        self._circuit.add_instruction(instruction)

    def add_noise_instruction(
        self, noise_instruction: str, target: list[int], probabilities: list[float]
    ) -> None:
        """Method to add a noise instruction to the circuit

        Args:
            noise_instruction (str): The name of the noise operation
            target (list[int]): The target qubit or qubits to which the noise operation is applied.
            probabilities (list[float]): The probabilities associated with each possible outcome
                of the noise operation.
        """
        instruction = Instruction(
            one_prob_noise_map[noise_instruction](*probabilities), target=target
        )
        self._circuit.add_instruction(instruction)

    def add_kraus_instruction(self, matrices: list[np.ndarray], target: list[int]) -> None:
        """Method to add a Kraus instruction to the circuit

        Args:
            matrices (list[ndarray]): The matrices defining the Kraus operation
            target (list[int]): The target qubit or qubits to which the Kraus operation is applied.
        """
        instruction = Instruction(Kraus(matrices), target)
        self._circuit.add_instruction(instruction)

    def add_result(self, result: Results) -> None:
        """Abstract method to add result type to the circuit

        Args:
            result (Results): The result object representing the measurement results
        """
        self._circuit.add_result_type(braket_result_to_result_type(result))

    def handle_parameter_value(
        self, value: Union[float, Expr]
    ) -> Union[float, FreeParameterExpression]:
        """Convert parameter value to required format.

        Args:
            value (Union[float, Expr]): Value of the parameter

        Returns:
            Union[float, FreeParameterExpression]: Return the value directly if numeric,
            otherwise wraps the symbolic expression as a `FreeParameterExpression`.
        """
        if isinstance(value, Expr):
            evaluated_value = value.evalf()
            if isinstance(evaluated_value, Number):
                return evaluated_value
            return FreeParameterExpression(evaluated_value)
        return value

    def add_measure(
        self, target: tuple[int], classical_targets: Optional[Iterable[int]] = None
    ) -> None:
        """Add a measure instruction to the circuit

        Args:
            target (tuple[int]): the target qubits to be measured.
            classical_targets (Optional[Iterable[int]]): the classical registers
                to use in the qubit measurement.
        """
        for iter, qubit in enumerate(target):
            index = classical_targets[iter] if classical_targets else iter
            instruction = Instruction(Measure(index=index), qubit)
            self._circuit.add_instruction(instruction)
