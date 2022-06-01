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

from braket.circuits.noise_model.criteria import Criteria, CriteriaKey, CriteriaKeyResult
from braket.circuits.noise_model.criteria_input_parsing import parse_qubit_input
from braket.circuits.noise_model.initialization_criteria import InitializationCriteria
from braket.circuits.qubit_set import QubitSet, QubitSetInput


class QubitInitializationCriteria(InitializationCriteria):
    """This class models initialization noise Criteria based on qubits."""

    def __init__(self, qubits: Optional[QubitSetInput] = None):
        """
        Creates initialization noise Qubit-based Criteria.

        Args:
            qubits (Optional[QubitSetInput]): A set of relevant qubits. If no qubits
                are provided, all (possible) qubits are considered to be relevant.
        """
        self._qubits = parse_qubit_input(qubits)

    def __str__(self):
        return f"{self.__class__.__name__}({self._qubits})"

    def __repr__(self):
        return f"{self.__class__.__name__}(qubits={self._qubits})"

    def applicable_key_types(self) -> Iterable[CriteriaKey]:
        """
        Returns:
            Iterable[CriteriaKey]: This Criteria operates on Qubits, but is valid for all Gates.
        """
        return [CriteriaKey.QUBIT]

    def get_keys(self, key_type: CriteriaKey) -> Union[CriteriaKeyResult, Set[Any]]:
        """Gets the keys for a given CriteriaKey.

        Args:
            key_type (CriteriaKey): The relevant Criteria Key.

        Returns:
            Union[CriteriaKeyResult, Set[Any]]: The return value is based on the key type:
            QUBIT will return a set of qubit targets that are relevant to this Critera, or
            CriteriaKeyResult.ALL if the Criteria is relevant for all (possible) qubits.
            All other keys will return an empty set.
        """
        if key_type == CriteriaKey.QUBIT:
            if self._qubits is None:
                return CriteriaKeyResult.ALL
            return set(self._qubits)
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
            "qubits": qubits,
        }

    def qubit_intersection(self, qubits: QubitSetInput) -> QubitSetInput:
        """
        Returns subset of passed qubits that match the criteria.

        Args:
            qubits (QubitSetInput): A qubit or set of qubits that may match the criteria.

        Returns:
            QubitSetInput: The subset of passed qubits that match the criteria.
        """
        target_qubit = QubitSet(qubits)
        if self._qubits is None:
            return target_qubit
        return self._qubits.intersection(target_qubit)

    @classmethod
    def from_dict(cls, criteria: dict) -> Criteria:
        """
        Deserializes a dictionary into a Criteria object.

        Args:
            criteria (dict): A dictionary representation of a QubitCriteria.

        Returns:
            Criteria: A deserialized QubitCriteria represented by the passed in
            serialized data.
        """
        return QubitInitializationCriteria(criteria["qubits"])


Criteria.register_criteria(QubitInitializationCriteria)
