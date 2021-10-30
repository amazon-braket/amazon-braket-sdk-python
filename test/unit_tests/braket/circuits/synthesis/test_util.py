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

import braket.circuits.synthesis.util as util
from braket.circuits.gates import X, Y, Z, H, S, CNot, CZ

I = np.eye(2)  # noqa: E741
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


simple_u_test = [
    u(0.12, 0.36, 0.71),
    u(-0.96, 2.74, -4.18),
    u(1.24, 4.12, 2.45),
    u(0.0, 0.1, -0.01),
]

product_gate_test = [
    np.kron(u(0.14, 0.52, -2.14), u(0.24, 0.05, 1.0)),
    np.kron(u(1.83, 2.18, 0.88), u(0.33, -1.35, 3.14)),
    np.kron(u(-0.14, 3.02, -1.55), u(0.61, 1.89, 0.99)),
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

unitary_test = simple_u_test + product_gate_test + one_cnot_test + two_cnot_test + three_cnot_test

unitary_test_with_phase = [u * np.exp(2 * np.pi * 0.58) for u in unitary_test]

dim8_test = [
    np.kron(
        u(2 * np.pi * 0.28, 2 * np.pi * 1.41, 2 * np.pi * 0.85),
        p,
    )
    for p in product_gate_test
]

dim16_test = [np.kron(p1, p2) for p1 in product_gate_test for p2 in product_gate_test]

# Test rx, ry, rz


@pytest.mark.parametrize(
    "theta", [2 * np.pi * 0.2, 2 * np.pi * 0.48, 2 * np.pi * 0.96, 2 * np.pi * (-1.2)]
)
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
        (I, x),
        (I, y),
        (y, I),
        (x, np.zeros_like(x)),
        (np.zeros_like(y), y),
        (cz, swap),
        (swap, cz),
        (np.kron(z, I), cnot),
        (np.kron(I, x), cnot),
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
        (I, x),
        (I, y),
        (y, I),
        (x, np.zeros_like(x)),
        (np.zeros_like(y), y),
        (z, z),
        (cz, swap),
        (swap, cz),
        (np.kron(z, I), cnot),
        (np.kron(I, x), cnot),
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
rand_2_matrices = [
    (np.array([[0.99075591, 0.50094016], [0.84589721, 0.53871472]]), [1.0, -1.52947062, 0.1099909]),
    (
        np.array([[0.18361679, 0.74752576], [0.98807338, 0.35065077]]),
        [1.0, -0.53426756, -0.67422493],
    ),
]

rand_3_matrices = [
    (
        np.array(
            [
                [0.92388307, 0.134172, 0.29094152],
                [0.51649275, 0.83797745, 0.70229967],
                [0.04661202, 0.00263746, 0.76393976],
            ]
        ),
        [1.0, -2.52580027, 2.03543595, -0.5302099],
    ),
    (
        np.array(
            [
                [0.53127718, 0.29017192, 0.93471071],
                [0.14653856, 0.35800881, 0.93947677],
                [0.61501518, 0.25281797, 0.06926795],
            ]
        ),
        [1.0, -0.95855394, -0.60309833, 0.1194751],
    ),
]


@pytest.mark.parametrize("char_poly_test, result", (rand_2_matrices + rand_3_matrices))
def test_characteristic_polynomial(char_poly_test, result):
    char_poly = util.char_poly(char_poly_test)
    assert np.allclose(char_poly, result)


@pytest.mark.parametrize(
    "char_poly_test",
    [1, 1.5, "random_matrix", [0.1, 0.2]],
)
@pytest.mark.xfail
def test_characteristic_polynomial_fail(char_poly_test):
    util.char_poly(char_poly_test)
