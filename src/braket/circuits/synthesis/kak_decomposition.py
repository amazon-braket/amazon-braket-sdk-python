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

import numpy as np
from scipy.linalg import expm
from typing import Tuple

from braket.circuits.synthesis.util import (diagonalize_two_matrices_with_hermitian_products,
                                            makhlin_invariants, magic_basis, is_diag)

kak_theta_transform = np.array([[1,  1, -1,  1], 
                              [1,  1,  1, -1],
                              [1, -1, -1, -1],
                              [1, -1,  1,  1]])

x = np.array([[0, 1],
	      [1, 0]], dtype=np.complex128)

y = np.array([[0, -1j],
              [1j, 0]])

z = np.array([[1, 0],
	      [0, -1]], dtype=np.complex128)

I = np.array([[1, 0],
	      [0, 1]], dtype=np.complex128)

def odo_decomposition(U: np.ndarray,
                      validate_input: bool=True,
                      atol: float=1E-8,
                      rtol: float=1E-5) -> Tuple[np.ndarray]:

    """
    Decompose a unitary matrix U into QL * exp(i * theta) * QR.T,
    where QL, QR are orthogonal matrices and theta is a 1-d vector
    of angles. This decomposition can be derived from the
    Eckhart-Young simultaneuous diagonalization of Hermitian matrices.
    We call it orthogonal-diagonal-orthogonal (odo) decomposition.

    Args:
        U (np.ndarray): input matrix to decompose.
        validate_input (bool): if check input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.

    Returns:
        QL (np.ndarray): first orthogonal matrix in the decomposition.
        theta (np.ndarray): the vector of diagonal elements.
        QR (np.ndarray): second orthogonal matrix in the decomposition.
    """

    if validate_input:
        try:
            dim1, dim2 = np.shape(U)

        except ValueError:
            print("The input need to be a 2d numpy array.")

        if (np.shape(U)[0] != np.shape(U)[1] or
            (not np.allclose(np.linalg.det(U.conj().T @ U),
                             1,
                             atol=atol,
                             rtol=rtol))):
            raise ValueError("The input matrix has to be unitary.")

    XR = np.real(U)
    XI = np.imag(U)

    QL, QR = diagonalize_two_matrices_with_hermitian_products(XR,
                                                              XI,
                                                              atol=atol,
                                                              rtol=rtol)

    if np.linalg.det(QL) < 0:
        QL[0, :] = -1 * QL[0, :]
    if np.linalg.det(QR) < 0:
        QR[:, 0] = -1 * QR[:, 0]
         
    theta = np.diag(np.angle(QL @ U @ QR))

    return (QL.T, theta, QR.T)

def decompose_two_qubit_product(U:np.ndarray,
                                validate_input: bool=True,
                                atol: float=1E-8,
                                rtol: float=1E-5):
    """
    Decompose a 4x4 unitary matrix to two 2x2 unitary matrices.

    Args:
        U (np.ndarray): input 4x4 unitary matrix to decompose.
        validate_input (bool): if check input.

    Returns:
        phase: global phase.
        U1: decomposed unitary matrix U1.
        U2: decomposed unitary matrix U2.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.

    Raises:
        AssertionError: if the input is not a 4x4 unitary or
        cannot be decomposed.
    """

    if validate_input:
        assert np.allclose(makhlin_invariants(U),
                           (1, 0, 3),
                           atol=atol,
                           rtol=rtol)

    i, j = np.unravel_index(np.argmax(U, axis=None), U.shape)

    def u1_set(i): return (1, 3) if i % 2 else (0, 2)
    def u2_set(i): return (0, 1) if i < 2 else (2, 3)

    u1 = U[np.ix_(u1_set(i), u1_set(j))]
    u2 = U[np.ix_(u2_set(i), u2_set(j))]
    
    try:
        u1 = u1 / np.sqrt(np.linalg.det(u1))
        u2 = u2 / np.sqrt(np.linalg.det(u2))
    except ValueError:
        print("The decomposed 1q product gate is ill-conditioned.")
    
    phase = U[i, j] / (u1[i // 2, j // 2] * u2[i % 2, j % 2])
    
    return phase, u1, u2


def kak_decomposition(U: np.ndarray,
                      validate_input: bool=True,
                      atol: float=1E-8,
                      rtol: float=1E-5):
    """
    KAK decomposition of a 4x4 unitary matrix U:
    U = (u1 ⊗ u2) · exp(i(a·XX + b·YY+c·ZZ))·(u3 ⊗ u4)
    
    References:
        1. Byron Drury, Peter J. Love, Constructive Quantum Shannon 
        Decomposition from Cartan Involutions, arXiv:quant-ph/0806.4015
        2. Robert R. Tucci, An introduction to Cartan's KAK decomposition
        for QC programmers, arXiv:quant-ph/0507171

    Args:
        U (np.ndarray): input 4x4 unitary matrix to decompose.
        validate_input (bool): if check input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.
    """

    if validate_input:
        try:
            dim1, dim2 = np.shape(U)

        except ValueError:
            print("The input need to be a 2d numpy array.")

        if (np.shape(U)[0] != 4 or
            np.shape(U)[1] != 4 or
            (not np.allclose(U.conj().T @ U,
                             np.eye(np.shape(U)[0]),
                             atol=atol,
                             rtol=rtol))):
            raise ValueError("The input matrix has to be 4x4 unitary.")

    magic_u = magic_basis.conj().T @ U @ magic_basis
    ql, theta, qr = odo_decomposition(magic_u,
                                      atol=atol,
                                      rtol=rtol)

    kak_4vector = 0.25 * kak_theta_transform.T @ theta
    
    g1, u1, u2 = decompose_two_qubit_product(magic_basis @ 
                                             ql @ 
                                             magic_basis.conj().T,
                                             atol=atol,
                                             rtol=rtol)

    g2, u3, u4 = decompose_two_qubit_product(magic_basis @
                                             qr @ 
                                             magic_basis.conj().T,
                                             atol=atol,
                                             rtol=rtol)

    return (g1 * g2 * np.exp(1j*kak_4vector[0]), u1, u2, u3, u4, kak_4vector[1:])
