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
from typing import List, Optional, Tuple, Union

from braket.circuits.circuit import Circuit
from braket.circuits.observables import TensorProduct, X, Y, Z

_IDENTITY = "I"
_PAULI_X = "X"
_PAULI_Y = "Y"
_PAULI_Z = "Z"
_PAULI_INDICES = {_IDENTITY: 0, _PAULI_X: 1, _PAULI_Y: 2, _PAULI_Z: 3}
_PAULI_OBSERVABLES = {_PAULI_X: X(), _PAULI_Y: Y(), _PAULI_Z: Z()}
_SIGN_MAP = {"+": 1, "-": -1}


class PauliString:
    """
    A lightweight representation of a Pauli string with its phase.
    """

    def __init__(self, pauli_string: Union[str, PauliString]):
        """
        Args:
            pauli_string (Union[str, PauliString]): The representation of the pauli word, either a
                string or another PauliString object. A valid string consists of an optional phase,
                specified by an optional sign +/- followed by an uppercase string in {I, X, Y, Z}.
                Example valid strings are: XYZ, +YIZY, -YX
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

    def to_unsigned_observable(self) -> TensorProduct:
        """Returns the observable corresponding to the unsigned part of the Pauli string.

        For example, for a Pauli string -XYZ, the corresponding observable is X ⊗ Y ⊗ Z.

        Returns:
            TensorProduct: The tensor product of the unsigned factors in the Pauli string.
        """
        return TensorProduct(
            [_PAULI_OBSERVABLES[self._nontrivial[qubit]] for qubit in sorted(self._nontrivial)]
        )

    def weight_n_substrings(self, weight: int) -> Tuple[PauliString, ...]:
        r"""Returns every substring of this Pauli string with exactly `weight` nontrivial factors.

        The number of substrings is equal to :math:`\binom{n}{w}`, where :math`n` is the number of
        nontrivial (non-identity) factors in the Pauli string and :math`w` is `weight`.

        Args:
            weight (int): The number of non-identity factors in the substrings.

        Returns:
            Tuple[PauliString, ...]: A tuple of weight-n Pauli substrings.
        """
        substrings = []
        for indices in itertools.combinations(self._nontrivial, weight):
            factors = [
                self._nontrivial[qubit]
                if qubit in set(indices).intersection(self._nontrivial)
                else "I"
                for qubit in range(self._qubit_count)
            ]
            substrings.append(
                PauliString(f"{PauliString._phase_to_str(self._phase)}{''.join(factors)}")
            )
        return tuple(substrings)

    def eigenstate(self, signs: Optional[Union[str, List[int], Tuple[int, ...]]] = None) -> Circuit:
        """Returns the eigenstate of this Pauli string with the given factor signs.

        The resulting eigenstate has each qubit in the +1 eigenstate of its corresponding signed
        Pauli operator. For example, a Pauli string +XYZ and signs ++- has factors +X, +Y and -Z,
        with the corresponding qubits in states |+⟩, |i⟩ and |1⟩ respectively (the global phase of
        the Pauli string is ignored).

        Args:
            signs (Union[str, List[int], Tuple[int, ...]], optional): The sign of each factor of the
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

    def __eq__(self, other):
        if isinstance(other, PauliString):
            return (
                self._phase == other._phase
                and self._nontrivial == other._nontrivial
                and self._qubit_count == other._qubit_count
            )
        return False

    def __getitem__(self, item):
        if item >= self._qubit_count:
            raise IndexError(item)
        return _PAULI_INDICES[self._nontrivial.get(item, "I")]

    def __len__(self):
        return self._qubit_count

    def __repr__(self):
        factors = [
            self._nontrivial[qubit] if qubit in self._nontrivial else "I"
            for qubit in range(self._qubit_count)
        ]
        return f"{PauliString._phase_to_str(self._phase)}{''.join(factors)}"

    @staticmethod
    def _split(pauli_word: str) -> Tuple[int, str]:
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

    def _generate_eigenstate_circuit(self, signs: Tuple[int, ...]) -> Circuit:
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
