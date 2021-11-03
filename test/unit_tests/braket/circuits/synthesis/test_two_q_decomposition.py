# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import io
import sys
import numpy as np
from scipy.linalg import expm
import pytest

from braket.circuits.qubit_set import QubitSet
import braket.circuits.quantum_operator_helpers as predicates
import braket.circuits.synthesis.two_qubit_decomposition as kak
from braket.circuits.gates import X, Y, Z, H, S, CNot, CZ

x = X().to_matrix()
y = Y().to_matrix()
z = Z().to_matrix()
h = H().to_matrix()
s = S().to_matrix()
cnot = CNot().to_matrix()
cz = CZ().to_matrix()

I = np.array([[1, 0], [0, 1]], dtype=np.complex128)  # noqa E741

iswap_d = np.array(
    [[1, 0, 0, 0], [0, 0, -1j, 0], [0, -1j, 0, 0], [0, 0, 0, 1]], dtype=np.complex128
)

unentangled_2q = np.array([[1, 0, 0, 0], [0, 1j, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1j]])

half_cz = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1j]])

cnot = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=np.complex128)

cnot_re = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=np.complex128)

swap = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=np.complex128)

ry30 = np.array(
    [[np.cos(np.pi / 12), -np.sin(np.pi / 12)], [np.sin(np.pi / 12), np.cos(np.pi / 12)]],
    dtype=np.complex128,
)

rx30 = np.array(
    [[np.cos(np.pi / 12), -1j * np.sin(np.pi / 12)], [-1j * np.sin(np.pi / 12), np.cos(np.pi / 12)]]
)


def u(a, b, c):
    return np.array(
        [
            [np.cos(0.5 * a), -np.exp(1j * c) * np.sin(0.5 * a)],
            [np.sin(0.5 * a) * np.exp(1j * b), np.cos(0.5 * a) * np.exp(1j * (b + c))],
        ],
        dtype=np.complex128,
    )


product_gate_test = [
    np.kron(u(0.14, 0.52, -2.14), u(0.24, 0.05, 1.0)),
    np.kron(u(1.83, 2.18, 0.88), u(0.33, -1.35, 3.14)),
    np.kron(u(-0.14, 3.02, -1.55), u(0.61, 1.89, 0.99)),
    np.kron(u(6.14, 2.02, 3.55), u(-4.61, -2.89, 2.99)),
]

one_cnot_test = [p1 @ cnot @ p2 for p1 in product_gate_test for p2 in product_gate_test]

two_cnot_test = [
    p1 @ cnot @ p2 @ cnot @ p3
    for p1 in product_gate_test
    for p2 in product_gate_test
    for p3 in product_gate_test
]

three_cnot_test = [
    p1 @ cnot @ p2 @ cnot_re @ p3 @ cnot @ p4
    for p1 in product_gate_test
    for p2 in product_gate_test
    for p3 in product_gate_test
    for p4 in product_gate_test
]

# Test decompose_one_qubit_product


@pytest.mark.parametrize(
    "unitary_test_cases",
    [np.kron(x, z), np.kron(x, y), np.kron(y, z), np.kron(x, I), np.kron(h, x)] + product_gate_test,
)
def test_decompose_one_qubit_product(unitary_test_cases):
    phase, u1, u2 = kak.decompose_one_qubit_product(unitary_test_cases)
    assert np.allclose(phase * np.kron(u1, u2), unitary_test_cases)


@pytest.mark.parametrize(
    "unitary_test_cases", [1, 0.5, "random_matrix", cnot, cz, cnot_re, iswap_d]
)
@pytest.mark.xfail
def test_decompose_one_qubit_product_edge_cases(unitary_test_cases):
    phase, u1, u2 = kak.decompose_one_qubit_product(unitary_test_cases)


# Test odo_decomposition.


@pytest.mark.parametrize(
    "unitary_test_cases",
    [x, y, z, h, rx30, ry30, cnot, cz, unentangled_2q, half_cz, s]
    + product_gate_test
    + one_cnot_test
    + two_cnot_test
    + three_cnot_test,
)
def test_odo_decomposition(unitary_test_cases):
    ql, theta, qr = kak.odo_decomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    assert np.allclose(
        ql @ expm(1j * np.diag(theta)) @ qr, unitary_test_cases, atol=1e-6, rtol=1e-4
    )


@pytest.mark.parametrize(
    "nonunitary_test_cases",
    [1, 0.5, "random_matrix", np.array([[1, 2], [3, 4]]), np.array([[1j, 2], [3, 4j]])],
)
@pytest.mark.xfail
def test_odo_decomposition_edge_cases(nonunitary_test_cases):
    ql, theta, qr = kak.odo_decomposition(nonunitary_test_cases)


# Test kak decomposition
@pytest.mark.parametrize(
    "unitary_test_cases",
    [cnot, iswap_d, np.kron(rx30, ry30) @ cnot @ swap, cz, swap, swap @ swap, cz @ cnot]  # Identity
    + product_gate_test
    + one_cnot_test
    + two_cnot_test
    + three_cnot_test,
)
def test_kak_decomposition(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    phase = KAK.phase
    u1, u2, u3, u4 = KAK.su2
    theta = KAK.canonical_vector

    result = (
        phase
        * np.kron(u1, u2)
        @ expm(
            1j * (theta[0] * np.kron(x, x) + theta[1] * np.kron(y, y) + theta[2] * np.kron(z, z))
        )
        @ np.kron(u3, u4)
    )

    assert np.allclose(result, unitary_test_cases)
    assert np.allclose(KAK.unitary, unitary_test_cases)

    # Test to cover all branches of _move_to_weyl_chamber
    # Test the KAK vector is indeed in the Weyl chamber
    for i in range(3):
        KAK.canonical_vector[i] += 0.5 * np.pi
    kak._move_to_weyl_chamber(KAK)
    assert np.allclose(KAK.unitary, unitary_test_cases)
    assert KAK.canonical_vector[0] < 0.5 * np.pi
    assert KAK.canonical_vector[1] <= KAK.canonical_vector[0]
    assert KAK.canonical_vector[2] <= KAK.canonical_vector[1]
    assert KAK.canonical_vector[0] + KAK.canonical_vector[1] <= 0.5 * np.pi
    assert (KAK.canonical_vector[2] != 0) or (KAK.canonical_vector[0] <= 0.25 * np.pi)


@pytest.mark.parametrize("unitary_test_cases", product_gate_test)
def test_kak_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    circ = KAK.to_circuit(QubitSet([0, 1]))

    assert KAK.num_cnots == 0
    assert predicates.eq_up_to_phase(circ.as_unitary(), KAK.unitary, atol=KAK.atol, rtol=KAK.rtol)


@pytest.mark.parametrize("unitary_test_cases", one_cnot_test)
def test_kak_one_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    circ = KAK.to_circuit(QubitSet([0, 1]))

    assert KAK.num_cnots == 1
    assert predicates.eq_up_to_phase(circ.as_unitary(), KAK.unitary, atol=KAK.atol, rtol=KAK.rtol)


@pytest.mark.parametrize("unitary_test_cases", two_cnot_test)
def test_kak_two_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    circ = KAK.to_circuit(QubitSet([0, 1]))

    assert KAK.num_cnots == 2
    assert predicates.eq_up_to_phase(circ.as_unitary(), KAK.unitary, atol=KAK.atol, rtol=KAK.rtol)


@pytest.mark.parametrize("unitary_test_cases", three_cnot_test)
def test_kak_three_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    circ = KAK.to_circuit(QubitSet([0, 1]))

    assert KAK.num_cnots == 3
    assert predicates.eq_up_to_phase(circ.as_unitary(), KAK.unitary, atol=KAK.atol, rtol=KAK.rtol)


xx_repr = """
TwoQubitDecomposition(
  U = (u1 ⊗ u2) · exp(i(v0·XX + v1·YY+v2·ZZ))·(u3 ⊗ u4)
  global phase: (-1+1.2246467991473532e-16j),
  canonical vector v: [0 0 0],
  u1: [[0.000000e+00+0.j 6.123234e-17-1.j]
      [6.123234e-17-1.j 0.000000e+00+0.j]],
  u2: [[0.000000e+00+0.j 6.123234e-17-1.j]
      [6.123234e-17-1.j 0.000000e+00+0.j]],
  u3: [[1. 0.]
      [0. 1.]],
  u4: [[1. 0.]
      [0. 1.]]
)
""".strip()

xx_pretty = """
TwoQubitDecomposition(
  U = (u1 ⊗ u2) · exp(i(v0·XX + v1·YY+v2·ZZ))·(u3 ⊗ u4)
  global phase: -1.+1.225e-16j,
  canonical vector: [0 0 0],
  u1: [[0.000e+00+0.j 6.123e-17-1.j]
      [6.123e-17-1.j 0.000e+00+0.j]],
  u2: [[0.000e+00+0.j 6.123e-17-1.j]
      [6.123e-17-1.j 0.000e+00+0.j]],
  u3: [[1. 0.]
      [0. 1.]],
  u4: [[1. 0.]
      [0. 1.]]
)
""".strip()


@pytest.mark.parametrize("xx_test_case, rep, pretty_rep", [(np.kron(x, x), xx_repr, xx_pretty)])
def test_misc(xx_test_case, rep, pretty_rep):

    test_decomp = kak.TwoQubitDecomposition(xx_test_case)

    # Test two_qubit_decompose function
    assert kak.two_qubit_decompose(xx_test_case).__repr__() == test_decomp.__repr__()

    # Test rep
    assert test_decomp.__repr__().strip() == rep

    # Test pretty_print
    capturedOutput = io.StringIO()
    sys.stdout = capturedOutput
    assert test_decomp.pretty_print().strip() == pretty_rep
    sys.stdout = sys.__stdout__
    assert capturedOutput.getvalue().strip() == pretty_rep


@pytest.mark.parametrize(
    "nonunitary_test_cases",
    [
        1,
        0.5,
        "random_matrix",
        np.array([[1, 2], [3, 4]]),
        np.array([[1j, 2], [3, 4j]]),
        np.array([[1, 2, 3, 4], [1j, 2j, 3j, 5j], [6, 8, 7, 1], [2, 6, 8, 1]]),
    ],
)
@pytest.mark.xfail
def test_kak_decomposition_edge_cases(nonunitary_test_cases):
    kak.TwoQubitDecomposition(nonunitary_test_cases)
