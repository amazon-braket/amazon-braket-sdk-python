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

from collections.abc import Mapping, Sequence
from typing import Union

import numpy as np

ParameterSetsLike = Union[
    "ParameterSets", Sequence[Mapping[str, float]], Mapping[str, Sequence[float]]
]


class ParameterSets:
    def __init__(
        self,
        parameter_sets: ParameterSetsLike | None = None,
        *,
        keys: Sequence[str] | None = None,
        values: Sequence[Sequence[float]] | np.ndarray | None = None,
        **kwargs,
    ):
        """
        Stores a sequence of parameter sets for a parametrized circuit.

        Exactly one of inputs, keys and values, or kwargs must be specified.

        Args:
            parameter_sets (ParameterSetsLike | None): Multiple
                inputs to a parametrized circuit; must either be a list of dicts, where every dict
                has the same parameter names for keys, or a dict mapping parameter names to lists of
                values, where each list must be the same length. Default: None.
            keys (Sequence[str] | None): A list of parameter names as strings. If specified, values
                must also be specified. Default: None.
            values (Sequence[Sequence[float]] | ndarray | None): A list of parameter value lists,
                in the same order as keys; each list must be the same length. Default: None.
            **kwargs: Keys are parameter names, while values are lists of values; each list must be
                the same length.
        """
        ParameterSets._validate_combinations(parameter_sets, keys=keys, values=values, **kwargs)
        if parameter_sets:
            match parameter_sets:
                case ParameterSets(_inputs=inputs):
                    self._inputs = inputs
                case Mapping():
                    self._inputs = ParameterSets._mapping_to_dict(parameter_sets)
                case Sequence():
                    self._inputs = ParameterSets._sequence_to_dict(parameter_sets)
                case _:
                    raise TypeError(f"Unsupported type {type(parameter_sets)} for ParameterSets")
        elif keys:
            self._inputs = ParameterSets._mapping_to_dict(dict(zip(keys, values, strict=True)))
        elif kwargs:
            self._inputs = ParameterSets._mapping_to_dict(kwargs)
        else:
            self._inputs = None

    def as_dict(self) -> dict[str, list[float]]:
        """The keys and corresponding value lists of this ParameterSets object.

        Returns:
            dict[str, list[float]]: A dict mapping parameter names to lists of values.
        """
        return self._inputs

    def as_list(self) -> list[dict[str, float]]:
        """A list of dicts mapping parameters to the ith value

        Returns:
            list[dict[str, float]]: A list of dicts mapping parameter names to values.
        """
        items = self._inputs.items()
        return [{k: v[i] for k, v in items} for i in range(len(self))]

    def __len__(self):
        return len(next(iter(self._inputs.values()))) if self._inputs else 0

    def __add__(self, other: ParameterSetsLike):
        other_cast = other if isinstance(other, ParameterSets) else ParameterSets(other)
        if set(self._inputs.keys()) != set(other_cast._inputs.keys()):
            raise ValueError("Mismatched keys between parameter sets")
        other_dict = other_cast.as_dict() or {}
        return ParameterSets({k: v + other_dict[k] for k, v in self.as_dict().items()})

    def __mul__(self, other: ParameterSetsLike):
        other_cast = other if isinstance(other, ParameterSets) else ParameterSets(other)
        product = {
            k: list(sum(zip(*([v] * len(other_cast)), strict=True), ()))
            for k, v in self.as_dict().items()
        }
        other_multiplied = {k: v * len(self) for k, v in (other_cast.as_dict() or {}).items()}
        product.update(other_multiplied)
        return ParameterSets(product)

    def __repr__(self):
        return repr(self.as_dict())

    def __eq__(self, other: ParameterSetsLike):
        if isinstance(other, ParameterSets):
            return self._inputs == other._inputs
        try:
            return self._inputs == ParameterSets(other)._inputs
        except Exception:
            return False

    @staticmethod
    def _sequence_to_dict(inputs_list: Sequence[Mapping[str, float]]) -> dict[str, list[float]]:
        converted = {k: [v] for k, v in inputs_list[0].items()}
        for inputs in inputs_list[1:]:
            remaining = set(converted.keys())
            for k, v in inputs.items():
                if k not in converted:
                    raise ValueError("Mismatched keys in inputs_list")
                converted[k].append(v)
                remaining.remove(k)
            if remaining:
                raise ValueError("Mismatched keys in inputs_list")
        return converted

    @staticmethod
    def _mapping_to_dict(inputs_dict: Mapping[str, Sequence[float]]) -> dict[str, list[float]]:
        items = list(inputs_dict.items())
        k0, v0 = items[0]
        inputs = {k0: list(v0)}
        length = len(v0)
        for k, v in items[1:]:
            if len(v) != length:
                raise ValueError("List of values must be identical for all keys")
            inputs[k] = list(v)
        return inputs

    @staticmethod
    def _validate_combinations(
        parameter_sets: ParameterSetsLike | None,
        *,
        keys: Sequence[str] | None,
        values: Sequence[Sequence[float]] | np.ndarray | None,
        **kwargs,
    ) -> None:
        if parameter_sets and (keys is not None or values is not None):
            raise ValueError("Can only populate one of inputs or key-value pairs")
        if parameter_sets and kwargs:
            raise ValueError("Can only populate one of inputs or kwargs")
        if kwargs and (keys is not None or values is not None):
            raise ValueError("Can only populate one of kwargs or key-value pairs")
        if (keys is not None and values is None) or (values is not None and keys is None):
            raise ValueError("Both keys and values must be specified")
