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

import itertools
import numbers
from collections.abc import Iterable, Iterator, Sequence

from braket.circuits.circuit import Circuit
from braket.circuits.observable import Observable
from braket.circuits.observables import I, Sum, TensorProduct, X, Y, Z

_IDENTITY = "I"
_PAULI_X = "X"
_PAULI_Y = "Y"
_PAULI_Z = "Z"
_PAULI_INDICES = {_IDENTITY: 0, _PAULI_X: 1, _PAULI_Y: 2, _PAULI_Z: 3}
_PRODUCT_MAP = {
    "X": {"Y": ["Z", 1j], "Z": ["Y", -1j]},
    "Y": {"X": ["Z", -1j], "Z": ["X", 1j]},
    "Z": {"X": ["Y", 1j], "Y": ["X", -1j]},
}
_ID_OBS = I()
_PAULI_OBSERVABLES = {_PAULI_X: X(), _PAULI_Y: Y(), _PAULI_Z: Z()}
_SIGN_MAP = {"+": 1, "-": -1}


class PauliString:
    """A lightweight representation of a Pauli string with its phase."""

    def __init__(self, pauli_string: str | PauliString):
        """Initializes a `PauliString`.

        Args:
            pauli_string (str | PauliString): The representation of the pauli word, either a
                string or another PauliString object. A valid string consists of an optional phase,
                specified by an optional sign +/- followed by an uppercase string in {I, X, Y, Z}.
                Example valid strings are: XYZ, +YIZY, -YX

        Raises:
            ValueError: If the Pauli String is empty.
        """
        if not pauli_string:
            raise ValueError("pauli_string must not be empty")
        if isinstance(pauli_string, PauliString):
            self._phase = pauli_string._phase
            self._qubit_count = pauli_string._qubit_count
            self._nontrivial = pauli_string._nontrivial
        elif isinstance(pauli_string, str):
            self._phase, factors_str = PauliString._split(pauli_string)
            self._qubit_count = len(factors_str)
            self._nontrivial = {
                i: factors_str[i] for i in range(len(factors_str)) if factors_str[i] != "I"
            }
        else:
            raise TypeError(f"Pauli word {pauli_string} must be of type {PauliString} or {str}")

    @property
    def phase(self) -> int:
        """int: The phase of the Pauli string.

        Can be one of +/-1
        """
        return self._phase

    @property
    def qubit_count(self) -> int:
        """int: The number of qubits this Pauli string acts on."""
        return self._qubit_count

    def to_unsigned_observable(self, include_trivial: bool = False) -> TensorProduct:
        """Returns the observable corresponding to the unsigned part of the Pauli string.

        For example, for a Pauli string -XYZ, the corresponding observable is X ⊗ Y ⊗ Z.

        Args:
            include_trivial (bool): Whether to include explicit identity factors in the observable.
                Default: False.

        Returns:
            TensorProduct: The tensor product of the unsigned factors in the Pauli string.
        """
        if include_trivial:
            return TensorProduct([
                (
                    _PAULI_OBSERVABLES[self._nontrivial[qubit]]
                    if qubit in self._nontrivial
                    else _ID_OBS
                )
                for qubit in range(self._qubit_count)
            ])
        return TensorProduct([
            _PAULI_OBSERVABLES[self._nontrivial[qubit]] for qubit in sorted(self._nontrivial)
        ])

    def weight_n_substrings(self, weight: int) -> tuple[PauliString, ...]:
        r"""Returns every substring of this Pauli string with exactly `weight` nontrivial factors.

        The number of substrings is equal to :math:`\binom{n}{w}`, where :math`n` is the number of
        nontrivial (non-identity) factors in the Pauli string and :math`w` is `weight`.

        Args:
            weight (int): The number of non-identity factors in the substrings.

        Returns:
            tuple[PauliString, ...]: A tuple of weight-n Pauli substrings.
        """
        substrings = []
        for indices in itertools.combinations(self._nontrivial, weight):
            idx_set = set(indices)
            nontrivial = {i: self._nontrivial[i] for i in idx_set}
            # Bypass __init__ via __new__ to skip string parsing. The internal
            # state (phase, qubit_count, nontrivial dict) is already known here,
            # so going through PauliString(str) would only round-trip the data
            # through a dense string representation for no benefit.
            ps = PauliString.__new__(PauliString)
            ps._phase = self._phase
            ps._qubit_count = self._qubit_count
            ps._nontrivial = nontrivial
            substrings.append(ps)
        return tuple(substrings)

    def eigenstate(self, signs: str | list[int] | tuple[int, ...] | None = None) -> Circuit:
        """Returns the eigenstate of this Pauli string with the given factor signs.

        The resulting eigenstate has each qubit in the +1 eigenstate of its corresponding signed
        Pauli operator. For example, a Pauli string +XYZ and signs ++- has factors +X, +Y and -Z,
        with the corresponding qubits in states `|+⟩` , `|i⟩` , and `|1⟩` respectively (the global
        phase of the Pauli string is ignored).

        Args:
            signs (str | list[int] | tuple[int, ...] | None): The sign of each factor of the
                eigenstate, specified either as a string of "+" and "_", or as a list or tuple of
                +/-1. The length of signs must be equal to the length of the Pauli string. If not
                specified, it is assumed to be all +. Default: None.

        Returns:
            Circuit: A circuit that prepares the desired eigenstate of the Pauli string.

        Raises:
            ValueError: If the length of signs is not equal to that of the Pauli string or the signs
                are invalid.
        """
        qubit_count = self._qubit_count
        if not signs:
            signs = "+" * qubit_count
        elif len(signs) != qubit_count:
            raise ValueError(
                f"signs must be the same length of the Pauli string ({qubit_count}), "
                f"but was {len(signs)}"
            )
        signs_tup = (
            tuple(_SIGN_MAP.get(sign) for sign in signs) if isinstance(signs, str) else tuple(signs)
        )
        if not set(signs_tup) <= {1, -1}:
            raise ValueError(f"signs must be +/-1, got {signs}")
        return self._generate_eigenstate_circuit(signs_tup)

    def dot(self, other: PauliString, inplace: bool = False) -> PauliString:
        """Right multiplies this Pauli string with the argument.

        Returns the result of multiplying the current circuit by the argument on its right. For
        example, if called on `-XYZ` with argument `ZYX`, then `YIY` is the result. In-place
        computation is off by default.

        Args:
            other (PauliString): The right multiplicand.
            inplace (bool): If `True`, `self` is updated to hold the product.

        Returns:
            PauliString: The resultant circuit from right multiplying `self` with `other`.

        Raises:
            ValueError: If the lengths of the Pauli strings being multiplied differ.
        """
        if self._qubit_count != other._qubit_count:
            raise ValueError(
                f"Input Pauli string must be of length ({self._qubit_count}), "
                f"not {other._qubit_count}"
            )
        pauli_result = {}
        phase_result = self._phase * other._phase
        for i in self._nontrivial:
            if i not in other._nontrivial:
                pauli_result[i] = self._nontrivial[i]
            elif self._nontrivial[i] != other._nontrivial[i]:
                gate, phase = _PRODUCT_MAP[self._nontrivial[i]][other._nontrivial[i]]
                pauli_result[i] = gate
                phase_result *= phase
        for i in other._nontrivial:
            if i not in self._nontrivial:
                pauli_result[i] = other._nontrivial[i]

        # ignore complex global phase
        out_phase = -1 if (phase_result.real < 0 or phase_result.imag < 0) else 1

        # Bypass __init__ via __new__ to avoid serializing the computed dict
        # back into a string just to have __init__ parse it again. The fields
        # below fully define a valid PauliString, so direct assignment is both
        # faster and avoids an O(qubit_count) dense-string round trip.
        out_pauli_string = PauliString.__new__(PauliString)
        out_pauli_string._phase = out_phase
        out_pauli_string._qubit_count = self._qubit_count
        out_pauli_string._nontrivial = pauli_result

        if inplace:
            self._phase = out_pauli_string._phase
            self._qubit_count = out_pauli_string._qubit_count
            self._nontrivial = out_pauli_string._nontrivial
        return out_pauli_string

    def __mul__(
        self, other: PauliString | PauliStringSum | numbers.Real
    ) -> PauliString | PauliStringSum:
        """Right multiplication operator overload using `dot()`.

        Returns the result of multiplying the current circuit by the argument on its right.

        Args:
            other (PauliString): The right multiplicand.

        Returns:
            PauliString: The resultant circuit from right multiplying `self` with `other`.

        Raises:
            ValueError: If the lengths of the Pauli strings being multiplied differ.

        See Also:
            `braket.quantum_information.PauliString.dot()`
        """
        if isinstance(other, numbers.Real):
            return PauliStringSum([(other, self)])
        if isinstance(other, PauliStringSum):
            return other._left_multiply(self)
        return self.dot(other)

    def __rmul__(self, other: numbers.Real | PauliStringSum) -> PauliStringSum:
        if isinstance(other, numbers.Real):
            return PauliStringSum([(other, self)])
        if isinstance(other, PauliStringSum):
            return other * self
        return NotImplemented

    def __add__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        return PauliStringSum([self]) + other

    def __radd__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        return PauliStringSum([other]) + self

    def __sub__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        return PauliStringSum([self]) - other

    def __rsub__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        return PauliStringSum([other]) - self

    def __neg__(self) -> PauliStringSum:
        return PauliStringSum([(-1, self)])

    def __imul__(self, other: PauliString) -> PauliString:
        """Operator overload for right-multiplication assignment (`*=`) using `dot()`.

        Right-multiplies `self` by `other`, and assigns the result to `self`.

        Args:
            other (PauliString): The right multiplicand.

        Returns:
            PauliString: The resultant circuit from right multiplying `self` with `other`.

        Raises:
            ValueError: If the lengths of the Pauli strings being multiplied differ.

        See Also:
            `braket.quantum_information.PauliString.dot()`
        """
        return self.dot(other, inplace=True)

    def power(self, n: int, inplace: bool = False) -> PauliString:
        """Composes Pauli string with itself n times.

        Args:
            n (int): The number of times to self-multiply. Can be any integer value.
            inplace (bool): Update `self` if `True`

        Returns:
            PauliString: If `n` is positive, result from self-multiplication `n` times.
            If zero, identity. If negative, self-multiplication from trivial
            inverse (recall Pauli operators are involutory).

        Raises:
            ValueError: If `n` isn't a plain Python `int`.
        """
        if not isinstance(n, int):
            raise TypeError("Must be raised to integer power")

        # Since pauli ops involutory, result is either identity or unchanged.
        # Bypass __init__ via __new__ to skip the PauliString(self) copy path,
        # which would re-validate fields we already know are consistent. Direct
        # field assignment keeps the hot path allocation-light.
        pauli_other = PauliString.__new__(PauliString)
        pauli_other._qubit_count = self._qubit_count
        if n % 2 == 0:
            pauli_other._phase = 1
            pauli_other._nontrivial = {}
        else:
            pauli_other._phase = self._phase
            pauli_other._nontrivial = dict(self._nontrivial)

        if inplace:
            self._phase = pauli_other._phase
            self._qubit_count = pauli_other._qubit_count
            self._nontrivial = pauli_other._nontrivial
        return pauli_other

    def __pow__(self, n: int) -> PauliString:
        """Pow operator overload for Pauli string composition.

        Syntactic sugar for `power()`.

        Args:
            n (int): The number of times to self-multiply. Can be any integer

        Returns:
            PauliString: If `n` is positive, result from self-multiplication `n` times.
            If zero, identity. If negative, self-multiplication from trivial
            inverse (recall Pauli operators are involutory).

        Raises:
            ValueError: If `n` isn't a plain Python `int`.

        See Also:
            `braket.quantum_information.PauliString.power()`
        """
        return self.power(n)

    def __ipow__(self, n: int) -> PauliString:
        """Operator overload for in-place pow assignment (`**=`) using `power()`.

        Syntactic sugar for in-place `power()`.

        Args:
            n (int): The number of times to self-multiply. Can be any integer

        Returns:
            PauliString: If `n` is positive, result from self-multiplication `n` times.
            If zero, identity. If negative, self-multiplication from trivial
            inverse (recall Pauli operators are involutory).

        Raises:
            ValueError: If `n` isn't a plain Python `int`.

        See Also:
            `braket.quantum_information.PauliString.power()`
        """
        return self.power(n, inplace=True)

    def to_circuit(self) -> Circuit:
        """Returns circuit represented by this `PauliString`.

        Returns:
            Circuit: The circuit for this `PauliString`.
        """
        circ = Circuit()
        for qubit in range(self._qubit_count):
            if qubit not in self._nontrivial:
                circ = circ.i(qubit)
            elif self._nontrivial[qubit] == "X":
                circ = circ.x(qubit)
            elif self._nontrivial[qubit] == "Y":
                circ = circ.y(qubit)
            else:
                circ = circ.z(qubit)
        return circ

    def __eq__(self, other: PauliString):
        if isinstance(other, PauliString):
            return (
                self._phase == other._phase
                and self._nontrivial == other._nontrivial
                and self._qubit_count == other._qubit_count
            )
        return False

    def __hash__(self):
        return hash((self._phase, self._qubit_count, tuple(sorted(self._nontrivial.items()))))

    def __getitem__(self, item: int):
        if item >= self._qubit_count:
            raise IndexError(item)
        return _PAULI_INDICES[self._nontrivial.get(item, "I")]

    def __len__(self):
        return self._qubit_count

    def __repr__(self):
        factors = ["I"] * self._qubit_count
        for i, p in self._nontrivial.items():
            factors[i] = p
        return f"{PauliString._phase_to_str(self._phase)}{''.join(factors)}"

    @staticmethod
    def _split(pauli_word: str) -> tuple[int, str]:
        index = 0
        phase = 1
        if pauli_word[index] in {"+", "-"}:
            phase *= int(f"{pauli_word[index]}1")
            index += 1
        unsigned = pauli_word[index:]
        if not unsigned:
            raise ValueError("Pauli string cannot be empty")
        if set(unsigned) - _PAULI_INDICES.keys():
            raise ValueError(f"{pauli_word} is not a valid Pauli string")
        return phase, unsigned

    @staticmethod
    def _phase_to_str(phase: int) -> str:
        return "+" if phase > 0 else "-"

    def _generate_eigenstate_circuit(self, signs: tuple[int, ...]) -> Circuit:
        circ = Circuit()
        for qubit in range(len(signs)):
            state = signs[qubit] * self[qubit]
            if state == -3:
                circ.x(qubit)
            elif state == 1:
                circ.h(qubit)
            elif state == -1:
                circ.x(qubit).h(qubit)
            elif state == 2:
                circ.h(qubit).s(qubit)
            elif state == -2:
                circ.h(qubit).si(qubit)
        return circ


WeightedPauliString = PauliString | str | tuple[numbers.Real, PauliString | str]


class PauliStringSum:
    """A canonical weighted sum of Pauli strings."""

    def __init__(self, terms: Iterable[WeightedPauliString]):
        """Initializes a `PauliStringSum`.

        Args:
            terms (Iterable[WeightedPauliString]): Terms specified as Pauli strings, string
                representations, or `(coefficient, pauli_string)` tuples.
        """
        self._terms: dict[PauliString, float] = {}
        for term in terms:
            coefficient, pauli_string = self._parse_term(term)
            self._add_term(coefficient, pauli_string)

    @classmethod
    def from_list(cls, terms: Sequence[tuple[numbers.Real, str | PauliString]]) -> PauliStringSum:
        """Builds a `PauliStringSum` from `(coefficient, pauli_string)` tuples."""
        return cls(terms)

    @classmethod
    def from_sum(cls, observable_sum: Sum) -> PauliStringSum:
        """Builds a `PauliStringSum` from a Braket `Observable.Sum`.

        Args:
            observable_sum (Sum): A sum containing only Pauli observables.

        Returns:
            PauliStringSum: The corresponding weighted Pauli-string sum.

        Raises:
            TypeError: If the observable contains non-Pauli terms.
        """
        if not isinstance(observable_sum, Sum):
            raise TypeError("observable_sum must be an Observable.Sum")
        return cls(cls._observable_to_term(observable) for observable in observable_sum.summands)

    @property
    def terms(self) -> tuple[tuple[float, PauliString], ...]:
        """tuple[tuple[float, PauliString], ...]: The canonical nonzero terms."""
        return tuple(
            (coefficient, PauliString(pauli)) for pauli, coefficient in self._terms.items()
        )

    def to_list(self) -> list[tuple[float, str]]:
        """Returns the terms as `(coefficient, pauli_string)` tuples."""
        return [(coefficient, str(pauli)) for coefficient, pauli in self]

    def to_sum(self) -> Sum:
        """Converts this Pauli string sum into an `Observable.Sum`.

        Raises:
            ValueError: If the sum has no nonzero terms.
        """
        if not self._terms:
            raise ValueError("Cannot convert an empty PauliStringSum to Observable.Sum")
        observables = [
            coefficient * pauli.to_unsigned_observable(include_trivial=True)
            for coefficient, pauli in self
        ]
        return Sum(observables)

    def commutes_with(self, other: PauliString | PauliStringSum) -> bool:
        """Returns whether every term in this sum commutes with every term in `other`."""
        other_sum = self._coerce_to_sum(other)
        return all(
            self._pauli_strings_commute(left, right)
            for left in self._terms
            for right in other_sum._terms
        )

    @property
    def is_self_commuting(self) -> bool:
        """bool: Whether all terms in this sum pairwise commute."""
        terms = tuple(self._terms)
        return all(
            self._pauli_strings_commute(terms[i], terms[j])
            for i in range(len(terms))
            for j in range(i + 1, len(terms))
        )

    def __iter__(self) -> Iterator[tuple[float, PauliString]]:
        for pauli, coefficient in self._terms.items():
            yield coefficient, PauliString(pauli)

    def __len__(self) -> int:
        return len(self._terms)

    def __contains__(self, item: PauliString | str) -> bool:
        return self._canonical_pauli(PauliString(item)) in self._terms

    def __getitem__(self, item: int | PauliString | str) -> tuple[float, PauliString] | float:
        if isinstance(item, int):
            return self.terms[item]
        pauli = PauliString(item)
        return pauli.phase * self._terms.get(self._canonical_pauli(pauli), 0.0)

    def __add__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        result = PauliStringSum(self.terms)
        for coefficient, pauli in self._coerce_to_sum(other):
            result._add_term(coefficient, pauli)
        return result

    def __radd__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        return self + other

    def __sub__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        return self + (-self._coerce_to_sum(other))

    def __rsub__(self, other: PauliString | PauliStringSum) -> PauliStringSum:
        return self._coerce_to_sum(other) - self

    def __neg__(self) -> PauliStringSum:
        return PauliStringSum([(-coefficient, pauli) for coefficient, pauli in self])

    def __mul__(
        self,
        other: numbers.Real | PauliString | PauliStringSum,
    ) -> PauliStringSum:
        if isinstance(other, numbers.Real):
            return PauliStringSum([(coefficient * other, pauli) for coefficient, pauli in self])
        if isinstance(other, PauliString):
            return PauliStringSum([(coefficient, pauli * other) for coefficient, pauli in self])
        if isinstance(other, PauliStringSum):
            return PauliStringSum([
                (left_coefficient * right_coefficient, left_pauli * right_pauli)
                for left_coefficient, left_pauli in self
                for right_coefficient, right_pauli in other
            ])
        return NotImplemented

    def __rmul__(
        self,
        other: numbers.Real | PauliString,
    ) -> PauliStringSum:
        if isinstance(other, numbers.Real):
            return self * other
        if isinstance(other, PauliString):
            return self._left_multiply(other)
        return NotImplemented

    def __eq__(self, other: PauliStringSum) -> bool:
        if isinstance(other, PauliStringSum):
            return self._terms == other._terms
        return False

    def __repr__(self) -> str:
        return f"PauliStringSum({self.to_list()})"

    def _left_multiply(self, left: PauliString) -> PauliStringSum:
        return PauliStringSum([(coefficient, left * pauli) for coefficient, pauli in self])

    def _add_term(self, coefficient: numbers.Real, pauli_string: PauliString) -> None:
        if not isinstance(coefficient, numbers.Real):
            raise TypeError("PauliStringSum coefficients must be real numbers")
        canonical_pauli = self._canonical_pauli(pauli_string)
        signed_coefficient = float(coefficient * pauli_string.phase)
        if signed_coefficient == 0:
            return
        new_coefficient = self._terms.get(canonical_pauli, 0.0) + signed_coefficient
        if new_coefficient == 0:
            self._terms.pop(canonical_pauli, None)
        else:
            self._terms[canonical_pauli] = new_coefficient

    @staticmethod
    def _parse_term(term: WeightedPauliString) -> tuple[numbers.Real, PauliString]:
        if isinstance(term, tuple):
            if len(term) != 2:
                raise ValueError("Weighted terms must be (coefficient, pauli_string) tuples")
            coefficient, pauli_string = term
            return coefficient, PauliString(pauli_string)
        return 1, PauliString(term)

    @staticmethod
    def _canonical_pauli(pauli_string: PauliString) -> PauliString:
        canonical = PauliString.__new__(PauliString)
        canonical._phase = 1
        canonical._qubit_count = pauli_string.qubit_count
        canonical._nontrivial = dict(pauli_string._nontrivial)
        return canonical

    @staticmethod
    def _coerce_to_sum(other: PauliString | PauliStringSum) -> PauliStringSum:
        if isinstance(other, PauliStringSum):
            return other
        if isinstance(other, PauliString):
            return PauliStringSum([other])
        return PauliStringSum([other])

    @staticmethod
    def _pauli_strings_commute(left: PauliString, right: PauliString) -> bool:
        if left.qubit_count != right.qubit_count:
            raise ValueError(
                f"Input Pauli string must be of length ({left.qubit_count}), "
                f"not {right.qubit_count}"
            )
        return left * right == right * left

    @staticmethod
    def _observable_to_term(observable: Observable) -> tuple[float, PauliString]:
        coefficient = float(observable.coefficient)
        if isinstance(observable, TensorProduct):
            pauli_string = PauliStringSum._tensor_product_to_pauli(observable)
        else:
            pauli_string = PauliStringSum._single_observable_to_pauli(observable)
        return coefficient, pauli_string

    @staticmethod
    def _tensor_product_to_pauli(observable: TensorProduct) -> PauliString:
        if observable.targets:
            factors = ["I"] * (max(observable.targets) + 1)
            targets = iter(observable.targets)
            for factor in observable.factors:
                if factor.qubit_count != 1:
                    raise TypeError("Only single-qubit Pauli factors are supported")
                factors[next(targets)] = PauliStringSum._observable_symbol(factor)
            return PauliString("".join(factors))
        return PauliString(
            "".join(PauliStringSum._observable_symbol(f) for f in observable.factors)
        )

    @staticmethod
    def _single_observable_to_pauli(observable: Observable) -> PauliString:
        symbol = PauliStringSum._observable_symbol(observable)
        if observable.targets:
            factors = ["I"] * (max(observable.targets) + 1)
            factors[next(iter(observable.targets))] = symbol
            return PauliString("".join(factors))
        return PauliString(symbol)

    @staticmethod
    def _observable_symbol(observable: Observable) -> str:
        if observable.qubit_count != 1:
            raise TypeError("Only Pauli observables are supported")
        symbol = observable.ascii_symbols[0]
        if symbol not in _PAULI_INDICES:
            raise TypeError("Only Pauli observables are supported")
        return symbol
