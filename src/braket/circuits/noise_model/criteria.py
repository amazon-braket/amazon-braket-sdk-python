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

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import Any


class CriteriaKey(str, Enum):
    """Specifies the types of keys that a criteria may use to match an instruction,
    observable, etc.
    """

    QUBIT = "QUBIT"
    GATE = "GATE"
    UNITARY_GATE = "UNITARY_GATE"
    OBSERVABLE = "OBSERVABLE"


class CriteriaKeyResult(str, Enum):
    """The get_keys() method may return this enum instead of actual keys for
    a given criteria key type.
    """

    ALL = "ALL"


class Criteria(ABC):
    """Represents conditions that need to be met for a noise to apply to a circuit."""

    @abstractmethod
    def applicable_key_types(self) -> Iterable[CriteriaKey]:
        """Returns the relevant set of keys for the Criteria

        This informs what the Criteria operates on and can be used to optimize
        which Criteria is relevant.

        Returns:
            Iterable[CriteriaKey]: The relevant set of keys for the Criteria.
        """
        raise NotImplementedError

    @abstractmethod
    def get_keys(self, key_type: CriteriaKey) -> CriteriaKeyResult | set[Any]:
        """Returns a set of key for a given key type.

        Args:
            key_type (CriteriaKey): The criteria key type.

        Returns:
            Union[CriteriaKeyResult, set[Any]]: Returns a set of keys for a key type. The
            actual returned keys will depend on the CriteriaKey. If the provided key type
            is not relevant the returned list will be empty. If the provided key type is
            relevant for all possible inputs, the string CriteriaKeyResult.ALL will be returned.
        """
        raise NotImplementedError

    def __eq__(self, other: Criteria):
        if not isinstance(other, Criteria):
            return NotImplemented
        if self.applicable_key_types() != other.applicable_key_types():
            return False
        return all(
            self.get_keys(key_type) == other.get_keys(key_type)
            for key_type in self.applicable_key_types()
        )

    @abstractmethod
    def to_dict(self) -> dict:
        """Converts this Criteria object into a dict representation

        Returns:
            dict: A dictionary object representing the Criteria.
        """
        raise NotImplementedError

    @classmethod
    def from_dict(cls, criteria: dict) -> Criteria:
        """Converts a dictionary representing an object of this class into an instance of this
        class.

        Args:
            criteria (dict): A dictionary representation of an object of this class.

        Returns:
            Criteria: An object of this class that corresponds to the passed in dictionary.
        """
        if "__class__" in criteria:
            criteria_name = criteria["__class__"]
            criteria_cls = getattr(Criteria, criteria_name)
            return criteria_cls.from_dict(criteria)
        raise NotImplementedError

    @classmethod
    def register_criteria(cls, criteria: type[Criteria]) -> None:
        """Register a criteria implementation by adding it into the Criteria class.

        Args:
            criteria (type[Criteria]): Criteria class to register.
        """
        setattr(cls, criteria.__name__, criteria)
