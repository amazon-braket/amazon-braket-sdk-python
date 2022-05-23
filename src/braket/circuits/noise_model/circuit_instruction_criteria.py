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

from abc import abstractmethod
from typing import Optional, Set, Tuple, Union

from braket.circuits.instruction import Instruction
from braket.circuits.noise_model.criteria import Criteria
from braket.circuits.qubit_set import QubitSetInput


class CircuitInstructionCriteria(Criteria):
    """Criteria that implement these methods may be used to determine gate noise."""

    @abstractmethod
    def instruction_matches(self, instruction: Instruction) -> bool:
        """Returns True if an Instruction matches the criteria.

        Args:
            instruction (Instruction): An Instruction to match.

        Returns:
            bool: True if an Instruction matches the criteria.
        """
        raise NotImplementedError

    @staticmethod
    def _check_target_in_qubits(
        qubits: Optional[Set[Union[int, Tuple[int]]]], target: QubitSetInput
    ) -> bool:
        """
        Returns true if the given targets of an instruction match the given qubit input set.

        Args:
            qubits (Optional[Set[Union[int, Tuple[int]]]]): The qubits provided to the criteria.
            target (QubitSetInput): Targets of an instruction.

        Returns:
            bool: True if the provided target should be matched by the given qubits.
        """
        if qubits is None:
            return True
        target = [int(item) for item in target]
        if len(target) == 1:
            return target[0] in qubits
        return tuple(target) in qubits
