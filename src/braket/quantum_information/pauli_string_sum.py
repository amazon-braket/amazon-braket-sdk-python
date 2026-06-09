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

from typing import Union

from braket.quantum_information.pauli_string import PauliString

_Term = Union[tuple[float, Union[str, PauliString]], PauliString]


class PauliStringSum:
    """A weighted sum of :class:`PauliString` objects.

    Supports addition, subtraction, scalar multiplication, and multiplication
    by a :class:`PauliString`.  Duplicate terms are automatically combined.

    Args:
        terms: An iterable of either :class:`PauliString` objects (weight 1)
            or ``(weight, pauli)`` tuples where *pauli* is a string or
            :class:`PauliString`.

    Examples::

        from braket.quantum_information import PauliString, PauliStringSum

        s = PauliStringSum([(1.0, "XY"), (0.5, "ZI")])
        s += PauliStringSum([(1.0, "XY")])     # coefficient of XY becomes 2.0
        s2 = 3.0 * s
    """

    def __init__(self, terms=None):
        self._terms: dict[str, tuple[float, PauliString]] = {}
        if terms is None:
            return
        for item in terms:
            if isinstance(item, PauliString):
                self._add_term(1.0, item)
            elif isinstance(item, tuple) and len(item) == 2:
                coeff, pauli = item
                if not isinstance(pauli, PauliString):
                    pauli = PauliString(pauli)
                self._add_term(float(coeff), pauli)
            else:
                raise TypeError(
                    f"Each term must be a PauliString or (coeff, pauli) tuple, got {type(item)}"
                )

    def _add_term(self, coeff: float, pauli: PauliString) -> None:
        key = repr(pauli)
        if key in self._terms:
            new_coeff = self._terms[key][0] + coeff
            self._terms[key] = (new_coeff, pauli)
        else:
            self._terms[key] = (coeff, pauli)

    def _drop_zeros(self, tol: float = 1e-12) -> None:
        self._terms = {k: v for k, v in self._terms.items() if abs(v[0]) > tol}

    @classmethod
    def from_list(cls, terms: list[tuple[float, str]]) -> PauliStringSum:
        """Construct from a list of ``(coefficient, pauli_string_str)`` tuples.

        Args:
            terms: List of ``(float, str)`` pairs.

        Returns:
            PauliStringSum: The corresponding sum.
        """
        return cls(terms)

    def to_list(self) -> list[tuple[float, str]]:
        """Return a list of ``(coefficient, pauli_string_str)`` pairs.

        Returns:
            list[tuple[float, str]]: The terms, one per non-zero entry.
        """
        return [(coeff, repr(ps)) for coeff, ps in self._terms.values()]

    def __len__(self) -> int:
        return len(self._terms)

    def __iter__(self):
        for coeff, ps in self._terms.values():
            yield coeff, ps

    def __contains__(self, item) -> bool:
        if isinstance(item, str):
            item = PauliString(item)
        if isinstance(item, PauliString):
            return repr(item) in self._terms
        return False

    def __getitem__(self, key):
        if isinstance(key, int):
            items = list(self._terms.values())
            return items[key]
        if isinstance(key, str):
            key = PauliString(key)
        if isinstance(key, PauliString):
            k = repr(key)
            if k not in self._terms:
                raise KeyError(key)
            return self._terms[k][0]
        raise TypeError(f"Index must be int, str, or PauliString, got {type(key)}")

    def __add__(self, other) -> PauliStringSum:
        result = PauliStringSum()
        result._terms = dict(self._terms)
        if isinstance(other, PauliStringSum):
            for coeff, ps in other:
                result._add_term(coeff, ps)
        elif isinstance(other, PauliString):
            result._add_term(1.0, other)
        elif isinstance(other, tuple) and len(other) == 2:
            coeff, ps = other
            if not isinstance(ps, PauliString):
                ps = PauliString(ps)
            result._add_term(float(coeff), ps)
        else:
            return NotImplemented
        result._drop_zeros()
        return result

    def __radd__(self, other) -> PauliStringSum:
        return self.__add__(other)

    def __iadd__(self, other) -> PauliStringSum:
        if isinstance(other, PauliStringSum):
            for coeff, ps in other:
                self._add_term(coeff, ps)
        elif isinstance(other, PauliString):
            self._add_term(1.0, other)
        elif isinstance(other, tuple) and len(other) == 2:
            coeff, ps = other
            if not isinstance(ps, PauliString):
                ps = PauliString(ps)
            self._add_term(float(coeff), ps)
        else:
            return NotImplemented
        self._drop_zeros()
        return self

    def __neg__(self) -> PauliStringSum:
        result = PauliStringSum()
        result._terms = {k: (-c, ps) for k, (c, ps) in self._terms.items()}
        return result

    def __sub__(self, other) -> PauliStringSum:
        if isinstance(other, (PauliStringSum, PauliString, tuple)):
            return self.__add__(
                -PauliStringSum(
                    [other] if not isinstance(other, PauliStringSum) else list(other)
                )
            )
        return NotImplemented

    def __rsub__(self, other) -> PauliStringSum:
        return (-self).__add__(other)

    def __isub__(self, other) -> PauliStringSum:
        neg = -PauliStringSum(
            [other] if not isinstance(other, PauliStringSum) else list(other)
        )
        return self.__iadd__(neg)

    def __mul__(self, other) -> PauliStringSum:
        if isinstance(other, (int, float)):
            result = PauliStringSum()
            result._terms = {k: (c * other, ps) for k, (c, ps) in self._terms.items()}
            result._drop_zeros()
            return result
        if isinstance(other, PauliString):
            result = PauliStringSum()
            for coeff, ps in self:
                product = ps.dot(other)
                result._add_term(coeff * product._phase, PauliString(repr(product)))
            result._drop_zeros()
            return result
        return NotImplemented

    def __rmul__(self, other) -> PauliStringSum:
        if isinstance(other, (int, float)):
            return self.__mul__(other)
        if isinstance(other, PauliString):
            result = PauliStringSum()
            for coeff, ps in self:
                product = other.dot(ps)
                result._add_term(coeff * product._phase, PauliString(repr(product)))
            result._drop_zeros()
            return result
        return NotImplemented

    def __imul__(self, other) -> PauliStringSum:
        if isinstance(other, (int, float)):
            self._terms = {k: (c * other, ps) for k, (c, ps) in self._terms.items()}
            self._drop_zeros()
            return self
        return NotImplemented

    def __eq__(self, other) -> bool:
        if not isinstance(other, PauliStringSum):
            return False
        self._drop_zeros()
        other._drop_zeros()
        if set(self._terms.keys()) != set(other._terms.keys()):
            return False
        for k in self._terms:
            sc, _ = self._terms[k]
            oc, _ = other._terms[k]
            if abs(sc - oc) > 1e-12:
                return False
        return True

    def __repr__(self) -> str:
        if not self._terms:
            return "PauliStringSum([])"
        parts = [f"{c:+g} * {repr(ps)}" for c, ps in self._terms.values()]
        return " ".join(parts)

    def commutes_with(self, other: PauliStringSum | PauliString) -> bool:
        """Return True if this sum commutes with *other*.

        Checks whether [self, other] = self * other - other * self is the zero sum.

        Args:
            other: Another :class:`PauliStringSum` or :class:`PauliString`.

        Returns:
            bool: True if the commutator vanishes.
        """
        if isinstance(other, PauliString):
            other = PauliStringSum([other])
        ab = self * other if isinstance(other, PauliString) else self._mul_sum(other)
        ba = (
            other._mul_sum(self)
            if isinstance(other, PauliStringSum)
            else PauliStringSum([other])._mul_sum(self)
        )
        return (ab + (-ba)) == PauliStringSum()

    def _mul_sum(self, other: PauliStringSum) -> PauliStringSum:
        result = PauliStringSum()
        for c1, ps1 in self:
            for c2, ps2 in other:
                product = ps1.dot(ps2)
                new_coeff = c1 * c2 * product._phase
                clean = PauliString.__new__(PauliString)
                clean._phase = 1
                clean._qubit_count = product._qubit_count
                clean._nontrivial = dict(product._nontrivial)
                result._add_term(new_coeff, clean)
        result._drop_zeros()
        return result

    def is_self_commuting(self) -> bool:
        """Return True if all pairs of terms in this sum commute with each other.

        Returns:
            bool: True if every pair of constituent :class:`PauliString` terms commutes.
        """
        terms_list = list(self._terms.values())
        for i in range(len(terms_list)):
            for j in range(i + 1, len(terms_list)):
                _, ps_i = terms_list[i]
                _, ps_j = terms_list[j]
                ab = ps_i.dot(ps_j)
                ba = ps_j.dot(ps_i)
                if ab != ba:
                    return False
        return True
