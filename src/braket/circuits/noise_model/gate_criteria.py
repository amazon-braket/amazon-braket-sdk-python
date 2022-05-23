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

from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.noise_model.circuit_instruction_criteria import CircuitInstructionCriteria
from braket.circuits.noise_model.criteria import Criteria, CriteriaKey, CriteriaKeyResult
from braket.circuits.noise_model.criteria_input_parsing import (
    parse_operator_input,
    parse_qubit_input,
)
from braket.circuits.qubit_set import QubitSetInput


class GateCriteria(CircuitInstructionCriteria):
    """This class models noise Criteria based on named Braket SDK Gates."""

    def __init__(
        self,
        gates: Optional[Union[Gate, Iterable[Gate]]] = None,
        qubits: Optional[QubitSetInput] = None,
    ):
        """
        Creates Gate-based Criteria. See instruction_matches() for more details.

        Args:
            gates (Optional[Union[Gate, Iterable[Gate]]]): A set of relevant Gates. All the Gates
                must have the same fixed_qubit_count(). Optional. If gates are not provided
                this matcher will match on all gates.
            qubits (Optional[QubitSetInput]): A set of relevant qubits. If no qubits
                are provided, all (possible) qubits are considered to be relevant.

        Raises:
            ValueError: If the gates don't all operate on the same number of qubits, or if
            qubits are not valid targets for the provided gates.
        """
        self._gates = parse_operator_input(gates)
        expected_qubit_count = next(iter(self._gates)).fixed_qubit_count() if self._gates else 0
        self._qubits = parse_qubit_input(qubits, expected_qubit_count)

    def __str__(self):
        gate_names = {gate.__name__ for gate in self._gates} if self._gates is not None else None
        return f"{self.__class__.__name__}({gate_names}, {self._qubits})"

    def __repr__(self):
        gate_names = {gate.__name__ for gate in self._gates} if self._gates is not None else None
        return f"{self.__class__.__name__}(gates={gate_names}, qubits={self._qubits})"

    def applicable_key_types(self) -> Iterable[CriteriaKey]:
        """
        Returns:
            Iterable[CriteriaKey]: This Criteria operates on Gates and Qubits.
        """
        return [CriteriaKey.QUBIT, CriteriaKey.GATE]

    def get_keys(self, key_type: CriteriaKey) -> Union[CriteriaKeyResult, Set[Any]]:
        """Gets the keys for a given CriteriaKey.

        Args:
            key_type (CriteriaKey): The relevant Criteria Key.

        Returns:
            Union[CriteriaKeyResult, Set[Any]]: The return value is based on the key type:
            GATE will return a set of Gate classes that are relevant to this Criteria.
            QUBIT will return a set of qubit targets that are relevant to this Criteria, or
            CriteriaKeyResult.ALL if the Criteria is relevant for all (possible) qubits.
            All other keys will return an empty list.
        """
        if key_type == CriteriaKey.GATE:
            return CriteriaKeyResult.ALL if self._gates is None else self._gates
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
        gates = [gate.__name__ for gate in self._gates] if self._gates is not None else None
        return {
            "__class__": self.__class__.__name__,
            "gates": gates,
            "qubits": qubits,
        }

    def instruction_matches(self, instruction: Instruction) -> bool:
        """Returns true if an Instruction matches the criteria.

        Args:
            instruction (Instruction): An Instruction to match.

        Returns:
            bool: Returns true if the operator is one of the Gates provided in the constructor and
            the target is a qubit (or set of qubits) provided in the constructor.
            If gates were not provided in the constructor, then this method will accept any Gate.
            If qubits were not provided in the constructor, then this method will accept any
            Instruction target.
        """
        if isinstance(instruction, Iterable):
            return False
        if not isinstance(instruction.operator, Gate):
            return False
        if self._gates is not None and type(instruction.operator) not in self._gates:
            return False
        return CircuitInstructionCriteria._check_target_in_qubits(self._qubits, instruction.target)

    @classmethod
    def from_dict(cls, criteria: dict) -> Criteria:
        """Deserializes a dictionary into a Criteria object.

        Args:
            criteria (dict): A dictionary representation of a GateCriteria.

        Returns:
            Criteria: A deserialized GateCriteria represented by the passed in
            serialized data.
        """
        gates = (
            [getattr(Gate, name) for name in criteria["gates"]]
            if criteria["gates"] is not None
            else None
        )
        return GateCriteria(gates, criteria["qubits"])


Criteria.register_criteria(GateCriteria)
