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

from typing import Any, Iterable, Optional, Set, Union

from braket.circuits.gates import Unitary
from braket.circuits.instruction import Instruction
from braket.circuits.noise_model.circuit_instruction_criteria import CircuitInstructionCriteria
from braket.circuits.noise_model.criteria import Criteria, CriteriaKey, CriteriaKeyResult
from braket.circuits.noise_model.criteria_input_parsing import parse_qubit_input
from braket.circuits.qubit_set import QubitSetInput


class UnitaryGateCriteria(CircuitInstructionCriteria):
    """This class models noise Criteria based on unitary gates represented as a matrix."""

    def __init__(self, unitary: Unitary, qubits: Optional[QubitSetInput] = None):
        """
        Creates unitary gate-based Criteria. See instruction_matches() for more details.

        Args:
            unitary (Unitary): A unitary gate matrix represented as a Braket Unitary.
            qubits (Optional[QubitSetInput]): A set of relevant qubits. If no qubits
                are provided, all (possible) qubits are considered to be relevant.
        Throws:
            ValueError: If unitary is not a Unitary type.
        """
        if not isinstance(unitary, Unitary):
            raise TypeError("unitary must be a Unitary type")
        self._unitary = unitary
        self._qubits = parse_qubit_input(qubits)

    def __str__(self):
        return f"{self.__class__.__name__}(unitary={self._unitary}, qubits={self._qubits})"

    def __repr__(self):
        return f"{self.__class__.__name__}(unitary={self._unitary}, qubits={self._qubits})"

    def applicable_key_types(self) -> Iterable[CriteriaKey]:
        """
        Returns:
            Iterable[CriteriaKey]: This Criteria operates on unitary gates and Qubits.
        """
        return [CriteriaKey.QUBIT, CriteriaKey.UNITARY_GATE]

    def get_keys(self, key_type: CriteriaKey) -> Union[CriteriaKeyResult, Set[Any]]:
        """Gets the keys for a given CriteriaKey.

        Args:
            key_type (CriteriaKey): The relevant Criteria Key.

        Returns:
            Union[CriteriaKeyResult, Set[Any]]: The return value is based on the key type:
            UNITARY_GATE will return a set containing the bytes of the unitary matrix representing
            the unitary gate.
            QUBIT will return a set of qubit targets that are relevant to this Criteria, or
            CriteriaKeyResult.ALL if the Criteria is relevant for all (possible) qubits.
            All other keys will return an empty list.
        """
        if key_type == CriteriaKey.UNITARY_GATE:
            return {self._unitary.to_matrix().tobytes()}
        if key_type == CriteriaKey.QUBIT:
            return CriteriaKeyResult.ALL if self._qubits is None else set(self._qubits)
        return set()

    def to_dict(self) -> dict:
        """
        Converts a dictionary representing an object of this class into an instance of this class.

        Returns:
            dict: A dictionary representing the serialized version of this Criteria.
        """
        qubits = list(self._qubits) if self._qubits is not None else None
        return {
            "__class__": self.__class__.__name__,
            "unitary": self._unitary,
            "qubits": qubits,
        }

    def instruction_matches(self, instruction: Instruction) -> bool:
        """Returns true if an Instruction matches the criteria.

        Args:
            instruction (Instruction): An Instruction to match.

        Returns:
            bool: Returns true if the operator is one of the Unitary gates provided in the
            constructor and the target is a qubit (or set of qubits) provided in the constructor.
            If qubits were not provided in the constructor, then this method will ignore
            the Instruction target.
        """
        if isinstance(instruction, Iterable):
            return False
        if instruction.operator != self._unitary:
            return False
        return CircuitInstructionCriteria._check_target_in_qubits(self._qubits, instruction.target)

    @classmethod
    def from_dict(cls, criteria: dict) -> Criteria:
        """Deserializes a dictionary into a Criteria object.

        Args:
            criteria (dict): A dictionary representation of a UnitaryGateCriteria.

        Returns:
            Criteria: A deserialized UnitaryGateCriteria represented by the passed in
            serialized data.
        """
        return UnitaryGateCriteria(criteria["unitary"], criteria["qubits"])


Criteria.register_criteria(UnitaryGateCriteria)
