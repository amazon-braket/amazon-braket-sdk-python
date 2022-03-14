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
from braket.circuits.noise_model.criteria_input_parsing import (
    parse_operator_input,
    parse_qubit_input,
)
from braket.circuits.noise_model.result_type_criteria import ResultTypeCriteria
from braket.circuits.observable import Observable
from braket.circuits.qubit_set import QubitSetInput
from braket.circuits.result_type import ObservableResultType, ResultType


class ObservableCriteria(ResultTypeCriteria):
    """This class models noise Criteria based on the Braket SDK Observable classes."""

    def __init__(
        self,
        observables: Optional[Union[Observable, Iterable[Observable]]] = None,
        qubits: Optional[QubitSetInput] = None,
    ):
        """
        Creates Observable-based Criteria. See instruction_matches() for more details.

        Args:
            observables (Optional[Union[Observable, Iterable[Observable]]]): A set of relevant
                Observables. Observables must only operate on a single qubit. Optional. If
                observables are not specified, this criteria will match on any observable.
            qubits (Optional[QubitSetInput]): A set of relevant qubits. If no qubits
                are provided, all (possible) qubits are considered to be relevant.

        Throws:
            ValueError: If the operators operate on more than one qubit.
        """
        self._observables = parse_operator_input(observables)
        self._qubits = parse_qubit_input(qubits, 1)

    def __str__(self):
        observables_names = (
            {observable.__name__ for observable in self._observables}
            if self._observables is not None
            else None
        )
        return f"{self.__class__.__name__}({observables_names}, {self._qubits})"

    def __repr__(self):
        observables_names = (
            {observable.__name__ for observable in self._observables}
            if self._observables is not None
            else None
        )
        return f"{self.__class__.__name__}(observables={observables_names}, qubits={self._qubits})"

    def applicable_key_types(self) -> Iterable[CriteriaKey]:
        """
        Returns:
            Iterable[CriteriaKey]: This Criteria operates on Observables and Qubits.
        """
        return [CriteriaKey.OBSERVABLE, CriteriaKey.QUBIT]

    def get_keys(self, key_type: CriteriaKey) -> Union[CriteriaKeyResult, Set[Any]]:
        """Gets the keys for a given CriteriaKey.

        Args:
            key_type (CriteriaKey): The relevant Criteria Key.

        Returns:
            Union[CriteriaKeyResult, Set[Any]]: The return value is based on the key type:
            OBSERVABLE will return a set of Observable classes that are relevant to this Criteria,
            or CriteriaKeyResult.ALL if the Criteria is relevant for all (possible) observables.
            QUBIT will return a set of qubit targets that are relevant to this Criteria, or
            CriteriaKeyResult.ALL if the Criteria is relevant for all (possible) qubits.
            All other keys will return an empty set.
        """
        if key_type == CriteriaKey.OBSERVABLE:
            return CriteriaKeyResult.ALL if self._observables is None else set(self._observables)
        if key_type == CriteriaKey.QUBIT:
            return CriteriaKeyResult.ALL if self._qubits is None else set(self._qubits)
        return set()

    def to_dict(self) -> dict:
        """
        Converts a dictionary representing an object of this class into an instance of this class.

        Returns:
            dict: A dictionary representing the serialized version of this Criteria.
        """
        observables = (
            [observable.__name__ for observable in self._observables]
            if self._observables is not None
            else None
        )
        qubits = list(self._qubits) if self._qubits is not None else None
        return {
            "__class__": self.__class__.__name__,
            "observables": observables,
            "qubits": qubits,
        }

    def result_type_matches(self, result_type: ResultType) -> bool:
        """Returns true if a result type matches the criteria.

        Args:
            result_type (ResultType): A result type or list of result types to match.
        Returns:
            bool: Returns true if the result type is one of the Observables provided in the
            constructor and the target is a qubit (or set of qubits)provided in the constructor.
            If observables were not provided in the constructor, then this method will accept any
            Observable.
            If qubits were not provided in the constructor, then this method will accept any
            result type target.
        """
        if not isinstance(result_type, ObservableResultType):
            return False
        if self._observables is not None and type(result_type.observable) not in self._observables:
            return False
        if self._qubits is None:
            return True
        target = list(result_type.target)
        if not target:
            return True
        return target[0] in self._qubits

    @classmethod
    def from_dict(cls, criteria: dict) -> Criteria:
        """Deserializes a dictionary into a Criteria object.

        Args:
            criteria (dict): A dictionary representation of a GateCriteria.

        Returns:
            Criteria: A deserialized GateCriteria represented by the passed in
            serialized data.
        """
        observables = (
            [getattr(Observable, name) for name in criteria["observables"]]
            if criteria["observables"] is not None
            else None
        )
        return ObservableCriteria(observables, criteria["qubits"])


Criteria.register_criteria(ObservableCriteria)
