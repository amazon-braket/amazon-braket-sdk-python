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
from scipy.linalg import block_diag
from typing import List, Tuple, Union

magic_basis = np.sqrt(0.5) * np.array([[1, 0,   0,  1j], 
                                       [0, 1j,  1,   0],
                                       [0, 1j, -1,   0],
                                       [1, 0,   0, -1j]])

def is_diag(U, 
            validate_input: bool=True,
            atol: float=1E-8,
            rtol: float=1E-5) -> bool:
    """
    Find out if a matrix is diagonal.

    Args:
        U (np.ndarray): matrix to check.
        validate_input (bool): if validate input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.
    
    Returns:
        diag (bool): True if U is diagonal and False otherwise.
    """

    if validate_input:
        try:
            dim1, dim2 = np.shape(U)

        except ValueError:
            print("The input need to be a 2d numpy array.")

    return np.allclose(U - np.diag(np.diagonal(U)),
                       np.zeros_like(U),
                       atol=atol,
                       rtol=rtol)

def makhlin_invariants(U:np.ndarray,
                       validate_input: bool=True,
                       atol: float=1E-8,
                       rtol: float=1E-5) -> np.dtype:
    """
    Calculate the Maklin invariants of a 2q gate.

    Args:
        U (np.ndarray): matrix to calculate the Makelin invariant.
        validate_input (bool): if validate input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.

    Returns:
        makhlin_invariants (np.dtype): the calculated Makhlin invariants.
    """
    if validate_input:
        try:
            dim1, dim2 = np.shape(U)

        except ValueError:
            print("The input need to be a 2d numpy array.")

        if (np.shape(U) != (4, 4) or
            (not np.allclose(U.conj().T @ U,
                             np.eye(np.shape(U)[0]),
                             atol=atol,
                             rtol=rtol))):
            raise ValueError("The input matrix has to be 4x4 unitary.")

    U_magic = magic_basis.conj().T @ U @ magic_basis
    det = np.linalg.det(U_magic)
    m = U_magic.T @ U_magic

    makhlin_invariants = (np.real(np.trace(m) ** 2 / (16 * det)),
                          np.imag(np.trace(m) ** 2 / (16 * det)),
                          (np.trace(m) ** 2 - np.trace(m @ m)) / (4 * det))

    return makhlin_invariants

def decompose_one_qubit_product(U:np.ndarray,
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


def diagonalize_commuting_hermitian_matrices(Ha: np.ndarray,
                                             Hb: np.ndarray,
                                             validate_input: bool=True,
                                             atol: float=1E-8,
                                             rtol: float=1E-5) -> np.ndarray:
    """
    Given two commuting Hermitian matrices Ha, Hb, calculuate the
    matrix P that simultaneously diagonalizes both Ha and Hb.

    If we replace the numpy.eigh used with numpy.eig, 
    this function can also diagonalize any two commuting matrices
    (not just limited to hermitian matrices), but it will be slower.

    Args:
        Ha (np.ndarray): first matrix to diagonalize.
        Hb (np.ndarray): second matrix to diagonalize.
        validate_input (bool): if validate input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.

    Returns:
        P (np.ndarray): the matrix that simultaneously diagonalizes Ha and Hb.

    Raises:
        ValueError: if not Ha and Hb don't commute.
    """
    
    if validate_input:
        
        if Ha.shape != Hb.shape:
            raise ValueError("The two matrices dimensions do not match.")

        if not np.prod(Ha.shape):
            raise ValueError("Matrices cannot be 0 dimensions.")

        if not np.allclose(Ha @ Hb - Hb @ Ha,
                           0,
                           atol=atol,
                           rtol=rtol):
            raise ValueError("Input matrices do not commute.")

        print("Ha\n", Ha)
        print("Hb\n", Hb)
        print("atol", atol)
        print("rtol", rtol)
    
        if not (np.allclose(Ha, 
                            Ha.conj().T,
                            atol=atol,
                            rtol=rtol)
                and
                np.allclose(Hb,
                            Hb.conj().T,
                            atol=atol,
                            rtol=rtol)):
            raise ValueError("Ha and Hb have to be Hermitian.")

    # Check if Ha is all zero.
    if not np.any(Ha):
        Db, Pb = np.linalg.eigh(Hb)
        return Pb

    # Find the eigenvalues and eigenvectors of Ha
    Da, Pa = np.linalg.eigh(Ha)
    
    block_diag_b = Pa.conj().T @ Hb @ Pa # RHS results in a block diagonal matrix
    if (not np.any(Hb)) or is_diag(block_diag_b, validate_input=False):
        return Pa
    
    # Partition into sub-arrays with equal eigenvalues.
    Da_index = np.arange(Da.shape[0])
    cut_points = np.where(np.diff(Da))[0] + 1

    start_ind = np.insert(cut_points, 0, 0)
    end_ind = np.append(cut_points, len(Da_index))

    blocks = []
    
    for i in range(start_ind.shape[0]):
        block = block_diag_b[start_ind[i]:end_ind[i], start_ind[i]:end_ind[i]]
        _, u = np.linalg.eigh(block)
        
        blocks.append(u)

    P = Pa @ block_diag(*blocks)

    return P

def diagonalize_two_matrices_with_hermitian_products(Ca: np.ndarray,
                                                     Cb: np.ndarray,
                                                     validate_input: bool=True,
                                                     atol: float=1E-8,
                                                     rtol: float=1E-5) -> Tuple[np.ndarray]:
    """
    Given two complex matrices Ca, Cb and the promise that
    (1) Ca times the transpose conjugate of Cb and (2) the transpose conjugate
    of Ca times Cb are Hermitian. Calculate the matrices U and V that 
    simultaneous diagonlize Ca and Cb.

    Reference:
    1. C. Eckart and G. Young, A princial axis transformation for
    non-hermitian matrices, Bull. Amer. Math. Soc. 45, 118-121 (1939).


    Args:
        Ca (np.ndarray): An input complex matrix
        Cb (np.ndarray): Second input complex matrix
        validate_input (bool): if validate input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.
       
    Returns:
        U (np.ndarray): First unitary matrix for simultaneous diagonalization.
        V (np.ndarray): Second unitary matrix for simultaneous diagonalization.

    Raises:
        ValueError: If (1) Ca and Cb have different dimensions or (2)
        Ca and Cb are not 2-d matrices or (3) Ca * conjugate(Cb).T
        and conjugate(Ca).T * Cb are not Hermitian.
    """
    
    # Input validation

    if validate_input:
        if np.shape(Ca) != np.shape(Cb):
            raise ValueError("Matrices to diagonalize need to have the same dimension.")
        
        try:
            dim1, dim2 = np.shape(Ca)
        except ValueError:
            print("Matrices to diagonalized need to be 2-dimensional.")

        if not dim1 * dim2:
            raise ValueError("Matrices to diagonalized cannot be empty.")
            
        a_bconj = np.dot(Ca, Cb.conj().T)
        aconj_b = np.dot(Ca.conj().T, Cb)

        if not (np.allclose(a_bconj, 
                            a_bconj.conj().T,
                            atol=atol,
                            rtol=rtol)
                and
                np.allclose(aconj_b,
                            aconj_b.conj().T,
                            atol=atol,
                            rtol=rtol)):
            raise ValueError("Ca * conj(Cb).T and conj(Ca).T * Cb have to be Hermitian.")
    
    if np.allclose(Ca,
                   0,
                   atol=atol,
                   rtol=rtol):
        ub, sb, vbh = np.linalg.svd(Cb)
        return (ub.conj().T, vbh.conj().T)

    ua, sa, vah = np.linalg.svd(Ca)

    # block_diag_cb = ua.conj().T @ Cb @ vah.conj().T
    block_diag_cb = ua.T @ Cb @ vah.T

    # Check if Ca or Cb is all zero, speedup some common cases.
    if not np.any(Cb):
        return (ua.conj().T, vah.conj().T)
    
    rank = np.count_nonzero(~np.isclose(sa, 0))
    if rank == Ca.shape[0]:
        P = diagonalize_commuting_hermitian_matrices(np.diag(sa),
                                                     block_diag_cb,
                                                     atol=atol,
                                                     rtol=rtol)
        return P.conj().T @ ua.conj().T, vah.conj().T @ P

    else:
        block_nonzero_ca = np.diag(sa)[:rank, :rank]
        block_nonzero_cb = block_diag_cb[:rank, :rank]
        block_zero_cb = block_diag_cb[rank:, rank:]
        
        # block_nonzero_ca and block_nonzero_cb commute
        P = diagonalize_commuting_hermitian_matrices(block_nonzero_ca,
                                                     block_nonzero_cb,
                                                     atol=atol,
                                                     rtol=rtol)
        uh, _, vhh = np.linalg.svd(block_zero_cb)

        U = block_diag(P.conj().T, uh.conj().T) @ ua.conj().T
        V = vah.conj().T @ block_diag(P, vhh.conj().T)

        return U, V
