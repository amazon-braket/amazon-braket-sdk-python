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

from typing import List, Optional, Tuple

import numpy as np

from braket.circuits import Circuit, Instruction
from braket.circuits.gates import Unitary
from braket.circuits.noises import Kraus
from braket.circuits.translations import (
    BRAKET_GATES,
    braket_result_to_result_type,
    one_prob_noise_map,
)
from braket.default_simulator.openqasm.program_context import AbstractProgramContext
from braket.ir.jaqcd.program_v1 import Results


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
        return self._circuit

    def is_builtin_gate(self, name: str) -> bool:
        user_defined_gate = self.is_user_defined_gate(name)
        return name in BRAKET_GATES and not user_defined_gate

    def add_phase_instruction(self, target: Tuple[int], phase_value: int) -> None:
        raise NotImplementedError

    def add_gate_instruction(
        self, gate_name: str, target: Tuple[int], *params, ctrl_modifiers: List[int], power: float
    ) -> None:
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
        instruction = Instruction(Unitary(unitary), target)
        self._circuit.add_instruction(instruction)

    def add_noise_instruction(
        self, noise_instruction: str, target: List[int], probabilities: List[float]
    ) -> None:
        instruction = one_prob_noise_map[noise_instruction](target, *probabilities)
        self._circuit.add_instruction(instruction)

    def add_kraus_instruction(self, matrices, target):
        instruction = Instruction(Kraus(matrices), target)
        self._circuit.add_instruction(instruction)

    def add_result(self, result: Results) -> None:
        self._circuit.add_result_type(braket_result_to_result_type(result))
