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
from typing import Tuple

from braket.circuits.synthesis.predicates import is_diag, is_hermitian, commute


def rx(theta):
    """
    Unitary for 1-qubit X rotations.

    Args:
        theta (float): the rotation angle.
    """

    # faster than expm(-0.5j * theta * x)
    return np.array(
        [
            [np.cos(0.5 * theta), -1j * np.sin(0.5 * theta)],
            [-1j * np.sin(0.5 * theta), np.cos(0.5 * theta)],
        ]
    )


def ry(theta):
    """
    Unitary for 1-qubit Y rotations.

    Args:
        theta (float): the rotation angle.
    """
    return np.array(
        [[np.cos(0.5 * theta), -np.sin(0.5 * theta)], [np.sin(0.5 * theta), np.cos(0.5 * theta)]]
    )


def rz(theta):
    """
    Unitary for 1-qubit Z rotations.

    Args:
        theta (float): the rotation angle.
    """
    return np.array([[np.exp(-0.5j * theta), 0], [0, np.exp(0.5j * theta)]])


def to_su(u: np.ndarray) -> np.ndarray:
    """
    Given a unitary in U(N), return the
    unitary in SU(N).

    Args:
        u (np.ndarray): The unitary in U(N).

    Returns:
        su (np.ndarray): The unitary in SU(N)
    """

    return u * np.linalg.det(u) ** (-1 / np.shape(u)[0])


def char_poly(M: np.ndarray, validate_input: bool = True) -> np.ndarray:
    """
    Calculate the characteristic polynomial of a square matrix M
    based on the recursive Faddeev Leverrier algorithm.

    Args:
        M (np.ndarray): The input matrix.
        validate_input (bool): if validate input.

    Returns:
        char_poly (np.ndarray): the charateristics polynomial.
    """

    if validate_input:
        try:
            dim1, dim2 = np.shape(M)
        except ValueError:
            print("The input has to be a 2d numpy array.")

        if M.shape[0] != M.shape[1]:
            raise ValueError("The input has to be a square matrix.")

    char_poly = np.array([1.0])
    Mk = np.array(M)

    for k in range(1, M.shape[0] + 1):
        ak = -Mk.trace() / k
        char_poly = np.append(char_poly, ak)
        Mk += np.diag(np.repeat(ak, M.shape[0]))
        Mk = np.dot(M, Mk)

    return char_poly


def diagonalize_commuting_hermitian_matrices(
    Ha: np.ndarray,
    Hb: np.ndarray,
    validate_input: bool = True,
    atol: float = 1e-8,
    rtol: float = 1e-5,
) -> np.ndarray:
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

        try:
            dim1, dim2 = np.shape(Ha)
        except ValueError:
            print("The input has to be a 2d numpy array.")

        if not dim1 * dim2:
            raise ValueError("Matrices to diagonalized cannot be empty.")

        commute(Ha, Hb, atol=atol, rtol=rtol, raise_exception=True)
        is_hermitian(Ha, atol=atol, rtol=rtol)
        is_hermitian(Hb, atol=atol, rtol=rtol)

    # Check if Ha is all zero.
    if not np.any(Ha):
        Db, Pb = np.linalg.eigh(Hb)
        return Pb

    # Find the eigenvalues and eigenvectors of Ha
    Da, Pa = np.linalg.eigh(Ha)

    block_diag_b = Pa.conj().T @ Hb @ Pa  # RHS results in a block diagonal matrix

    if (not np.any(Hb)) or is_diag(block_diag_b):
        return Pa

    # Partition into sub-arrays with equal eigenvalues.
    Da_index = np.arange(Da.shape[0])
    cut_points = np.where(~np.isclose(np.diff(Da), 0, atol=3e-7))[0] + 1
    # cut_points = np.where(np.diff(Da))[0] + 1

    start_ind = np.insert(cut_points, 0, 0)
    end_ind = np.append(cut_points, len(Da_index))

    blocks = []

    for i in range(start_ind.shape[0]):
        block = block_diag_b[start_ind[i] : end_ind[i], start_ind[i] : end_ind[i]]
        _, u = np.linalg.eigh(block)

        blocks.append(u)

    P = Pa @ block_diag(*blocks)

    return P


def diagonalize_two_matrices_with_hermitian_products(
    Ca: np.ndarray,
    Cb: np.ndarray,
    validate_input: bool = True,
    atol: float = 1e-8,
    rtol: float = 1e-5,
) -> Tuple[np.ndarray]:
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
            print("The input has to be a 2d numpy array.")

        if not dim1 * dim2:
            raise ValueError("Matrices to diagonalized cannot be empty.")

        a_bconj = np.dot(Ca, Cb.conj().T)
        aconj_b = np.dot(Ca.conj().T, Cb)

        is_hermitian(a_bconj, atol=atol, rtol=rtol, raise_exception=True)
        is_hermitian(aconj_b, atol=atol, rtol=rtol, raise_exception=True)

    # Check if Ca is all zero, speedup some common cases.
    if np.allclose(Ca, 0, atol=atol, rtol=rtol):
        ub, sb, vbh = np.linalg.svd(Cb)
        return (ub.conj().T, vbh.conj().T)

    ua, sa, vah = np.linalg.svd(Ca)

    # block_diag_cb = ua.conj().T @ Cb @ vah.conj().T
    block_diag_cb = ua.T @ Cb @ vah.T

    # Check if Cb is all zero, speedup some common cases.
    if not np.any(Cb):
        return (ua.conj().T, vah.conj().T)

    rank = np.count_nonzero(~np.isclose(sa, 0))
    if rank == Ca.shape[0]:
        P = diagonalize_commuting_hermitian_matrices(
            np.diag(sa), block_diag_cb, atol=atol, rtol=rtol
        )

        return P.conj().T @ ua.conj().T, vah.conj().T @ P

    else:
        block_nonzero_ca = np.diag(sa)[:rank, :rank]
        block_nonzero_cb = block_diag_cb[:rank, :rank]
        block_zero_cb = block_diag_cb[rank:, rank:]

        # block_nonzero_ca and block_nonzero_cb commute
        P = diagonalize_commuting_hermitian_matrices(
            block_nonzero_ca, block_nonzero_cb, atol=atol, rtol=rtol
        )

        uh, _, vhh = np.linalg.svd(block_zero_cb)

        U = block_diag(P.conj().T, uh.conj().T) @ ua.conj().T
        V = vah.conj().T @ block_diag(P, vhh.conj().T)

        return U, V
