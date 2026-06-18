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

import numbers
from collections.abc import Iterable
from itertools import combinations, starmap

from braket.circuits.observable import Observable, StandardObservable
from braket.circuits.observables import I, Sum, TensorProduct, X, Y, Z
from braket.quantum_information.pauli_string import PauliString

_OBSERVABLE_TO_FACTOR = {I: "I", X: "X", Y: "Y", Z: "Z"}


class PauliSum:
    """A weighted sum of Pauli strings."""

    def __init__(self, terms: Iterable[tuple[numbers.Number, str | PauliString]] = ()):
        """Initializes a ``PauliSum``.

        Args:
            terms (Iterable[tuple[numbers.Number, str | PauliString]]): Pairs of coefficient and
                Pauli string.
        """
        self._terms: dict[str, numbers.Number] = {}
        for coefficient, pauli_string in terms:
            self._add_term(coefficient, PauliString(pauli_string))
        self._all_terms_commute = self._compute_all_terms_commute()

    @property
    def all_terms_commute(self) -> bool:
        """bool: Whether all terms in the sum commute with each other."""
        return self._all_terms_commute

    @classmethod
    def from_list(cls, terms: Iterable[tuple[numbers.Number, str | PauliString]]) -> PauliSum:
        """Builds a ``PauliSum`` from a list of weighted Pauli strings."""
        return cls(terms)

    @property
    def terms(self) -> tuple[tuple[numbers.Number, PauliString], ...]:
        """tuple[tuple[numbers.Number, PauliString], ...]: The weighted Pauli terms."""
        return tuple(
            (coefficient, PauliString(pauli)) for pauli, coefficient in self._terms.items()
        )

    @property
    def qubit_count(self) -> int:
        """int: The number of qubits in the largest Pauli string term."""
        if not self._terms:
            return 0
        return max(PauliString(pauli).qubit_count for pauli in self._terms)

    def to_list(self) -> list[tuple[numbers.Number, str]]:
        """Returns a list representation of the weighted Pauli strings."""
        return [(coefficient, pauli) for pauli, coefficient in self._terms.items()]

    def to_sum(self) -> Sum:
        """Converts the weighted Pauli strings into a circuit ``Sum`` observable."""
        if not self._terms:
            raise ValueError("Cannot convert an empty PauliSum to Sum")
        observables = []
        for coefficient, pauli in self.terms:
            observables.append(coefficient * pauli.to_unsigned_observable(include_trivial=True))
        return Sum(observables)

    def commutes_with(self, other: PauliSum | PauliString | str) -> bool:
        """Returns whether all terms commute with ``other``."""
        other_sum = self._coerce(other)
        if not self.all_terms_commute or not other_sum.all_terms_commute:
            return False
        return all(
            self._pauli_strings_commute(left, right)
            for _, left in self.terms
            for _, right in other_sum.terms
        )

    def is_self_commuting(self) -> bool:
        """Returns whether all terms in this sum commute with each other."""
        return self._all_terms_commute

    @classmethod
    def from_sum(cls, observable_sum: Sum) -> PauliSum:
        """Builds a ``PauliSum`` from a circuit ``Sum`` observable."""
        if not isinstance(observable_sum, Sum):
            raise TypeError("Expected a Sum observable")
        return cls(cls._term_from_observable(observable) for observable in observable_sum.summands)

    def __add__(self, other: PauliSum | PauliString | str) -> PauliSum:
        other_sum = self._coerce(other)
        return PauliSum((*self.terms, *other_sum.terms))

    def __radd__(self, other: PauliSum | PauliString | str) -> PauliSum:
        return self + other

    def __sub__(self, other: PauliSum | PauliString | str) -> PauliSum:
        return self + (-1 * self._coerce(other))

    def __rsub__(self, other: PauliSum | PauliString | str) -> PauliSum:
        return self._coerce(other) + (-self)

    def __neg__(self) -> PauliSum:
        return -1 * self

    def __mul__(self, other: numbers.Number | PauliString | str) -> PauliSum:
        if isinstance(other, numbers.Number):
            return PauliSum((coefficient * other, pauli) for coefficient, pauli in self.terms)
        pauli = PauliString(other)
        qubit_count = max(self.qubit_count, pauli.qubit_count)
        right = self._pad_pauli_string(pauli, qubit_count)
        return PauliSum(
            (coefficient, self._pad_pauli_string(term, qubit_count).dot(right))
            for coefficient, term in self.terms
        )

    def __rmul__(self, other: numbers.Number | PauliString | str) -> PauliSum:
        if isinstance(other, numbers.Number):
            return self * other
        pauli = PauliString(other)
        qubit_count = max(self.qubit_count, pauli.qubit_count)
        left = self._pad_pauli_string(pauli, qubit_count)
        return PauliSum(
            (coefficient, left.dot(self._pad_pauli_string(term, qubit_count)))
            for coefficient, term in self.terms
        )

    def __contains__(self, item: str | PauliString) -> bool:
        _, pauli = self._canonical_term(PauliString(item))
        return pauli in self._terms

    def __getitem__(self, item: int) -> tuple[numbers.Number, PauliString]:
        return self.terms[item]

    def __iter__(self):
        return iter(self.terms)

    def __len__(self) -> int:
        return len(self._terms)

    def __eq__(self, other: PauliSum) -> bool:
        if not isinstance(other, PauliSum):
            return False
        return self._terms == other._terms

    def __repr__(self) -> str:
        return f"PauliSum({self.to_list()})"

    def _add_term(self, coefficient: numbers.Number, pauli_string: PauliString) -> None:
        if not isinstance(coefficient, numbers.Number):
            raise TypeError("PauliSum coefficients must be numbers")
        coefficient, pauli = self._canonical_term(pauli_string, coefficient)
        if coefficient == 0:
            return
        new_coefficient = self._terms.get(pauli, 0) + coefficient
        if new_coefficient == 0:
            self._terms.pop(pauli, None)
        else:
            self._terms[pauli] = new_coefficient

    def _compute_all_terms_commute(self) -> bool:
        if len(self._terms) <= 1:
            return True
        paulis = [PauliString(pauli) for pauli in self._terms]
        return all(starmap(self._pauli_strings_commute, combinations(paulis, 2)))

    @staticmethod
    def _canonical_term(
        pauli_string: PauliString, coefficient: numbers.Number = 1
    ) -> tuple[numbers.Number, str]:
        factors = ["I"] * pauli_string.qubit_count
        for qubit in range(pauli_string.qubit_count):
            factors[qubit] = "IXYZ"[pauli_string[qubit]]
        return coefficient * pauli_string.phase, f"+{''.join(factors)}"

    @staticmethod
    def _coerce(other: PauliSum | PauliString | str) -> PauliSum:
        if isinstance(other, PauliSum):
            return other
        return PauliSum([(1, other)])

    @staticmethod
    def _pauli_strings_commute(left: PauliString, right: PauliString) -> bool:
        anticommuting_factors = 0
        qubit_count = max(left.qubit_count, right.qubit_count)
        for qubit in range(qubit_count):
            left_factor = left[qubit] if qubit < left.qubit_count else 0
            right_factor = right[qubit] if qubit < right.qubit_count else 0
            if left_factor and right_factor and left_factor != right_factor:
                anticommuting_factors += 1
        return anticommuting_factors % 2 == 0

    @staticmethod
    def _pad_pauli_string(pauli_string: PauliString, qubit_count: int) -> PauliString:
        if pauli_string.qubit_count == qubit_count:
            return pauli_string
        factors = ["I"] * qubit_count
        for qubit in range(pauli_string.qubit_count):
            factors[qubit] = "IXYZ"[pauli_string[qubit]]
        sign = "-" if pauli_string.phase < 0 else "+"
        return PauliString(f"{sign}{''.join(factors)}")

    @staticmethod
    def _term_from_observable(observable: Observable) -> tuple[numbers.Number, str]:
        coefficient = observable.coefficient
        unscaled = observable._unscaled()
        if isinstance(unscaled, StandardObservable):
            factors = PauliSum._factors_from_standard(unscaled)
        elif isinstance(unscaled, TensorProduct):
            factors = PauliSum._factors_from_tensor_product(unscaled)
        else:
            raise TypeError(f"Unsupported observable type {type(observable).__name__}")
        return coefficient, f"+{''.join(factors)}"

    @staticmethod
    def _factors_from_standard(observable: StandardObservable) -> list[str]:
        factor = PauliSum._factor_from_standard(observable)
        if observable.targets:
            factors = ["I"] * (max(observable.targets) + 1)
            factors[int(observable.targets[0])] = factor
            return factors
        return [factor]

    @staticmethod
    def _factors_from_tensor_product(observable: TensorProduct) -> list[str]:
        if observable.targets:
            factors = ["I"] * (max(observable.targets) + 1)
            for factor, target in zip(observable.factors, observable.targets, strict=True):
                factors[int(target)] = PauliSum._factor_from_standard(factor)
            return factors
        return [PauliSum._factor_from_standard(factor) for factor in observable.factors]

    @staticmethod
    def _factor_from_standard(observable: StandardObservable) -> str:
        for observable_type, factor in _OBSERVABLE_TO_FACTOR.items():
            if isinstance(observable, observable_type):
                return factor
        raise TypeError(f"Unsupported observable factor {type(observable).__name__}")


PauliStringSum = PauliSum
