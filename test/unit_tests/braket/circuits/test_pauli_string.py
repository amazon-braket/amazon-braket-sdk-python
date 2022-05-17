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
from braket.circuits.observables import X, Y, Z

ORDER = ["I", "X", "Y", "Z"]
PAULI_INDEX_MATRICES = {
    0: gates.I().to_matrix(),
    1: gates.X().to_matrix(),
    2: gates.Y().to_matrix(),
    3: gates.Z().to_matrix(),
}
SIGN_MAP = {"+": 1, "-": -1}


@pytest.mark.parametrize(
    "pauli_string, string, phase, observable",
    [
        ("+XZ", "+XZ", 1, X() @ Z()),
        ("-ZXY", "-ZXY", -1, Z() @ X() @ Y()),
        ("YIX", "+YIX", 1, Y() @ X()),
        (PauliString("-ZYXI"), "-ZYXI", -1, Z() @ Y() @ X()),
    ],
)
def test_happy_case(pauli_string, string, phase, observable):
    instance = PauliString(pauli_string)
    assert str(instance) == string
    assert instance.phase == phase
    pauli_list = list(str(pauli_string))
    if pauli_list[0] in {"-", "+"}:
        pauli_list.pop(0)
    stripped = "".join(pauli_list)
    assert len(instance) == len(stripped)
    for i in range(len(instance)):
        assert ORDER[instance[i]] == stripped[i]
    assert instance == PauliString(pauli_string)
    assert instance == PauliString(instance)
    assert instance.to_unsigned_observable() == observable


@pytest.mark.parametrize("other", ["foo", PauliString("+XYZ"), PauliString("-XI")])
def test_not_equal(other):
    assert PauliString("-XYZ") != other


@pytest.mark.xfail(raises=ValueError)
def test_none():
    PauliString(None)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("invalid_string", ["XAY", "-BYZ", "+", "-", "xyz", "", None])
def test_invalid_string(invalid_string):
    PauliString(invalid_string)


@pytest.mark.xfail(raises=TypeError)
def test_invalid_type():
    PauliString(1234)


@pytest.mark.parametrize(
    "string,signs",
    list(itertools.product(["X", "Y", "Z"], ["+", "-"]))
    + [("ZIY", "+--"), ("YIXIZ", [1, 1, -1, -1, 1]), ("XYZ", (-1, -1, -1)), ("XZIY", None)],
)
def test_eigenstate(string, signs):
    pauli_string = PauliString(string)
    circuit = pauli_string.eigenstate(signs)
    for qubit in range(len(string)):
        circuit.i(qubit)
    initial_state = np.zeros(2 ** len(pauli_string))
    initial_state[0] = 1
    state = circuit.to_unitary() @ initial_state

    if not signs:
        signs = [1] * len(string)
    signs_list = [SIGN_MAP[sign] for sign in signs] if isinstance(signs, str) else signs
    positive = [signs_list[i] for i in range(len(string)) if signs_list[i] < 0 and string[i] != "I"]
    total_sign = 1 if len(positive) % 2 == 0 else -1
    pauli_matrix = functools.reduce(
        np.kron, [PAULI_INDEX_MATRICES[pauli] for pauli in pauli_string]
    )
    actual = total_sign * pauli_matrix @ state
    assert np.allclose(actual, state)
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
