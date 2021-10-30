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

from functools import lru_cache
from typing import Iterable

import numpy as np


def verify_quantum_operator_matrix_dimensions(matrix: np.array) -> None:
    """
    Verifies matrix is square and matrix dimensions are positive powers of 2,
    raising `ValueError` otherwise.

    Args:
        matrix (np.ndarray): matrix to verify

    Raises:
        ValueError: If `matrix` is not a two-dimensional square matrix,
            or has a dimension length that is not a positive power of 2
    """
    if not is_square_matrix(matrix):
        raise ValueError(f"{matrix} is not a two-dimensional square matrix")

    matrix = np.array(matrix, dtype=complex)
    qubit_count = int(np.log2(matrix.shape[0]))

    if 2 ** qubit_count != matrix.shape[0] or qubit_count < 1:
        raise ValueError(f"`matrix` dimension {matrix.shape[0]} is not a positive power of 2")


def is_hermitian(
    matrix: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
        ) -> bool:
    r"""
    Whether matrix is Hermitian

    A square matrix :math:`U` is Hermitian if

    .. math:: U = U^\dagger

    where :math:`U^\dagger` is the conjugate transpose of :math:`U`.

    Args:
        matrix (np.ndarray): matrix to verify
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        bool: If matrix is Hermitian
    """
    is_hermitian = np.allclose(matrix, matrix.conj().T, atol=atol, rtol=rtol)

    if raise_exception and not is_hermitian:
        raise ValueError(f"{matrix} is not Hermitian.")

    return is_hermitian


def is_diag(
    matrix: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
) -> bool:
    """
    Whether matrix is diagonal

    Args:
        matrix (np.ndarray): matrix to check.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        is_diag (bool): True if U is diagonal and False otherwise.
    """
    is_diag = np.allclose(matrix - np.diag(np.diagonal(matrix)), np.zeros_like(matrix), atol=atol, rtol=rtol)

    if raise_exception and not is_diag:
        raise ValueError(f"{matrix} is not diagonal.")

    return is_diag


def is_square_matrix(matrix: np.array) -> bool:
    """
    Whether matrix is square, meaning it has exactly two dimensions and the dimensions are equal

    Args:
        matrix (np.ndarray): matrix to verify

    Returns:
        bool: If matrix is square
    """
    return len(matrix.shape) == 2 and matrix.shape[0] == matrix.shape[1]


def is_unitary(
    matrix: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
        ) -> bool:
    r"""
    Whether matrix is unitary

    A square matrix :math:`U` is unitary if

    .. math:: UU^\dagger = I

    where :math:`U^\dagger` is the conjugate transpose of :math:`U`
    and :math:`I` is the identity matrix.

    Args:
        matrix (np.ndarray): matrix to verify
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        is_unitary (bool): If matrix is unitary
    """
    is_unitary = np.allclose(np.eye(len(matrix)), matrix.dot(matrix.T.conj()), atol=atol, rtol=rtol)

    if raise_exception and not is_unitary:
        raise ValueError(f"{matrix} is not unitary.")

    return is_unitary


def is_cptp(
    matrices: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
        ) -> bool:
    """
    Whether a transformation defined by these matrics as Kraus operators is a
    completely positive trace preserving (CPTP) map. This is the requirement for
    a transformation to be a quantum channel.
    Reference: Section 8.2.3 in Nielsen & Chuang (2010) 10th edition.

    Args:
        matrices (Iterable[np.array]): List of matrices representing Kraus operators.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        is_cptp (bool): If the matrices define a CPTP map.
    """
    E = sum([np.dot(matrix.T.conjugate(), matrix) for matrix in matrices])
    is_cptp = np.allclose(E, np.eye(*E.shape), atol=atol, rtol=rtol)

    if raise_exception and not is_cptp:
        raise ValueError(f"The input Kraus operators does not form a CPTP map.")

    return is_cptp


def commute(
    M1: np.ndarray,
    M2: np.ndarray,
    atol: float = 1e-8,
    rtol: float = 1e-5,
    raise_exception: bool = False,
) -> bool:
    """
    Find out if matrix a, b commute.

    Args:
        M1 (np.ndarray): first matrix to check.
        M2 (np.ndarray): second matrix to check.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        pred (bool): True if M1, M2 commute and False otherwise.
    """

    commute = np.allclose(M1 @ M2 - M2 @ M1, 0, atol=atol, rtol=rtol)

    if raise_exception and not commute:
        raise ValueError(f"{M1}, {M2} do not commute.")

    return commute


def eq_up_to_phase(
    U1, U2, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
) -> bool:
    """
    Find out if U1 and U2 are equivalent up to a global phase.

    Args:
        U1 (np.ndarray): first 2x2 matrix to compare.
        U2 (np.ndarray): second 2x2 matrix to compare.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        eq (bool): True if U1 and U2 are equal up to a global phase.
    """

    i, j = np.unravel_index(np.argmax(abs(U1), axis=None), U1.shape)
    phase = U2[i, j] / U1[i, j]

    eq = np.allclose(U1 * phase, U2, atol=atol, rtol=rtol)

    if raise_exception and not eq:
        raise ValueError(f"{U1} and {U2} are not equal up to a phase")

    return eq


@lru_cache()
def get_pauli_eigenvalues(num_qubits: int) -> np.ndarray:
    """
    Get the eigenvalues of Pauli operators and their tensor products as
    an immutable Numpy array.

    Args:
        num_qubits (int): the number of qubits the operator acts on
Returns:
        np.ndarray: the eigenvalues of a Pauli product operator of the given size
    """
    if num_qubits == 1:
        eigs = np.array([1, -1])
        eigs.setflags(write=False)
        return eigs
    eigs = np.concatenate(
        [get_pauli_eigenvalues(num_qubits - 1), -get_pauli_eigenvalues(num_qubits - 1)]
    )
    eigs.setflags(write=False)
    return eigs
