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
import braket.circuits.synthesis.kak_decomposition as kak

diag_matrix_3d = np.array([[2, 0, 0],
			   [0, 2, 0],
			   [0, 0, 1]], dtype=np.complex128)

matrix_3d = np.array([[3, 1, 0],
		      [1, 3, 0],
		      [0, 0, 4]], dtype=np.complex128)

partial_rank_diag_3d = np.array([[2, 0, 0],
		                 [0, 2, 0],
			         [0, 0, 0]], dtype=np.complex128)

partial_rank_diag_3d_2 = np.array([[2, 0, 0],
		                 [0, 2, 0],
			         [0, 0, 0]], dtype=np.complex128)
partial_rank_3d = np.array([[3, 1, 0],
		            [1, 3, 0],
		            [0, 0, 0]], dtype=np.complex128)

partial_diag_numeric = np.array([[2.00000000e+00, 3.99346924e-16, 0.00000000e+00],
                                 [3.54604637e-16, 4.00000000e+00, 0.00000000e+00],
                                 [0.00000000e+00, 0.00000000e+00, 0.00000000e+00]], dtype=np.complex128)

empty_2d = np.array([[0, 0],
                     [0, 0]], dtype=np.complex128)

x = np.array([[0, 1],
	      [1, 0]], dtype=np.complex128)

y = np.array([[0, -1j],
              [1j, 0]])

z = np.array([[1, 0],
	      [0, -1]], dtype=np.complex128)

h = 0.5 * np.sqrt(2) * np.array([[1,  1],
                                 [1, -1]], dtype=np.complex128)

s = np.array([[1, 0],
	      [0, 1j]])

I = np.array([[1, 0],
              [0, 1]], dtype=np.complex128)

cz = np.array([[1, 0, 0, 0],
               [0, 1, 0, 0],
               [0, 0, 1, 0],
               [0, 0, 0, -1]], dtype=np.complex128)

iswap_d = np.array([[1, 0, 0, 0],
                    [0, 0,-1j, 0],
                    [0,-1j, 0, 0],
                    [0, 0, 0,  1]], dtype=np.complex128)

unentangled_2q = np.array([[1, 0,  0, 0],
                           [0, 1j, 0, 0],
                           [0, 0,  1, 0],
                           [0, 0,  0, 1j]])

half_cz = np.array([[1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1j]])

cx =  np.array([[1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]], dtype=np.complex128)

cx_re = np.array([[1, 0, 0, 0],
                  [0, 0, 0, 1],
                  [0, 0, 1, 0],
                  [0, 1, 0, 0]], dtype=np.complex128)

swap =  np.array([[1, 0, 0, 0],
                  [0, 0, 1, 0],
                  [0, 1, 0, 0],
                  [0, 0, 0, 1]], dtype=np.complex128)

ry30 = np.array([[np.cos(np.pi/12), -np.sin(np.pi/12)],
                 [np.sin(np.pi/12),  np.cos(np.pi/12)]], dtype=np.complex128)

rx30 = np.array([[np.cos(np.pi/12), -1j*np.sin(np.pi/12)],
                 [-1j*np.sin(np.pi/12),  np.cos(np.pi/12)]])

# Test is_diag function
@pytest.mark.parametrize("diag_test_input, diag_test_output", [
    (x, False),
    (z, True),
    (y, False),
    (s, True),
    (partial_rank_diag_3d, True),
    (partial_rank_3d, False),
    (diag_matrix_3d, True),
    (matrix_3d, False),
    (partial_diag_numeric, True)])
def test_diag(diag_test_input, diag_test_output):
    
    assert util.is_diag(diag_test_input) == diag_test_output

# Test diagonalize_commuting_hermitian_matrices function

@pytest.mark.parametrize("d_c_h_m_test_1, d_c_h_m_test_2", [
    (matrix_3d, diag_matrix_3d),
    (diag_matrix_3d, matrix_3d),
    (partial_rank_3d, partial_rank_diag_3d),
    (partial_rank_3d, partial_rank_diag_3d_2),
    (partial_rank_diag_3d_2, partial_rank_3d),
    (I, x),
    (I, y),
    (y, I),
    (x, np.zeros_like(x)),
    (np.zeros_like(y), y),
    (cz, swap),
    (swap, cz),
    (np.kron(z, I), cx),
    (np.kron(I, x), cx)])
def test_d_c_h_m(d_c_h_m_test_1, d_c_h_m_test_2):

    p = util.diagonalize_commuting_hermitian_matrices(d_c_h_m_test_1,
                                                      d_c_h_m_test_2)

    assert (util.is_diag(p.conj().T @ d_c_h_m_test_1 @ p) and
            util.is_diag(p.conj().T @ d_c_h_m_test_2 @ p))

@pytest.mark.parametrize("d_c_h_m_edge_test_1, d_c_h_m_edge_test_2", [
    (empty_2d, ry30),
    (np.array([[]]), np.array([[]])),
    (np.array([[[0],[1]]]), x),
    (x, z),
    (matrix_3d, x)])
@pytest.mark.xfail
def test_d_c_h_m_edge_cases(d_c_h_m_edge_test_1, d_c_h_m_edge_test_2):

    p = util.diagonalize_commuting_hermitian_matrices(d_c_h_m_edge_test_1,
                                                      d_c_h_m_edge_test_2)


# Test diagonalize_two_matrices_with_hermitian_products function

@pytest.mark.parametrize("d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2", [
    (empty_2d, ry30),
    (matrix_3d, diag_matrix_3d),
    (diag_matrix_3d, matrix_3d),
    (partial_rank_3d, partial_rank_diag_3d),
    (partial_rank_3d, partial_rank_diag_3d_2),
    (partial_rank_diag_3d_2, partial_rank_3d),
    (I, x),
    (I, y),
    (y, I),
    (x, np.zeros_like(x)),
    (np.zeros_like(y), y),
    (z, z),
    (cz, swap),
    (swap, cz),
    (np.kron(z, I), cx),
    (np.kron(I, x), cx)])
def test_d_t_m_w_h_p(d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2):

    u, v = util.diagonalize_two_matrices_with_hermitian_products(d_t_m_w_h_p_test_1,
                                                                 d_t_m_w_h_p_test_2)
    
    assert (util.is_diag(u @ d_t_m_w_h_p_test_1 @ v) and
            util.is_diag(u @ d_t_m_w_h_p_test_2 @ v))

@pytest.mark.parametrize("d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2", [
    (np.array([[[0],[1]]]), x),
    (x, z),
    (matrix_3d, x),
    (rx30, ry30)])
@pytest.mark.xfail
def test_d_t_m_w_h_p_edge_cases(d_t_m_w_h_p_test_1, d_t_m_w_h_p_test_2):

    u, v = util.diagonalize_two_matrices_with_hermitian_products(d_t_m_w_h_p_test_1,
                                                                 d_t_m_w_h_p_test_2)


# Test makhlin_invariants

@pytest.mark.parametrize("unitary_test_cases, result", [
    (np.kron(x, y), (1, 0, 3)),
    (np.kron(y, z), (1, 0, 3)),
    (np.kron(h, z), (1, 0, 3)),
    (np.kron(rx30, ry30), (1, 0, 3)),
    (cx, (0, 0, 1)),
    (cz, (0, 0, 1)),
    (iswap_d, (0, 0, -1))
    ])
def test_makhlin_invariants(unitary_test_cases, result):

    mk = util.makhlin_invariants(unitary_test_cases)
    
    assert np.allclose(mk, result)

@pytest.mark.parametrize("nonunitary_test_cases", [
    np.array([[1, 2],
              [3, 4]]),
    np.array([[1j, 2],
              [3, 4j]])
    ])
@pytest.mark.xfail
def test_makhlin_invariants(nonunitary_test_cases):

    mk = util.makhlin_invariants(nonunitary_test_cases)

# Test decompose two qubit product
@pytest.mark.parametrize("unitary_test_cases", [
    np.kron(x, z),
    np.kron(x, y),
    np.kron(y, z),
    np.kron(x, I),
    np.kron(h, x)
    ])
def test_decompose_two_qubit_product(unitary_test_cases):

    phase, u1, u2 = kak.decompose_two_qubit_product(unitary_test_cases)

    assert np.allclose(phase * np.kron(u1, u2), unitary_test_cases)
    
# Test odo decomposition.

@pytest.mark.parametrize("unitary_test_cases", [
    x,
    y,
    z,
    h,
    rx30,
    ry30,
    cx,
    cz,
    unentangled_2q,
    half_cz,
    s])
def test_odo_decomposition(unitary_test_cases):

    ql, theta, qr = kak.odo_decomposition(unitary_test_cases)

    assert np.allclose(ql @ np.diag(np.exp(1j*theta)) @ qr,  unitary_test_cases, atol=1E-5)


@pytest.mark.parametrize("nonunitary_test_cases", [
    np.array([[1, 2],
              [3, 4]]),
    np.array([[1j, 2],
              [3, 4j]])
    ])
@pytest.mark.xfail
def test_odo_decomposition_edge_cases(nonunitary_test_cases):

    ql, theta, qr = kak.odo_decomposition(nonunitary_test_cases)


# Generating random tests on the fly does not work: 
# we cannot control if the random matrix is ill-conditioned.
# Thus, instead, we use static random matrices.
# 

random_prod_gates = [
    np.array([[ 0.8063174 -0.j,0.24737272-0.07059792j,-0.45466043+0.22528128j,-0.11976202+0.10892302j],
              [ 0.23395   +0.10698003j,-0.79715594-0.12120294j,-0.16180775+0.0050414j,0.48335807-0.15437857j],
              [-0.32582821-0.38897782j,-0.13401923-0.09080755j,-0.73836796-0.32397609j,-0.25489234-0.03474513j],
              [-0.04292931-0.15609048j, 0.26365626+0.43353563j,-0.17125045-0.19196514j,0.68127954+0.43128405j]]),
    np.array([[-0.5625085 +0.j        ,-0.49802491-0.16788566j, 0.17554906+0.43207001j,0.02646973+0.43493352j],
              [ 0.52495059+0.0253236j ,-0.52375933-0.20516327j,-0.14437652-0.41112435j,0.00586758+0.46633415j],
              [-0.2232265 +0.40947759j,-0.31984899+0.29591288j,-0.55890905-0.06353333j,-0.475876  -0.22306151j],
              [ 0.22675627-0.3720879j ,-0.35719767+0.29985294j, 0.51873127+0.08445285j,-0.49723538-0.2630072j ]]),
    np.array([[-0.26402072+0.j,        -0.1746762+0.78861593j, 0.1162715 +0.11533914j,0.42143719-0.27098839j],
              [ 0.77021842-0.24329088j, 0.0231976+0.26299963j, -0.44547796-0.2293325j, .1046771 -0.12595587j],
              [ 0.04313484-0.15799229j,-0.4433765-0.23336927j, 0.22874078-0.13185066j,-0.24249594-0.77046907j],
              [ 0.01975161+0.50065346j,-0.1611712-0.02908634j, -0.54579919+0.59542431j,-0.1514386 -0.21627134j]])]

random_twoq_gates = [
    np.array([[-0.49007092+0.00702938j, 0.39489867+0.41581432j,-0.59705207-0.23140995j,-0.01772778+0.14352199j],
              [ 0.31736401+0.03787557j,-0.0756966 -0.39778764j,-0.32945446-0.50656775j,0.51663842+0.31908332j],
              [-0.40662081+0.61444012j,-0.52129145-0.19082607j,-0.0879649 -0.24656548j,-0.18218762-0.21734488j],
              [-0.30884813+0.13914848j,-0.28087774+0.34660762j, 0.28851213+0.27028786j,0.59672663+0.41694597j]]),
    np.array([[-0.87900399-0.09049082j, 0.0360273 +0.1251152j,  0.12177434-0.03471878j,-0.05092698+0.42846666j],
              [ 0.16262249+0.06438469j, 0.41500686+0.48131463j,-0.60401669-0.1450482j,-0.30375521+0.29558704j],
              [ 0.34602579-0.01542241j, 0.23355145-0.19325159j, 0.53265694-0.44221126j,-0.1265688 +0.54114875j],
              [ 0.13303497+0.22561458j,-0.65961413-0.22840861j,-0.24986772+0.23744974j,-0.27359424+0.50046818j]]),
    np.array([[ 0.15559852-0.22619733j,-0.04393983+0.02602995j, 0.46197779+0.33220716j,0.73755443-0.23290337j],
              [-0.6583155 -0.56086741j,-0.14938805-0.20152001j, 0.17741259+0.219999j,-0.15253952+0.29322049j],
              [ 0.20537531-0.29276479j,-0.58536375+0.61573704j, 0.04312438-0.30941939j,-0.00486776+0.22957173j],
              [-0.21692114-0.04156087j,-0.45121163-0.09534085j,-0.69140583+0.14386812j,0.24363593-0.42477944j]]),
    np.array([[-0.34253502+0.45119525j,-0.2724136 +0.11679051j, 0.42466029-0.52100138j,0.11405593+0.35560631j],
              [-0.50293003+0.43092648j,-0.27351341-0.26209731j,-0.53571031+0.12283894j,-0.21032801-0.2674815j ],
              [-0.04111573-0.39591237j,-0.59495132+0.09671176j,-0.36157479+0.11972844j,0.32176905+0.47920361j],
              [ 0.08513863-0.27344225j,-0.47301539+0.42612489j, 0.06797549-0.31057101j,-0.43750273-0.46922394j]])]

# Test kak decomposition
@pytest.mark.parametrize("unitary_test_cases", [
    cx,
    iswap_d,
    np.kron(rx30, ry30) @ cx @ swap,
    cz,
    swap,
    swap @ swap, # Identity
    cz @ cx
    ] + 
    random_prod_gates +
    random_twoq_gates)
def test_kak_decomposition(unitary_test_cases):
    
    print(unitary_test_cases)
    phase, u1, u2, u3, u4, theta = kak.kak_decomposition(unitary_test_cases, atol=1E-6, rtol=1E-4)
    
    result = phase * np.kron(u1, u2) @ expm(1j*(theta[0] * np.kron(x, x) +
                                                theta[1] * np.kron(y, y) +
                                                theta[2] * np.kron(z, z))) @ np.kron(u3, u4)
    assert np.allclose(result, unitary_test_cases, atol=1E-6, rtol=1E-4)
    
@pytest.mark.parametrize("nonunitary_test_cases", [
    np.array([[1, 2],
              [3, 4]]),
    np.array([[1j, 2],
              [3, 4j]]),
    np.array([[1, 2, 3, 4],
              [1j, 2j, 3j, 5j],
              [6, 8, 7, 1],
              [2, 6, 8, 1]])
    ])
@pytest.mark.xfail
def test_kak_decomposition_edge_cases(nonunitary_test_cases):

    phase, u1, u2, u3, u4, theta = kak.kak_decomposition(nonunitary_test_cases)

