import numpy as np
import pytest
from braket.circuits.quantum_operator_helpers import (
    is_hermitian,
    is_square_matrix,
    is_unitary,
    verify_quantum_operator_matrix_dimensions,
)

valid_unitary_hermitian_matrix = np.array([[0, 1], [1, 0]])

invalid_dimension_matrices = [
    (np.array([[1]])),
    (np.array([1])),
    (np.array([0, 1, 2])),
    (np.array([[0, 1], [1, 2], [3, 4]])),
    (np.array([[0, 1, 2], [2, 3]])),
    (np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])),
]

invalid_unitary_matrices_false = [(np.array([[0, 1], [1, 1]])), (np.array([[1, 2], [3, 4]]))]

invalid_hermitian_matrices_false = [(np.array([[1, 0], [0, 1j]])), (np.array([[1, 2], [3, 4]]))]

invalid_matrix_type_error = np.array([[0, 1], ["a", 0]])


def test_verify_quantum_operator_matrix_dimensions():
    assert verify_quantum_operator_matrix_dimensions(valid_unitary_hermitian_matrix) is None


def test_is_unitary_true():
    assert is_unitary(valid_unitary_hermitian_matrix)


def test_is_hermitian_true():
    assert is_hermitian(valid_unitary_hermitian_matrix)


def test_is_square_matrix():
    assert is_square_matrix(valid_unitary_hermitian_matrix)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("matrix", invalid_dimension_matrices)
def test_verify_quantum_operator_matrix_dimensions_value_error(matrix):
    verify_quantum_operator_matrix_dimensions(matrix)


@pytest.mark.parametrize("matrix", invalid_unitary_matrices_false)
def test_is_unitary_false(matrix):
    assert not is_unitary(matrix)


@pytest.mark.parametrize("matrix", invalid_hermitian_matrices_false)
def test_is_hermitian_false(matrix):
    assert not is_hermitian(matrix)


@pytest.mark.xfail(raises=Exception)
def test_is_hermitian_exception():
    is_hermitian(invalid_matrix_type_error)


@pytest.mark.xfail(raises=Exception)
def test_is_unitary_exception():
    is_unitary(invalid_matrix_type_error)
