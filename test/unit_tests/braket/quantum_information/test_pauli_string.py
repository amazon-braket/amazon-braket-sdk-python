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
import math

import numpy as np
import pytest

from braket.circuits import gates
from braket.circuits.circuit import Circuit
from braket.circuits.observables import I, X, Y, Z
from braket.quantum_information import PauliString, PauliStringSum

ORDER = ["I", "X", "Y", "Z"]
PAULI_INDEX_MATRICES = {
    0: gates.I().to_matrix(),
    1: gates.X().to_matrix(),
    2: gates.Y().to_matrix(),
    3: gates.Z().to_matrix(),
}
SIGN_MAP = {"+": 1, "-": -1}


@pytest.mark.parametrize(
    "pauli_string, string, phase, observable, obs_with_id",
    [
        ("+XZ", "+XZ", 1, X() @ Z(), X() @ Z()),
        ("-ZXY", "-ZXY", -1, Z() @ X() @ Y(), Z() @ X() @ Y()),
        ("YIX", "+YIX", 1, Y() @ X(), Y() @ I() @ X()),
        (PauliString("-ZYXI"), "-ZYXI", -1, Z() @ Y() @ X(), Z() @ Y() @ X() @ I()),
        ("IIXIIIYI", "+IIXIIIYI", 1, X() @ Y(), I() @ I() @ X() @ I() @ I() @ I() @ Y() @ I()),
    ],
)
def test_happy_case(pauli_string, string, phase, observable, obs_with_id):
    instance = PauliString(pauli_string)
    assert str(instance) == string
    assert instance.phase == phase
    pauli_list = list(str(pauli_string))
    if pauli_list[0] in {"-", "+"}:
        pauli_list.pop(0)
    stripped = "".join(pauli_list)
    assert len(instance) == len(stripped)
    assert len(instance) == instance.qubit_count
    for i in range(len(instance)):
        assert ORDER[instance[i]] == stripped[i]
    assert instance == PauliString(pauli_string)
    assert instance == PauliString(instance)
    assert instance.to_unsigned_observable() == observable
    assert instance.to_unsigned_observable(include_trivial=True) == obs_with_id


@pytest.mark.parametrize(
    "other", ["foo", PauliString("+XYZ"), PauliString("-XI"), PauliString("-XYZI")]
)
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


@pytest.mark.xfail(raises=IndexError)
@pytest.mark.parametrize("string", ["XZY", "-YIIXZ", "+IXIYIZ"])
def test_index_out_of_bounds(string):
    PauliString(string)[len(string)]


@pytest.mark.parametrize(
    "string,weight",
    # Make phase explicit for test simplicity
    list(itertools.product(["-ZYX", "-IXIIXYZ", "+ZXYXY"], [1, 2, 3])),
)
def test_weight_n_substrings(string, weight):
    pauli_string = PauliString(string)
    qubit_count = pauli_string.qubit_count
    nontrivial = [qubit for qubit in range(qubit_count) if pauli_string[qubit]]
    substrings = []
    for indices in itertools.combinations(nontrivial, weight):
        factors = [string[qubit + 1] if qubit in indices else "I" for qubit in range(qubit_count)]
        substrings.append(PauliString(f"{string[0]}{''.join(factors)}"))
    actual = pauli_string.weight_n_substrings(weight)
    assert actual == tuple(substrings)
    assert len(actual) == math.comb(len(nontrivial), weight)


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


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("sign", ["+ab", "--+-", [+2, -1, -1], (-1, 1j, 1)])
def test_eigenstate_invalid_signs(sign):
    PauliString("XYZ").eigenstate(sign)


@pytest.mark.parametrize(
    "circ_arg_1, circ_arg_2, circ_res",
    [
        ("III", "+III", "III"),
        ("Z", "I", "Z"),
        ("I", "-Y", "-Y"),
        ("XYXZY", "+XYXZY", "IIIII"),
        ("XYZ", "ZYX", "YIY"),
        ("YZ", "ZX", "-XY"),
        ("-Z", "Y", "X"),
        ("Z", "Y", "-X"),
    ],
)
def test_dot(circ_arg_1, circ_arg_2, circ_res):
    circ1 = PauliString(circ_arg_1)
    circ2 = circ1.dot(PauliString(circ_arg_2))
    assert circ2 == PauliString(circ_res)
    assert circ1 == circ1

    # Test in-place computation
    circ1 = PauliString(circ_arg_1)
    circ1.dot(PauliString(circ_arg_2), inplace=True)
    assert circ1 == PauliString(circ_res)

    # Test operator overloads
    circ1 = PauliString(circ_arg_1)
    circ2 = PauliString(circ_arg_2)
    assert circ1 * circ2 == PauliString(circ_res)
    circ1 *= circ2
    assert circ1 == PauliString(circ_res)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize(
    "circ1, circ2, operation",
    [
        (PauliString("III"), PauliString("II"), "dot()"),
        (PauliString("III"), PauliString("II"), "*"),
        (PauliString("III"), PauliString("II"), "*="),
        (PauliString("IXI"), PauliString("II"), "dot()"),
        (PauliString("IXI"), PauliString("II"), "*"),
        (PauliString("IXI"), PauliString("II"), "*="),
    ],
)
def test_dot_unequal_lengths(circ1, circ2, operation):
    if operation == "dot()":
        circ1.dot(circ2)
    elif operation == "*":
        circ1 * circ2
    elif operation == "*=":
        circ1 *= circ2


@pytest.mark.parametrize(
    "circ, n, circ_res",
    [
        ("-X", 1, "-X"),
        ("Y", 2, "I"),
        ("Y", -2, "I"),
        ("-X", 3, "-X"),
        ("XYZ", 5, "XYZ"),
        ("XYZ", -5, "XYZ"),
        ("XYZ", 6, "III"),
        ("XYZ", 1, "XYZ"),
        ("-YX", 0, "II"),
        ("Y", 0, "I"),
    ],
)
def test_power(circ, n, circ_res):
    circ1 = PauliString(circ)
    circ2 = circ1.power(n)
    assert circ2 == PauliString(circ_res)
    assert circ1 == PauliString(circ)

    # Test in-place computation
    circ1.power(n, inplace=True)
    assert circ1 == PauliString(circ_res)

    # Test operator overloads
    circ1 = PauliString(circ)
    assert (circ1**n) == PauliString(circ_res)
    circ1 **= n
    assert circ1 == PauliString(circ_res)


@pytest.mark.xfail(raises=TypeError)
@pytest.mark.parametrize(
    "circ, n, operation",
    [
        (PauliString("XYZ"), "-1.2", "power()"),
        (PauliString("XYZ"), "-1.2", "**"),
        (PauliString("XYZ"), "-1.2", "**="),
        (PauliString("ZYX"), "1.2", "power()"),
        (PauliString("ZYX"), "1.2", "**"),
        (PauliString("ZYX"), "1.2", "**="),
        (PauliString("I"), "3j", "power()"),
        (PauliString("I"), "3j", "**"),
        (PauliString("I"), "3j", "**="),
    ],
)
def test_power_invalid_exp(circ, n, operation):
    if operation == "power()":
        circ.power(n)
    elif operation == "**":
        circ**n
    elif operation == "**=":
        circ **= n


@pytest.mark.parametrize(
    "circ, circ_res",
    [
        (PauliString("I"), Circuit().i(0)),
        (PauliString("-X"), Circuit().x(0)),
        (PauliString("IYX"), Circuit().i(0).y(1).x(2)),
        (PauliString("ZIIIX"), Circuit().z(0).i(1).i(2).i(3).x(4)),
    ],
)
def test_to_circuit(circ, circ_res):
    assert circ.to_circuit() == circ_res


def test_pauli_string_sum_from_terms_combines_like_terms():
    pauli_sum = PauliStringSum.from_terms([(1.5, "XI"), (2, "-XI"), (3, "IZ")])

    assert pauli_sum.qubit_count == 2
    assert pauli_sum.to_terms() == [(-0.5, "+XI"), (3.0, "+IZ")]


def test_pauli_string_sum_add_subtract_and_scalar_multiply():
    first = PauliString("XI")
    second = PauliString("IZ")

    pauli_sum = 2 * first + second - PauliString("-XI")

    assert isinstance(pauli_sum, PauliStringSum)
    assert pauli_sum.to_terms() == [(3.0, "+XI"), (1.0, "+IZ")]
    assert (0.5 * pauli_sum).to_terms() == [(1.5, "+XI"), (0.5, "+IZ")]
    assert (-pauli_sum).to_terms() == [(-3.0, "+XI"), (-1.0, "+IZ")]


def test_pauli_string_sum_multiplies_by_pauli_string_on_right_and_left():
    pauli_sum = PauliStringSum.from_terms([(2, "XI"), (3, "IZ")])

    assert (pauli_sum * PauliString("ZI")).to_terms() == [(-2.0, "+YI"), (3.0, "+ZZ")]
    assert (PauliString("ZI") * pauli_sum).to_terms() == [(2.0, "+YI"), (3.0, "+ZZ")]


def test_pauli_string_sum_index_and_contains():
    pauli_sum = PauliStringSum.from_terms([(2, "-XI"), (3, "IZ")])

    assert PauliString("XI") in pauli_sum
    assert PauliString("-XI") in pauli_sum
    assert pauli_sum[0] == (-2.0, PauliString("XI"))
    assert len(pauli_sum) == 2
    assert list(pauli_sum) == list(pauli_sum.terms)
    assert repr(pauli_sum) == "PauliStringSum([(-2.0, '+XI'), (3.0, '+IZ')])"


def test_pauli_string_sum_empty_copy_and_cancellation():
    empty = PauliStringSum()
    assert empty.qubit_count is None
    assert empty.to_terms() == []

    original = PauliStringSum(PauliString("XI"))
    copied = PauliStringSum(original)
    assert copied == original
    assert copied != PauliStringSum(PauliString("IZ"))
    assert copied != PauliString("XI")

    cancelled = original + PauliString("-XI")
    assert cancelled.to_terms() == []
    assert cancelled.qubit_count is None


def test_pauli_string_and_sum_reverse_arithmetic():
    first = PauliString("XI")
    second = PauliString("IZ")
    pauli_sum = PauliStringSum.from_terms([(2, "XI"), (3, "IZ")])

    assert (first + pauli_sum).to_terms() == [(3.0, "+XI"), (3.0, "+IZ")]
    assert (pauli_sum + first).to_terms() == [(3.0, "+XI"), (3.0, "+IZ")]
    assert (first - pauli_sum).to_terms() == [(-1.0, "+XI"), (-3.0, "+IZ")]
    assert (pauli_sum - first).to_terms() == [(1.0, "+XI"), (3.0, "+IZ")]
    assert (second - pauli_sum).to_terms() == [(-2.0, "+IZ"), (-2.0, "+XI")]


def test_pauli_string_sum_unsupported_operands_return_not_implemented():
    pauli_string = PauliString("X")
    pauli_sum = PauliStringSum(pauli_string)
    unsupported = object()

    assert pauli_string.__rmul__(unsupported) is NotImplemented
    assert pauli_sum.__add__(unsupported) is NotImplemented
    assert pauli_sum.__mul__(unsupported) is NotImplemented
    assert pauli_sum.__rmul__(unsupported) is NotImplemented


@pytest.mark.xfail(raises=ValueError)
def test_pauli_string_sum_rejects_unequal_lengths():
    PauliStringSum.from_terms([(1, "XI"), (1, "Z")])


@pytest.mark.xfail(raises=TypeError)
def test_pauli_string_sum_rejects_non_real_coefficients():
    PauliStringSum.from_terms([(1j, "X")])
