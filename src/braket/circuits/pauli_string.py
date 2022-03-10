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

from typing import List, Tuple, Union

from braket.circuits import Circuit

_IDENTITY = "I"
_PAULI_X = "X"
_PAULI_Y = "Y"
_PAULI_Z = "Z"
_PAULI_INDICES = {_IDENTITY: 0, _PAULI_X: 1, _PAULI_Y: 2, _PAULI_Z: 3}
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
                specified by an optional sign +/- and optional imaginary unit (both i and j are
                acceptable) followed by an uppercase string in {I, X, Y, Z}. Example valid strings
                are: XYZ, +YIZY, -YX, iXXY, -jZYX
        """
        if not pauli_string:
            raise ValueError("pauli_string must not be empty")
        if isinstance(pauli_string, PauliString):
            self._phase = pauli_string._phase
            self._str = pauli_string._str
            self._indices = pauli_string._indices
            self._eigenstate_circuits = pauli_string._eigenstate_circuits
        elif isinstance(pauli_string, str):
            self._phase, factors_str = PauliString._split(pauli_string)
            self._str = f"{PauliString._phase_to_str(self._phase)}{factors_str}"
            self._indices = [_PAULI_INDICES[letter] for letter in factors_str]
            self._eigenstate_circuits = {}
        else:
            raise TypeError(f"Pauli word {pauli_string} must be of type {PauliString} or {str}")

    @property
    def phase(self) -> complex:
        """int: The phase of the Pauli string.

        Can be one of {1, -1, 1j, -1j}
        """
        return self._phase

    def eigenstate(self, signs: Union[str, List[int], Tuple[int, ...]]) -> Circuit:
        """Returns the eigenstate of this Pauli string with the given factor signs.

        The resulting eigenstate has each qubit in the +1 eigenstate of its corresponding signed
        Pauli operator. For example, a Pauli string +iXYZ and signs ++- has factors +X, +Y and -Z,
        with the corresponding qubits in states |+⟩, |i⟩ and |1⟩ respectively (the global phase of
        the Pauli string is ignored).

        Args:
            signs (Union[str, List[int], Tuple[int, ...]]): The sign of each factor of the
                eigenstate, specified either as a string of "+" and "_", or as a list or tuple of
                +/-1. The length of signs must be equal to the length of the Pauli string.

        Returns:
            Circuit: A circuit that prepares the desired eigenstate of the Pauli string.

        Raises:
            ValueError: If the length of signs is not equal to that of the Pauli string or the signs
                are invalid.
        """
        if len(signs) != len(self._indices):
            raise ValueError(
                f"signs must be the same length of the Pauli string ({len(self._indices)}), "
                f"but was {len(signs)}"
            )
        if isinstance(signs, str) and not set(signs) <= set(_SIGN_MAP.keys()):
            raise ValueError(f"signs must be +/-1, got {signs}")
        signs_tup = (
            tuple(_SIGN_MAP[sign] for sign in signs) if isinstance(signs, str) else tuple(signs)
        )
        if not set(signs_tup) <= {1, -1}:
            raise ValueError(f"signs must be +/-1, got {signs}")
        if signs_tup in self._eigenstate_circuits:
            return self._eigenstate_circuits[signs_tup]
        circuit = self._generate_eigenstate_circuit(signs_tup)
        self._eigenstate_circuits[signs_tup] = circuit
        return circuit

    def __getitem__(self, item):
        return self._indices[item]

    def __len__(self):
        return len(self._indices)

    def __repr__(self):
        return self._str

    @staticmethod
    def _split(pauli_word: str) -> Tuple[complex, str]:
        index = 0
        phase = 1
        if pauli_word[index] in {"+", "-"}:
            if not pauli_word[1:]:
                raise ValueError("Pauli string cannot be empty")
            phase *= int(f"{pauli_word[index]}1")
            index += 1
        if pauli_word[index] in {"i", "j"}:
            phase *= 1j
            index += 1
        unsigned = pauli_word[index:]
        if not unsigned:
            raise ValueError("Pauli string cannot be empty")
        if set(unsigned) - _PAULI_INDICES.keys():
            raise ValueError(f"{pauli_word} is not a valid Pauli string")
        return complex(phase), unsigned

    @staticmethod
    def _phase_to_str(phase: complex) -> str:
        if phase.real:
            return "+" if phase.real > 0 else "-"
        return "+i" if phase.imag > 0 else "-i"

    def _generate_eigenstate_circuit(self, signs: Tuple[int, ...]) -> Circuit:
        circ = Circuit()
        for qubit in range(len(signs)):
            state = signs[qubit] * self._indices[qubit]
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
