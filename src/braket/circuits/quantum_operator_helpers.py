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

from functools import lru_cache

import numpy as np


def verify_quantum_operator_matrix_dimensions(matrix: np.array) -> None:
    """
    Verifies matrix is square and matrix dimensions are positive exponents of 2,
    raising `ValueError` otherwise.

    Args:
        matrix (np.ndarray): matrix to verify

    Raises:
        ValueError: If `matrix` is not a two-dimensional square matrix,
            or has a dimension length which is not a positive exponent of 2
    """
    if not is_square_matrix(matrix):
        raise ValueError(f"{matrix} is not a two-dimensional square matrix")

    matrix = np.array(matrix, dtype=complex)
    qubit_count = int(np.log2(matrix.shape[0]))
    if 2 ** qubit_count != matrix.shape[0] or qubit_count < 1:
        raise ValueError(f"`matrix` dimension {matrix.shape[0]} is not a positive exponent of 2")


def is_hermitian(matrix: np.array) -> bool:
    """
    Whether matrix is Hermitian

    Args:
        matrix (np.ndarray): matrix to verify

    Return:
        bool: If matrix is Hermitian
    """
    return np.allclose(matrix, matrix.conj().T)


def is_square_matrix(matrix: np.array) -> bool:
    """
    Whether matrix is square, meaning matrix has two dimensions are both are equivalent

    Args:
        matrix (np.ndarray): matrix to verify

    Return:
        bool: If matrix is square
    """
    return len(matrix.shape) == 2 and matrix.shape[0] == matrix.shape[1]


def is_unitary(matrix: np.array) -> bool:
    """
    Whether matrix is unitary

    Args:
        matrix (np.ndarray): matrix to verify

    Return:
        bool: If matrix is unitary
    """
    return np.allclose(np.eye(len(matrix)), matrix.dot(matrix.T.conj()))


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
