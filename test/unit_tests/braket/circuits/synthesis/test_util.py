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

import numpy as np
from scipy.linalg import expm
import pytest
import random

import braket.circuits.synthesis.util as util
from braket.circuits.gates import X, Y, Z, H, S, CNot, CZ

id_matrix = np.eye(2)
x = X().to_matrix()
y = Y().to_matrix()
z = Z().to_matrix()
h = H().to_matrix()
s = S().to_matrix()
cnot = CNot().to_matrix()
cz = CZ().to_matrix()

diag_matrix_3d = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 1]], dtype=np.complex128)

matrix_3d = np.array([[3, 1, 0], [1, 3, 0], [0, 0, 4]], dtype=np.complex128)

partial_rank_diag_3d = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 0]], dtype=np.complex128)

partial_rank_diag_3d_2 = np.array([[2, 0, 0], [0, 3 + 2j, 0], [0, 0, 0]], dtype=np.complex128)

partial_rank_3d = np.array([[3, 1, 0], [1, 3, 0], [0, 0, 0]], dtype=np.complex128)

empty_2d = np.array([[0, 0], [0, 0]], dtype=np.complex128)

unentangled_2q = np.array([[1, 0, 0, 0], [0, 1j, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1j]])

half_cz = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1j]])

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
    return np.kron(
        u(2 * np.pi * random.random(), 2 * np.pi * random.random(), 2 * np.pi * random.random()),
        u(2 * np.pi * random.random(), 2 * np.pi * random.random(), 2 * np.pi * random.random()),
    )


simple_u_test = [
    u(2 * np.pi * random.random(), 2 * np.pi * random.random(), 2 * np.pi * random.random())
    for _ in range(10)
]

product_gate_test = [random_kron_u() for _ in range(10)]

one_cnot_test = [random_kron_u() @ cnot @ random_kron_u() for _ in range(10)]

two_cnot_test = [
    random_kron_u() @ cnot @ random_kron_u() @ cnot @ random_kron_u() for _ in range(10)
]

three_cnot_test = [
    random_kron_u() @ cnot @ random_kron_u() @ cnot_re @ random_kron_u() @ cnot @ random_kron_u()
    for _ in range(10)
]

unitary_test = simple_u_test + product_gate_test + one_cnot_test + two_cnot_test + three_cnot_test

unitary_test_with_phase = [u * np.exp(2 * np.pi * random.random()) for u in unitary_test]

dim8_test = [
    np.kron(
        u(2 * np.pi * random.random(), 2 * np.pi * random.random(), 2 * np.pi * random.random()),
        random_kron_u(),
    )
    for _ in range(5)
]

dim16_test = [np.kron(random_kron_u(), random_kron_u()) for _ in range(5)]

# Test rx, ry, rz


@pytest.mark.parametrize("theta", [2 * np.pi * random.random() for _ in range(10)])
def test_r_gates(theta):
    rx_result = util.rx(theta)
    ry_result = util.ry(theta)
    rz_result = util.rz(theta)

    assert np.allclose(rx_result, expm(-0.5j * theta * x))
    assert np.allclose(ry_result, expm(-0.5j * theta * y))
    assert np.allclose(rz_result, expm(-0.5j * theta * z))


# Test to_su


@pytest.mark.parametrize("unitary_test_cases", unitary_test + dim8_test + dim16_test)
def test_to_su(unitary_test_cases):
    su = util.to_su(unitary_test_cases)
    assert np.isclose(np.linalg.det(su), 1)


# Test diagonalize_commuting_hermitian_matrices function


@pytest.mark.parametrize(
    "d_c_h_m_test_1, d_c_h_m_test_2",
    [
        (matrix_3d, diag_matrix_3d),
        (diag_matrix_3d, matrix_3d),
        (partial_rank_3d, partial_rank_diag_3d),
        (id_matrix, x),
        (id_matrix, y),
        (y, id_matrix),
        (x, np.zeros_like(x)),
        (np.zeros_like(y), y),
        (cz, swap),
        (swap, cz),
        (np.kron(z, id_matrix), cnot),
        (np.kron(id_matrix, x), cnot),
    ],
)
def test_d_c_h_m(d_c_h_m_test_1, d_c_h_m_test_2):

    p = util.diagonalize_commuting_hermitian_matrices(d_c_h_m_test_1, d_c_h_m_test_2)

    assert util.is_diag(p.conj().T @ d_c_h_m_test_1 @ p) and util.is_diag(
        p.conj().T @ d_c_h_m_test_2 @ p
    )


@pytest.mark.parametrize(
    "d_c_h_m_edge_test_1, d_c_h_m_edge_test_2",
    [
        (partial_rank_3d, partial_rank_diag_3d_2),
        (partial_rank_diag_3d_2, partial_rank_3d),
        (np.array([[]]), np.array([[]])),
        (np.array([[[0], [1]]]), x),
        (x, z),
        (matrix_3d, x),
    ],
)
@pytest.mark.xfail
def test_d_c_h_m_edge_cases(d_c_h_m_edge_test_1, d_c_h_m_edge_test_2):

    util.diagonalize_commuting_hermitian_matrices(d_c_h_m_edge_test_1, d_c_h_m_edge_test_2)


# Test diagonalize_two_matrices_with_hermitian_products function


@pytest.mark.parametrize(
    "d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2",
    [
        (empty_2d, ry30),
        (matrix_3d, diag_matrix_3d),
        (diag_matrix_3d, matrix_3d),
        (partial_rank_3d, partial_rank_diag_3d),
        (id_matrix, x),
        (id_matrix, y),
        (y, id_matrix),
        (x, np.zeros_like(x)),
        (np.zeros_like(y), y),
        (z, z),
        (cz, swap),
        (swap, cz),
        (np.kron(z, id_matrix), cnot),
        (np.kron(id_matrix, x), cnot),
        (np.kron(id_matrix, x), np.zeros((4, 4))),
    ],
)
def test_d_t_m_w_h_p(d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2):

    u, v = util.diagonalize_two_matrices_with_hermitian_products(
        d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2
    )

    assert np.allclose(u @ u.conj().T, np.eye(u.shape[0]))
    assert np.allclose(v @ v.conj().T, np.eye(v.shape[0]))
    assert util.is_diag(u @ d_t_m_w_h_p_test_1 @ v) and util.is_diag(u @ d_t_m_w_h_p_test_2 @ v)


@pytest.mark.parametrize(
    "d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2",
    [
        (np.array([[[0], [1]]]), x),
        (x, z),
        (matrix_3d, x),
        (partial_rank_3d, partial_rank_diag_3d_2),
        (partial_rank_diag_3d_2, partial_rank_3d),
        (rx30, ry30),
    ],
)
@pytest.mark.xfail
def test_d_t_m_w_h_p_edge_cases(d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2):

    u, v = util.diagonalize_two_matrices_with_hermitian_products(
        d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2
    )


# Test characteristic polynomial

rand_2_matrices = [np.random.rand(2, 2) for _ in range(5)]
rand_3_matrices = [np.random.rand(3, 3) for _ in range(5)]


@pytest.mark.parametrize("char_poly_test", (rand_2_matrices + rand_3_matrices))
def test_characteristic_polynomial(char_poly_test):

    char_poly = util.char_poly(char_poly_test)

    symp_matrix = Matrix(char_poly_test)
    a = Symbol("a")
    poly = symp_matrix.charpoly(a)

    symp_result = np.array(poly.all_coeffs()).astype(np.float128)

    assert np.allclose(char_poly, symp_result)


@pytest.mark.parametrize(
    "char_poly_test",
    [1, 1.5, "random_matrix", np.random.rand(2, 3), np.random.rand(5, 10), np.random.rand(1, 100)],
)
@pytest.mark.xfail
def test_characteristic_polynomial_fail(char_poly_test):
    char_poly = util.char_poly(char_poly_test)
