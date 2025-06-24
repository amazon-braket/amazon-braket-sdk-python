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

import functools
import itertools
import math
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from braket.default_simulator import gate_operations
from braket.default_simulator.linalg_utils import multiply_matrix
from braket.default_simulator.operation import GateOperation, Observable
from braket.default_simulator.operation_helpers import (
    check_hermitian,
    check_matrix_dimensions,
    pauli_eigenvalues,
)


class Identity(Observable):
    """Identity observable

    Note:
        This observable refers to the same mathematical object as the gate operation
        of the same name, but is meant to be used differently; the observable is viewed
        as a Hermitian operator to be measured, while the gate is viewed as a unitary
        operator to evolve the state of the system.
    """

    def __init__(self, targets: Optional[list[int]] = None):
        self._measured_qubits = _validate_and_clone_single_qubit_target(targets)

    def _pow(self, power: int) -> Observable:
        return self

    @property
    def targets(self) -> tuple[int, ...]:
        return ()

    @property
    def measured_qubits(self):
        return self._measured_qubits

    @property
    def eigenvalues(self) -> np.ndarray:
        return np.array([1, 1])

    def apply(self, state: np.ndarray) -> np.ndarray:
        return state

    def fix_qubit(self, qubit: int) -> Observable:
        return Identity([qubit])

    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        return ()


class _InvolutoryMatrixObservable(Observable, ABC):
    r"""
    An observable defined by an involutory matrix.

    A matrix :math:`M` is involutory if it is its own inverse, ie :math:`M^2 = \mathbb{I}`,
    where :math:`\mathbb{I}` is the identity. This further implies that any odd power is
    :math:`M` itself, and any even power is :math:`\mathbb{I}`.

    Note:
        This class does not enforce that the matrix is Hermitian or involutory.
    """

    @abstractmethod
    def __init__(self, matrix: np.ndarray, targets: Optional[list[int]] = None):
        self._matrix = matrix
        self._targets = _validate_and_clone_single_qubit_target(targets)

    def _pow(self, power: int) -> Observable:
        if power % 2:
            return self
        return Identity(self._targets)

    @property
    def targets(self) -> tuple[int, ...]:
        return self._targets

    def apply(self, state: np.ndarray) -> np.ndarray:
        return multiply_matrix(state, self._matrix, self.measured_qubits)


class Hadamard(_InvolutoryMatrixObservable):
    """Hadamard observable

    Note:
        This observable refers to the same mathematical object as the gate operation
        of the same name, but is meant to be used differently; the observable is viewed
        as a Hermitian operator to be measured, while the gate is viewed as a unitary
        operator to evolve the state of the system.
    """

    def __init__(self, targets: Optional[list[int]] = None):
        super().__init__(np.array([[1, 1], [1, -1]]) / math.sqrt(2), targets)

    @property
    def is_standard(self) -> bool:
        return True

    @property
    def eigenvalues(self) -> np.ndarray:
        return pauli_eigenvalues(1)

    def fix_qubit(self, qubit: int) -> Observable:
        return Hadamard([qubit])

    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        if self._targets is None:
            return tuple(Hadamard._diagonalizing_gate([target]) for target in range(num_qubits))
        return (Hadamard._diagonalizing_gate(self._targets),)

    @staticmethod
    def _diagonalizing_gate(targets):
        return gate_operations.RotY(targets, -math.pi / 4)


class PauliX(_InvolutoryMatrixObservable):
    """Pauli-X observable

    Note:
        This observable refers to the same mathematical object as the gate operation
        of the same name, but is meant to be used differently; the observable is viewed
        as a Hermitian operator to be measured, while the gate is viewed as a unitary
        operator to evolve the state of the system.
    """

    def __init__(self, targets: Optional[list[int]] = None):
        super().__init__(np.array([[0, 1], [1, 0]]), targets)

    @property
    def is_standard(self) -> bool:
        return True

    @property
    def eigenvalues(self) -> np.ndarray:
        return pauli_eigenvalues(1)

    def fix_qubit(self, qubit: int) -> Observable:
        return PauliX([qubit])

    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        if self._targets is None:
            return tuple(PauliX._diagonalizing_gate([target]) for target in range(num_qubits))
        return (PauliX._diagonalizing_gate(self._targets),)

    @staticmethod
    def _diagonalizing_gate(targets):
        return gate_operations.Hadamard(targets)


class PauliY(_InvolutoryMatrixObservable):
    """Pauli-Y observable

    Note:
        This observable refers to the same mathematical object as the gate operation
        of the same name, but is meant to be used differently; the observable is viewed
        as a Hermitian operator to be measured, while the gate is viewed as a unitary
        operator to evolve the state of the system.
    """

    # HS^{\dagger}
    _diagonalizing_matrix = np.array([[1, -1j], [1, 1j]]) / math.sqrt(2)

    def __init__(self, targets: Optional[list[int]] = None):
        super().__init__(np.array([[0, -1j], [1j, 0]]), targets)

    @property
    def is_standard(self) -> bool:
        return True

    @property
    def eigenvalues(self) -> np.ndarray:
        return pauli_eigenvalues(1)

    def fix_qubit(self, qubit: int) -> Observable:
        return PauliY([qubit])

    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        if self._targets is None:
            return tuple(PauliY._diagonalizing_gate([target]) for target in range(num_qubits))
        return (PauliY._diagonalizing_gate(self._targets),)

    @staticmethod
    def _diagonalizing_gate(targets):
        return gate_operations.Unitary(targets, PauliY._diagonalizing_matrix)


class PauliZ(_InvolutoryMatrixObservable):
    """Pauli-Z observable

    Note:
        This observable refers to the same mathematical object as the gate operation
        of the same name, but is meant to be used differently; the observable is viewed
        as a Hermitian operator to be measured, while the gate is viewed as a unitary
        operator to evolve the state of the system.
    """

    def __init__(self, targets: Optional[list[int]] = None):
        super().__init__(np.array([[1, 0], [0, -1]]), targets)
        self._measured_qubits = self._targets

    @property
    def targets(self) -> tuple[int, ...]:
        return ()

    @property
    def measured_qubits(self):
        return self._measured_qubits

    @property
    def is_standard(self) -> bool:
        return True

    @property
    def eigenvalues(self) -> np.ndarray:
        return pauli_eigenvalues(1)

    def fix_qubit(self, qubit: int) -> Observable:
        return PauliZ([qubit])

    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        # Already diagonalized
        return ()


class Hermitian(Observable):
    """Arbitrary Hermitian observable"""

    # Cache of eigenpairs for each used Hermitian matrix
    _eigenpairs = {}

    def __init__(self, matrix: np.ndarray, targets: Optional[list[int]] = None):
        clone = np.array(matrix, dtype=complex)
        self._targets = tuple(targets) if targets else None
        if targets:
            check_matrix_dimensions(clone, self._targets)
        elif clone.shape != (2, 2):
            raise ValueError(
                f"Matrix must have shape (2, 2) if target is empty, but has shape {clone.shape}"
            )
        check_hermitian(clone)
        self._matrix = clone
        eigendecomposition = Hermitian._eigendecomposition(clone)
        self._eigenvalues = eigendecomposition["eigenvalues"]
        self._diagonalizing_matrix = eigendecomposition["eigenvectors"].conj().T

    def _pow(self, power: int) -> Observable:
        return Hermitian(np.linalg.matrix_power(self._matrix, power), self._targets)

    @property
    def matrix(self) -> np.ndarray:
        """np.ndarray: The Hermitian matrix defining the observable."""
        return np.array(self._matrix)

    @property
    def targets(self) -> tuple[int, ...]:
        return self._targets

    @property
    def eigenvalues(self) -> np.ndarray:
        return self._eigenvalues

    def apply(self, state: np.ndarray) -> np.ndarray:
        return multiply_matrix(state, self._matrix, self.measured_qubits)

    def fix_qubit(self, qubit: int) -> Observable:
        targets = self._targets
        matrix = self._matrix
        if targets and len(targets) > 1:
            raise ValueError(f"Matrix must act on 1 qubit, but {matrix} acts on {len(targets)}")
        return Hermitian(self._matrix, [qubit])

    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        if self._targets is None:
            return tuple(self._diagonalizing_gate([target]) for target in range(num_qubits))
        return (self._diagonalizing_gate(self._targets),)

    def _diagonalizing_gate(self, targets):
        return gate_operations.Unitary(targets, self._diagonalizing_matrix)

    @staticmethod
    def _eigendecomposition(matrix: np.ndarray) -> dict[str, np.ndarray]:
        """Decomposes the Hermitian matrix into its eigenvectors and associated eigenvalues.

        The eigendecomposition is cached so that if another Hermitian observable
        is created with the same matrix, the eigendecomposition doesn't have to
        be recalculated.

        Args:
            matrix (np.ndarray): The matrix to decompose

        Returns:
            dict[str, np.ndarray]: The keys are "eigenvectors", mapping to a matrix whose
            columns are the eigenvectors of the matrix, and "eigenvalues", a list of
            associated eigenvalues in the order their corresponding eigenvectors in the
            "eigenvectors" matrix
        """
        mat_key = tuple(matrix.flatten().tolist())
        if mat_key not in Hermitian._eigenpairs:
            eigenvalues, eigenvectors = np.linalg.eigh(matrix)
            Hermitian._eigenpairs[mat_key] = {
                "eigenvectors": eigenvectors,
                "eigenvalues": eigenvalues,
            }
        return Hermitian._eigenpairs[mat_key]


class TensorProduct(Observable):
    """
    Tensor product of multiple observables.
    """

    def __init__(self, factors: list[Observable]):
        """
        Args:
            factors (list[Observable]): The observables to combine together
                into a tensor product
        """
        if len(factors) < 2:
            raise ValueError("A tensor product should have at least 2 factors")
        self._targets = tuple(target for observable in factors for target in observable.targets)
        self._measured_qubits = tuple(
            qubit for observable in factors for qubit in observable.measured_qubits
        )
        self._eigenvalues = TensorProduct._compute_eigenvalues(factors, self._measured_qubits)
        self._factors = tuple(factors)

    def _pow(self, power: int) -> Observable:
        return TensorProduct([factor**power for factor in self._factors])

    @property
    def factors(self) -> tuple[Observable]:
        return self._factors

    @property
    def targets(self) -> tuple[int, ...]:
        return self._targets

    @property
    def measured_qubits(self) -> tuple[int, ...]:
        return self._measured_qubits

    @property
    def eigenvalues(self) -> np.ndarray:
        return self._eigenvalues

    def apply(self, state: np.ndarray) -> np.ndarray:
        final = np.array(state)
        for factor in self._factors:
            final = factor.apply(final)
        return final

    def fix_qubit(self, qubit: int) -> Observable:
        raise TypeError("Tensor product cannot be measured on single qubit")

    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        return sum((factor.diagonalizing_gates() for factor in self._factors), ())

    @staticmethod
    def _compute_eigenvalues(factors: list[Observable], qubits: tuple[int, ...]) -> np.ndarray:
        # Check if there are any non-standard observables, namely Hermitian and Identity
        if any({not observable.is_standard for observable in factors}):
            # Tensor product of observables contains a mixture
            # of standard and nonstandard observables
            factors_sorted = sorted(factors, key=lambda x: x.measured_qubits)
            eigenvalues = np.ones(1)
            for is_standard, group in itertools.groupby(factors_sorted, lambda x: x.is_standard):
                # Group observables by whether or not they are standard
                group_eigenvalues = (
                    # `group` contains only standard observables, so eigenvalues
                    # are simply Pauli eigenvalues
                    pauli_eigenvalues(len(list(group)))
                    if is_standard
                    # `group` contains only nonstandard observables, so eigenvalues
                    # must be calculated
                    else functools.reduce(
                        np.kron, tuple(nonstandard.eigenvalues for nonstandard in group)
                    )
                )
                eigenvalues = np.kron(eigenvalues, group_eigenvalues)
        else:
            eigenvalues = pauli_eigenvalues(len(qubits))

        return eigenvalues


def _validate_and_clone_single_qubit_target(
    targets: Optional[list[int]],
) -> Optional[tuple[int, ...]]:
    clone = tuple(targets) if targets else None
    if clone and len(clone) > 1:
        raise ValueError(f"Observable only acts on one qubit, but found {len(clone)}")
    return clone
