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
from __future__ import annotations

import functools
from typing import List, Tuple

import numpy as np
from braket.circuits.observable import Observable
from braket.circuits.quantum_operator_helpers import (
    is_hermitian,
    verify_quantum_operator_matrix_dimensions,
)


class H(Observable):
    """Hadamard operation as an observable."""

    def __init__(self):
        """
        Examples:
            >>> Observable.I()
        """
        super().__init__(qubit_count=1, ascii_symbols=["H"])

    def to_ir(self) -> List[str]:
        return ["h"]

    def to_matrix(self) -> np.ndarray:
        return 1.0 / np.sqrt(2.0) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)


Observable.register_observable(H)


class I(Observable):  # noqa: E742, E261
    """Identity operation as an observable."""

    def __init__(self):
        """
        Examples:
            >>> Observable.I()
        """
        super().__init__(qubit_count=1, ascii_symbols=["I"])

    def to_ir(self) -> List[str]:
        return ["i"]

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)


Observable.register_observable(I)


class X(Observable):
    """Pauli-X operation as an observable."""

    def __init__(self):
        """
        Examples:
            >>> Observable.X()
        """
        super().__init__(qubit_count=1, ascii_symbols=["X"])

    def to_ir(self) -> List[str]:
        return ["x"]

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)


Observable.register_observable(X)


class Y(Observable):
    """Pauli-Y operation as an observable."""

    def __init__(self):
        """
        Examples:
            >>> Observable.Y()
        """
        super().__init__(qubit_count=1, ascii_symbols=["Y"])

    def to_ir(self) -> List[str]:
        return ["y"]

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)


Observable.register_observable(Y)


class Z(Observable):
    """Pauli-Z operation as an observable."""

    def __init__(self):
        """
        Examples:
            >>> Observable.Z()
        """
        super().__init__(qubit_count=1, ascii_symbols=["Z"])

    def to_ir(self) -> List[str]:
        return ["z"]

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


Observable.register_observable(Z)


class TensorProduct(Observable):
    """Tensor product of observables"""

    def __init__(self, observables: List[Observable]):
        """
        Args:
            observables (List[Observable]): List of observables for tensor product

        Examples:
            >>> t1 = Observable.Y() @ Observable.X()
            >>> t1.to_matrix()
            array([[0.+0.j, 0.+0.j, 0.-0.j, 0.-1.j],
            [0.+0.j, 0.+0.j, 0.-1.j, 0.-0.j],
            [0.+0.j, 0.+1.j, 0.+0.j, 0.+0.j],
            [0.+1.j, 0.+0.j, 0.+0.j, 0.+0.j]])
            >>> t2 = Observable.Z() @ t1
            >>> t2.observables
            (Z('qubit_count': 1), Y('qubit_count': 1), X('qubit_count': 1))

        Note: list of observables for tensor product must be given in the desired order that
        the tensor product will be calculated. For `TensorProduct(observables=[ob1, ob2, ob3])`,
        the tensor product's matrix will be the result of the tensor product of `ob1`, `ob2`,
        `ob3`, or `np.kron(np.kron(ob1.to_matrix(), ob2.to_matrix()), ob3.to_matrix())`
        """
        self._observables = tuple(observables)
        qubit_count = sum([obs.qubit_count for obs in observables])
        display_name = "@".join([obs.ascii_symbols[0] for obs in observables])
        super().__init__(qubit_count=qubit_count, ascii_symbols=[display_name] * qubit_count)

    def to_ir(self) -> List[str]:
        ir = []
        for obs in self.observables:
            ir.extend(obs.to_ir())
        return ir

    @property
    def observables(self) -> Tuple[Observable]:
        """Tuple[Observable]: observables part of tensor product"""
        return self._observables

    def to_matrix(self) -> np.ndarray:
        return functools.reduce(np.kron, [obs.to_matrix() for obs in self.observables])

    def __matmul__(self, other):
        if isinstance(other, TensorProduct):
            return TensorProduct(list(self.observables) + list(other.observables))

        if isinstance(other, Observable):
            return TensorProduct(list(self.observables) + [other])

        raise ValueError("Can only perform tensor products between observables.")

    def __rmatmul__(self, other):
        if isinstance(other, Observable):
            return TensorProduct([other] + list(self.observables))

        raise ValueError("Can only perform tensor products between observables.")

    def __repr__(self):
        return "TensorProduct(" + ", ".join([repr(o) for o in self.observables]) + ")"

    def __eq__(self, other):
        return self.matrix_equivalence(other)


Observable.register_observable(TensorProduct)


class Hermitian(Observable):
    """Hermitian matrix as an observable."""

    def __init__(self, matrix: np.ndarray, display_name: str = "Hermitian"):
        """
        Args:
            matrix (numpy.ndarray): Hermitian matrix which defines the observable.
            display_name (str): Name to be used for an instance of this Hermitian matrix
                observable for circuit diagrams. Defaults to `Hermitian`.

        Raises:
            ValueError: If `matrix` is not a two-dimensional square matrix,
                or has a dimension length which is not a positive exponent of 2,
                or is non-hermitian.

        Example:
            >>> Observable.Hermitian(matrix=np.array([[0, 1],[1, 0]]))
        """
        verify_quantum_operator_matrix_dimensions(matrix)
        self._matrix = np.array(matrix, dtype=complex)
        qubit_count = int(np.log2(self._matrix.shape[0]))

        if not is_hermitian(self._matrix):
            raise ValueError(f"{self._matrix} is not hermitian")

        super().__init__(qubit_count=qubit_count, ascii_symbols=[display_name] * qubit_count)

    def to_ir(self) -> List[List[List[List[float]]]]:
        return [
            [[[element.real, element.imag] for element in row] for row in self._matrix.tolist()]
        ]

    def to_matrix(self) -> np.ndarray:
        return self._matrix

    def __eq__(self, other) -> bool:
        return self.matrix_equivalence(other)


Observable.register_observable(Hermitian)
