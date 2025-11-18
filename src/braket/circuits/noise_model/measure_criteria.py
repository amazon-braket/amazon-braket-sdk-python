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
from typing import Any

from braket.circuits.instruction import Instruction
from braket.circuits.measure import Measure
from braket.circuits.noise_model.circuit_instruction_criteria import CircuitInstructionCriteria
from braket.circuits.noise_model.criteria import Criteria, CriteriaKey, CriteriaKeyResult
from braket.circuits.noise_model.criteria_input_parsing import parse_qubit_input
from braket.registers.qubit_set import QubitSetInput


class MeasureCriteria(CircuitInstructionCriteria):
    """This class models noise Criteria based on Measure instructions."""

    def __init__(self, qubits: QubitSetInput | None = None):
        """Creates Measure-based Criteria.

        Args:
            qubits (QubitSetInput | None): A set of relevant qubits. If no qubits
                are provided, all (possible) qubits are considered to be relevant.
        """
        self._qubits = parse_qubit_input(qubits, 1)

    def __str__(self):
        return f"{self.__class__.__name__}({self._qubits})"

    def __repr__(self):
        return f"{self.__class__.__name__}(qubits={self._qubits})"

    def applicable_key_types(self) -> Iterable[CriteriaKey]:
        """Returns an Iterable of criteria keys.

        Returns:
            Iterable[CriteriaKey]: This Criteria operates on Qubits.
        """
        return [CriteriaKey.QUBIT]

    def get_keys(self, key_type: CriteriaKey) -> CriteriaKeyResult | set[Any]:
        """Gets the keys for a given CriteriaKey.

        Args:
            key_type (CriteriaKey): The relevant Criteria Key.

        Returns:
            CriteriaKeyResult | set[Any]: The return value is based on the key type:
            QUBIT will return a set of qubit targets that are relevant to this Criteria, or
            CriteriaKeyResult.ALL if the Criteria is relevant for all (possible) qubits.
            All other keys will return an empty set.
        """
        if key_type == CriteriaKey.QUBIT:
            return CriteriaKeyResult.ALL if self._qubits is None else set(self._qubits)
        return set()

    def to_dict(self) -> dict:
        """Converts a dictionary representing an object of this class into an instance of
        this class.

        Returns:
            dict: A dictionary representing the serialized version of this Criteria.
        """
        qubits = list(self._qubits) if self._qubits is not None else None
        return {
            "__class__": self.__class__.__name__,
            "qubits": qubits,
        }

    def instruction_matches(self, instruction: Instruction) -> bool:
        """Returns true if an Instruction matches the criteria.

        Args:
            instruction (Instruction): An Instruction to match.

        Returns:
            bool: Returns true if the instruction is a Measure instruction and the target
            is a qubit (or set of qubits) provided in the constructor.
            If qubits were not provided in the constructor, then this method will accept any
            Measure instruction target.
        """
        if not isinstance(instruction.operator, Measure):
            return False
        return CircuitInstructionCriteria._check_target_in_qubits(self._qubits, instruction.target)

    @classmethod
    def from_dict(cls, criteria: dict) -> Criteria:
        """Deserializes a dictionary into a Criteria object.

        Args:
            criteria (dict): A dictionary representation of a MeasureCriteria.

        Returns:
            Criteria: A deserialized MeasureCriteria represented by the passed in
            serialized data.
        """
        return MeasureCriteria(criteria["qubits"])


Criteria.register_criteria(MeasureCriteria)
