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

import functools
import itertools

import numpy as np
import pytest

from braket.circuits import Circuit, PauliString, gates

ORDER = ["I", "X", "Y", "Z"]
PAULI_INDEX_MATRICES = {
    0: gates.I().to_matrix(),
    1: gates.X().to_matrix(),
    2: gates.Y().to_matrix(),
    3: gates.Z().to_matrix(),
}
SIGN_MAP = {"+": 1, "-": -1}


@pytest.mark.parametrize(
    "pauli_string, string, phase",
    [
        ("+XYZ", "+XYZ", complex(1)),
        ("-ZXY", "-ZXY", complex(-1)),
        ("YIX", "+YIX", complex(1)),
        ("+iZYXI", "+iZYXI", complex(1j)),
        ("-iXIZY", "-iXIZY", complex(-1j)),
        ("iYXIZ", "+iYXIZ", complex(1j)),
        (PauliString("-iYX"), "-iYX", complex(-1j)),
        (PauliString("ZYXI"), "+ZYXI", complex(1)),
    ],
)
def test_happy_case(pauli_string, string, phase):
    instance = PauliString(pauli_string)
    assert str(instance) == string
    assert instance.phase == phase
    pauli_list = list(str(pauli_string))
    if pauli_list[0] in {"-", "+"}:
        pauli_list.pop(0)
    if pauli_list[0] in {"i", "j"}:
        pauli_list.pop(0)
    stripped = "".join(pauli_list)
    assert len(instance) == len(stripped)
    for i in range(len(instance)):
        assert ORDER[instance[i]] == stripped[i]


@pytest.mark.xfail(raises=ValueError)
def test_none():
    PauliString(None)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("invalid_string", ["XAY", "-BYZ", "+", "-i", "j", "xyz", "", None])
def test_invalid_string(invalid_string):
    PauliString(invalid_string)


@pytest.mark.xfail(raises=TypeError)
def test_invalid_type():
    PauliString(1234)


@pytest.mark.parametrize("string,signs", list(itertools.product(["X", "Y", "Z"], ["+", "-"])))
def test_eigenstate(string, signs):
    pauli_string = PauliString(string)
    circuit = pauli_string.eigenstate(signs)
    for qubit in range(len(signs)):
        circuit.i(qubit)
    initial_state = np.zeros(2 ** len(pauli_string))
    initial_state[0] = 1
    state = circuit.as_unitary() @ initial_state
    signs_list = [SIGN_MAP[sign] for sign in signs] if isinstance(signs, str) else signs
    total_sign = 1 if len([1 for sign in signs_list if sign < 0]) % 2 == 0 else -1
    pauli_matrix = functools.reduce(
        np.kron, [PAULI_INDEX_MATRICES[pauli] for pauli in pauli_string]
    )
    actual = total_sign * pauli_matrix @ state
    assert np.isclose(actual, state).all()
    assert tuple(signs_list) in pauli_string._eigenstate_circuits


def test_cached_eigenstate_used():
    pauli_string = PauliString("XYZ")
    sign = (+1, -1, -1)
    circuit = Circuit()
    pauli_string._eigenstate_circuits[sign] = circuit
    assert pauli_string.eigenstate(sign) == circuit


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("sign", ["+ab", "--+-", [+2, -1, -1], (-1, 1j, 1)])
def test_eigenstate_invalid_signs(sign):
    PauliString("XYZ").eigenstate(sign)
