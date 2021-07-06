# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import math
import numpy as np
from scipy.linalg import expm
import pytest
import random

import braket.circuits.synthesis.util as util
import braket.circuits.synthesis.invariants as invariants
import braket.circuits.synthesis.two_qubit_decomposition as kak
from braket.circuits.gates import X, Y, Z, H, S, CNot, CZ


x = X().to_matrix()
y = Y().to_matrix()
z = Z().to_matrix()
h = H().to_matrix()
s = S().to_matrix()
cnot = CNot().to_matrix()
cz = CZ().to_matrix()

I = np.array([[1, 0], [0, 1]], dtype=np.complex128)

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

def random_kron_u():
    return np.kron(u(2*np.pi*random.random(),
                     2*np.pi*random.random(),
                     2*np.pi*random.random()),
                   u(2*np.pi*random.random(),
                     2*np.pi*random.random(),
                     2*np.pi*random.random()))

product_gate_test = [random_kron_u() for _ in range(10)]

one_product_gate_test = [random_kron_u() @ cnot @ random_kron_u() for _ in range(10)]

two_product_gate_test = [
    random_kron_u() @ cnot @ random_kron_u() @ cnot @ random_kron_u() for _ in range(10)
]

three_product_gate_test = [
    random_kron_u() @ cnot @ random_kron_u() @ cnot_re @ random_kron_u() @ cnot @ random_kron_u()
    for _ in range(10)
]

# Test decompose_one_qubit_product

@pytest.mark.parametrize(
    "unitary_test_cases",
    [np.kron(x, z),
     np.kron(x, y),
     np.kron(y, z),
     np.kron(x, I),
     np.kron(h, x)] +
    product_gate_test
)
def test_decompose_one_qubit_product(unitary_test_cases):
    phase, u1, u2 = kak.decompose_one_qubit_product(unitary_test_cases)
    assert np.allclose(phase * np.kron(u1, u2), unitary_test_cases)

@pytest.mark.parametrize("unitary_test_cases", [
    1,
    0.5,
    "random_matrix",
    cnot,
    cz,
    cnot_re,
    iswap_d])
@pytest.mark.xfail
def test_decompose_one_qubit_product_edge_cases(unitary_test_cases):
    phase, u1, u2 = kak.decompose_one_qubit_product(unitary_test_cases)

# Test odo_decomposition.

my_u = np.array([[ 0.27688492-0.05898814j, -0.41403904+0.39328519j,  0.09599308-0.12492767j, -0.58128089-0.48067088j],
              [-0.40551746-0.56281605j,  0.1321146 +0.27852805j, -0.34581881+0.22994657j, 0.22301507-0.44895406j],
              [ 0.01768505-0.26418919j, -0.50085292-0.09884015j,  0.10787925+0.72658022j, -0.09946403+0.34614802j],
              [ 0.60586235-0.0383528j,   0.5531946 +0.11053961j,  0.2675003 +0.43772044j, 0.0919967 -0.20395494j]])


@pytest.mark.parametrize(
    "unitary_test_cases", [x, y, z, h, rx30, ry30, cnot, cz, unentangled_2q, half_cz, s, my_u]
)
def test_odo_decomposition(unitary_test_cases):
    ql, theta, qr = kak.odo_decomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    assert np.allclose(ql @ expm(1j * np.diag(theta)) @ qr, unitary_test_cases, atol=1e-6, rtol=1e-4)

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
    + one_product_gate_test
    + two_product_gate_test
    + three_product_gate_test
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
    assert np.allclose(KAK.unitary(), unitary_test_cases)

@pytest.mark.parametrize("unitary_test_cases", product_gate_test)
def test_kak_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    phase, u1, u2, u3, u4, u5, u6, u7, u8 = KAK.build_circuit()

    assert KAK.num_cnots() == 0
    assert np.allclose(phase * np.kron(u1, u2),
                       KAK.unitary(),
                       atol=KAK.atol,
                       rtol=KAK.rtol)

@pytest.mark.parametrize("unitary_test_cases", one_product_gate_test)
def test_kak_one_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    phase, u1, u2, u3, u4, u5, u6, u7, u8 = KAK.build_circuit()

    assert KAK.num_cnots() == 1
    assert np.allclose(phase * np.kron(u1, u2) @ cnot @ np.kron(u3, u4),
                       KAK.unitary(),
                       atol=KAK.atol,
                       rtol=KAK.rtol)

@pytest.mark.parametrize("unitary_test_cases", two_product_gate_test)
def test_kak_two_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    phase, u1, u2, u3, u4, u5, u6, u7, u8 = KAK.build_circuit()

    two_cnot = cnot_re @ np.kron(u5, u6) @ cnot_re

    assert KAK.num_cnots() == 2
    assert np.allclose(phase * np.kron(u1, u2) @ two_cnot @ np.kron(u3, u4),
                       KAK.unitary(),
                       atol=KAK.atol,
                       rtol=KAK.rtol)

@pytest.mark.parametrize("unitary_test_cases", three_product_gate_test)
def test_kak_three_product_gate(unitary_test_cases):

    KAK = kak.TwoQubitDecomposition(unitary_test_cases, atol=1e-6, rtol=1e-4)
    phase, u1, u2, u3, u4, u5, u6, u7, u8 = KAK.build_circuit()
    
    assert KAK.num_cnots() == 3
    assert np.allclose(phase * np.kron(u1, u2) @
                       cnot @ np.kron(u5, u6) @
                       cnot @ np.kron(u3, u4) @
                       cnot @ np.kron(I, u7),
                       KAK.unitary())

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
    KAK = kak.TwoQubitDecomposition(unitary_test_cases)
