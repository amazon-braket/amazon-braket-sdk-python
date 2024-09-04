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

from __future__ import annotations

import functools
import itertools
import math
import numbers
from copy import deepcopy
from typing import ClassVar

import numpy as np

from braket.circuits.gate import Gate
from braket.circuits.observable import Observable, StandardObservable
from braket.circuits.quantum_operator_helpers import (
    get_pauli_eigenvalues,
    is_hermitian,
    verify_quantum_operator_matrix_dimensions,
)
from braket.circuits.serialization import IRType, OpenQASMSerializationProperties
from braket.registers import QubitInput, QubitSet, QubitSetInput


class H(StandardObservable):
    """Hadamard operation as an observable."""

    def __init__(self, target: QubitInput | None = None):
        """Initializes Hadamard observable.

        Args:
            target (QubitInput | None): The target qubit to measure the observable on.
                If not provided, this needs to be provided from the enclosing result type.
                Default: `None`.

        Examples:
            >>> observables.H(0)
            >>> observables.H()
        """
        super().__init__(ascii_symbols=["H"], target=target)

    def _unscaled(self) -> StandardObservable:
        return H(self._targets)

    def _to_jaqcd(self) -> list[str]:
        if self.coefficient != 1:
            raise ValueError("Observable coefficients not supported with Jaqcd")
        return ["h"]

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        coef_prefix = f"{self.coefficient} * " if self.coefficient != 1 else ""
        targets = target or self._targets
        qubit_target = int(targets[0]) if targets else None
        if qubit_target is not None:
            return f"{coef_prefix}h({serialization_properties.format_target(qubit_target)})"
        return f"{coef_prefix}h all"

    def to_matrix(self) -> np.ndarray:
        return self.coefficient * (
            1.0 / np.sqrt(2.0) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)
        )

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        return (Gate.Ry(-math.pi / 4),)


Observable.register_observable(H)


class I(Observable):  # noqa: E742
    """Identity operation as an observable."""

    def __init__(self, target: QubitInput | None = None):
        """Initializes Identity observable.

        Args:
            target (QubitInput | None): The target qubit to measure the observable on.
                If not provided, this needs to be provided from the enclosing result type.
                Default: `None`.

        Examples:
            >>> observables.I(0)
            >>> observables.I()
        """
        super().__init__(qubit_count=1, ascii_symbols=["I"], targets=target)

    def _unscaled(self) -> Observable:
        return I(self._targets)

    def _to_jaqcd(self) -> list[str]:
        if self.coefficient != 1:
            raise ValueError("Observable coefficients not supported with Jaqcd")
        return ["i"]

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        coef_prefix = f"{self.coefficient} * " if self.coefficient != 1 else ""

        targets = target or self._targets
        qubit_target = int(targets[0]) if targets else None
        if qubit_target is not None:
            return f"{coef_prefix}i({serialization_properties.format_target(qubit_target)})"
        return f"{coef_prefix}i all"

    def to_matrix(self) -> np.ndarray:
        return self.coefficient * np.eye(2, dtype=complex)

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        return ()

    @property
    def eigenvalues(self) -> np.ndarray:
        """Returns the eigenvalues of this observable.

        Returns:
            np.ndarray: The eigenvalues of this observable.
        """
        return self.coefficient * np.ones(2)

    def eigenvalue(self, index: int) -> float:
        return self.coefficient * 1.0


Observable.register_observable(I)


class X(StandardObservable):
    """Pauli-X operation as an observable."""

    def __init__(self, target: QubitInput | None = None):
        """Initializes Pauli-X observable.

        Args:
            target (QubitInput | None): The target qubit to measure the observable on.
                If not provided, this needs to be provided from the enclosing result type.
                Default: `None`.

        Examples:
            >>> observables.X(0)
            >>> observables.X()
        """
        super().__init__(ascii_symbols=["X"], target=target)

    def _unscaled(self) -> StandardObservable:
        return X(self._targets)

    def _to_jaqcd(self) -> list[str]:
        if self.coefficient != 1:
            raise ValueError("Observable coefficients not supported with Jaqcd")
        return ["x"]

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        coef_prefix = f"{self.coefficient} * " if self.coefficient != 1 else ""

        targets = target or self._targets
        qubit_target = int(targets[0]) if targets else None
        if qubit_target is not None:
            return f"{coef_prefix}x({serialization_properties.format_target(qubit_target)})"
        return f"{coef_prefix}x all"

    def to_matrix(self) -> np.ndarray:
        return self.coefficient * np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        return (Gate.H(),)


Observable.register_observable(X)


class Y(StandardObservable):
    """Pauli-Y operation as an observable."""

    def __init__(self, target: QubitInput | None = None):
        """Initializes Pauli-Y observable.

        Args:
            target (QubitInput | None): The target qubit to measure the observable on.
                If not provided, this needs to be provided from the enclosing result type.
                Default: `None`.

        Examples:
            >>> observables.Y(0)
            >>> observables.Y()
        """
        super().__init__(ascii_symbols=["Y"], target=target)

    def _unscaled(self) -> StandardObservable:
        return Y(self._targets)

    def _to_jaqcd(self) -> list[str]:
        if self.coefficient != 1:
            raise ValueError("Observable coefficients not supported with Jaqcd")
        return ["y"]

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        coef_prefix = f"{self.coefficient} * " if self.coefficient != 1 else ""
        targets = target or self._targets
        qubit_target = int(targets[0]) if targets else None
        if qubit_target is not None:
            return f"{coef_prefix}y({serialization_properties.format_target(qubit_target)})"
        return f"{coef_prefix}y all"

    def to_matrix(self) -> np.ndarray:
        return self.coefficient * np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        return Gate.Z(), Gate.S(), Gate.H()


Observable.register_observable(Y)


class Z(StandardObservable):
    """Pauli-Z operation as an observable."""

    def __init__(self, target: QubitInput | None = None):
        """Initializes Pauli-Z observable.

        Args:
            target (QubitInput | None): The target qubit to measure the observable on.
                If not provided, this needs to be provided from the enclosing result type.
                Default: `None`.

        Examples:
            >>> observables.Z(0)
            >>> observables.Z()
        """
        super().__init__(ascii_symbols=["Z"], target=target)

    def _unscaled(self) -> StandardObservable:
        return Z(self._targets)

    def _to_jaqcd(self) -> list[str]:
        if self.coefficient != 1:
            raise ValueError("Observable coefficients not supported with Jaqcd")
        return ["z"]

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        coef_prefix = f"{self.coefficient} * " if self.coefficient != 1 else ""
        targets = target or self._targets
        qubit_target = int(targets[0]) if targets else None
        if qubit_target is not None:
            return f"{coef_prefix}z({serialization_properties.format_target(qubit_target)})"
        return f"{coef_prefix}z all"

    def to_matrix(self) -> np.ndarray:
        return self.coefficient * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        return ()


Observable.register_observable(Z)


class TensorProduct(Observable):
    """Tensor product of observables"""

    def __init__(self, observables: list[Observable]):
        """Initializes a `TensorProduct`.

        Args:
            observables (list[Observable]): List of observables for tensor product

        Examples:
            >>> t1 = Observable.Y(0) @ Observable.X(1)
            >>> t1.to_matrix()
            array([[0.+0.j, 0.+0.j, 0.-0.j, 0.-1.j],
            [0.+0.j, 0.+0.j, 0.-1.j, 0.-0.j],
            [0.+0.j, 0.+1.j, 0.+0.j, 0.+0.j],
            [0.+1.j, 0.+0.j, 0.+0.j, 0.+0.j]])
            >>> t2 = Observable.Z(3) @ t1
            >>> t2.factors
            (Z('qubit_count': 1), Y('qubit_count': 1), X('qubit_count': 1))

        Note: You must provide the list of observables for the tensor product to be evaluated
        in the order that you want the tensor product to be calculated.
        For `TensorProduct(observables=[ob1, ob2, ob3])`, the tensor product's matrix is the
        result of the tensor product of `ob1`, `ob2`, `ob3`, or `np.kron(np.kron(ob1.to_matrix(),
        ob2.to_matrix()), ob3.to_matrix())`.
        """
        flattened_observables = []
        for obs in observables:
            if isinstance(obs, TensorProduct):
                flattened_observables.extend(iter(obs.factors))
                # make sure you don't lose coefficient of tensor product
                flattened_observables[-1] *= obs.coefficient
            elif isinstance(obs, Sum):
                raise TypeError("Sum observables not allowed in TensorProduct")
            else:
                flattened_observables.append(obs)
        qubit_count = sum(obs.qubit_count for obs in flattened_observables)
        # aggregate all coefficients for the product, since aX @ bY == ab * X @ Y
        coefficient = np.prod([obs.coefficient for obs in flattened_observables])
        unscaled_factors = tuple(obs._unscaled() for obs in flattened_observables)
        display_name = (
            f"{coefficient if coefficient != 1 else ''}"
            f"{'@'.join([obs.ascii_symbols[0] for obs in unscaled_factors])}"
        )
        all_targets = [factor.targets for factor in unscaled_factors]
        if not any(all_targets):
            merged_targets = QubitSet()
        elif all(all_targets):
            flat_targets = [qubit for target in all_targets for qubit in target]
            merged_targets = QubitSet(flat_targets)
            if len(merged_targets) != len(flat_targets):
                raise ValueError("Cannot have repeated target qubits")
        else:
            raise ValueError("Cannot mix factors with and without targets")

        super().__init__(
            qubit_count=qubit_count,
            ascii_symbols=[display_name] * qubit_count,
            targets=merged_targets,
        )
        self._coef = coefficient
        self._factors = unscaled_factors
        self._factor_dimensions = tuple(
            len(factor.to_matrix()) for factor in reversed(self._factors)
        )
        self._eigenvalue_indices = {}
        self._all_eigenvalues = None

    @property
    def ascii_symbols(self) -> tuple[str, ...]:
        return tuple(
            f"{self.coefficient if self.coefficient != 1 else ''}"
            f"{'@'.join([obs.ascii_symbols[0] for obs in self.factors])}"
            for _ in range(self.qubit_count)
        )

    def _unscaled(self) -> Observable:
        copied = TensorProduct(observables=self.factors)
        copied._coef = 1
        return copied

    def _to_jaqcd(self) -> list[str]:
        if self.coefficient != 1:
            raise ValueError("Observable coefficients not supported with Jaqcd")
        ir = []
        for obs in self.factors:
            ir.extend(obs.to_ir())
        return ir

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        coef_prefix = f"{self.coefficient} * " if self.coefficient != 1 else ""
        factors = []
        use_qubits = iter(target or self._targets)
        for obs in self._factors:
            obs_target = QubitSet()
            num_qubits = int(np.log2(obs.to_matrix().shape[0]))
            for _ in range(num_qubits):
                obs_target.add(next(use_qubits))
            factors.append(
                obs.to_ir(
                    target=obs_target,
                    ir_type=IRType.OPENQASM,
                    serialization_properties=serialization_properties,
                )
            )
        return f"{coef_prefix}{' @ '.join(factors)}"

    @property
    def factors(self) -> tuple[Observable, ...]:
        """tuple[Observable]: The observables that comprise this tensor product."""
        return self._factors

    def to_matrix(self) -> np.ndarray:
        return self.coefficient * functools.reduce(
            np.kron, [obs.to_matrix() for obs in self.factors]
        )

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        """Returns the basis rotation gates for this observable.

        Returns:
            tuple[Gate, ...]: The basis rotation gates for this observable.
        """
        gates = []
        for obs in self.factors:
            gates.extend(obs.basis_rotation_gates)
        return tuple(gates)

    @property
    def eigenvalues(self) -> np.ndarray:
        """Returns the eigenvalues of this observable.

        Returns:
            np.ndarray: The eigenvalues of this observable.
        """
        if self._all_eigenvalues is None:
            self._all_eigenvalues = TensorProduct._compute_eigenvalues(
                self._factors, self.qubit_count
            )
        return self.coefficient * self._all_eigenvalues

    def eigenvalue(self, index: int) -> float:
        """Returns the eigenvalue of this observable at the given index.

        The eigenvalues are ordered by their corresponding computational basis state
        after diagonalization.

        Args:
            index (int): The index of the desired eigenvalue

        Returns:
            float: The `index` th eigenvalue of the observable.
        """
        if index in self._eigenvalue_indices:
            return self._eigenvalue_indices[index]
        dimension = 2**self.qubit_count
        if index >= dimension:
            raise ValueError(
                f"Index {index} requested but observable has at most {dimension} eigenvalues"
            )
        # Calculating the eigenvalue amounts to converting the index to a new heterogeneous base
        # and multiplying the eigenvalues of each factor at the corresponding digit
        product = 1
        quotient = index
        for i in range(len(self._factors)):
            quotient, remainder = divmod(quotient, self._factor_dimensions[i])
            product *= self._factors[-i - 1].eigenvalue(remainder)
        self._eigenvalue_indices[index] = product
        return self.coefficient * self._eigenvalue_indices[index]

    def __repr__(self):
        return "TensorProduct(" + ", ".join([repr(o) for o in self.factors]) + ")"

    def __eq__(self, other: TensorProduct):
        return self.matrix_equivalence(other)

    @staticmethod
    def _compute_eigenvalues(observables: tuple[Observable], num_qubits: int) -> np.ndarray:
        if False in [isinstance(observable, StandardObservable) for observable in observables]:
            # Tensor product of observables contains a mixture
            # of standard and non-standard observables
            eigenvalues = np.array([1])
            for k, g in itertools.groupby(observables, lambda x: isinstance(x, StandardObservable)):
                if k:
                    # Subgroup g contains only standard observables.
                    eigenvalues = np.kron(eigenvalues, get_pauli_eigenvalues(len(list(g))))
                else:
                    # Subgroup g contains only non-standard observables.
                    for nonstandard in g:
                        # loop through all non-standard observables
                        eigenvalues = np.kron(eigenvalues, nonstandard.eigenvalues)
        else:
            eigenvalues = get_pauli_eigenvalues(num_qubits=num_qubits)

        eigenvalues.setflags(write=False)
        return eigenvalues


Observable.register_observable(TensorProduct)


class Sum(Observable):
    """Sum of observables"""

    def __init__(self, observables: list[Observable], display_name: str = "Hamiltonian"):
        """Inits a `Sum`.

        Args:
            observables (list[Observable]): List of observables for Sum
            display_name (str): Name to use for an instance of this Sum
                observable for circuit diagrams. Defaults to `Hamiltonian`.

        Examples:
            >>> t1 = -3 * Observable.Y(0) + 2 * Observable.X(0)
            Sum(X('qubit_count': 1), Y('qubit_count': 1))
            >>> t1.summands
            (X('qubit_count': 1), Y('qubit_count': 1))
        """
        flattened_observables = []
        for obs in observables:
            if isinstance(obs, Sum):
                flattened_observables.extend(iter(obs.summands))
            else:
                flattened_observables.append(obs)

        self._summands = tuple(flattened_observables)
        qubit_count = max(flattened_observables, key=lambda obs: obs.qubit_count).qubit_count
        all_targets = [observable.targets for observable in flattened_observables]
        if not any(all_targets):
            targets = QubitSet()
        elif all(all_targets):
            targets = all_targets
        else:
            raise ValueError("Cannot mix terms with and without targets")
        super().__init__(qubit_count=qubit_count, ascii_symbols=[display_name] * qubit_count)
        self._targets = targets

    def __mul__(self, other: numbers.Number) -> Observable:
        """Scalar multiplication"""
        if isinstance(other, numbers.Number):
            sum_copy = deepcopy(self)
            for i, _obs in enumerate(sum_copy.summands):
                sum_copy._summands[i]._coef *= other
            return sum_copy
        raise TypeError("Observable coefficients must be numbers.")

    def _to_jaqcd(self) -> list[str]:
        raise NotImplementedError("Sum Observable is not supported in Jaqcd")

    def _to_openqasm(
        self,
        serialization_properties: OpenQASMSerializationProperties,
        target: list[QubitSetInput] | None = None,
    ) -> str:
        target = target or self._targets
        if len(self.summands) != len(target):
            raise ValueError(
                f"Invalid target of length {len(target)} for Sum with {len(self.summands)} terms"
            )
        for i, (term, term_target) in enumerate(zip(self.summands, target)):
            if term.qubit_count != len(term_target):
                raise ValueError(
                    f"Invalid target for term {i} of Sum. "
                    f"Expected {term.qubit_count} targets, got {len(term_target)}"
                )
        return " + ".join(
            obs.to_ir(
                target=term_target,
                ir_type=IRType.OPENQASM,
                serialization_properties=serialization_properties,
            )
            for obs, term_target in zip(self.summands, target)
        ).replace("+ -", "- ")

    @property
    def summands(self) -> tuple[Observable, ...]:
        """tuple[Observable]: The observables that comprise this sum."""
        return self._summands

    def to_matrix(self) -> np.ndarray:
        raise NotImplementedError("Matrix operation is not supported for Sum")

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        raise NotImplementedError("Basis rotation calculation not supported for Sum")

    @property
    def eigenvalues(self) -> np.ndarray:
        raise NotImplementedError("Eigenvalue calculation not supported for Sum")

    def eigenvalue(self, index: int) -> float:
        raise NotImplementedError("Eigenvalue calculation not supported for Sum")

    def __repr__(self):
        return "Sum(" + ", ".join([repr(o) for o in self.summands]) + ")"

    def __eq__(self, other: Sum):
        return repr(self) == repr(other)

    @staticmethod
    def _compute_eigenvalues(observables: tuple[Observable], num_qubits: int) -> np.ndarray:
        raise NotImplementedError("Eigenvalue calculation not supported for Sum")


Observable.register_observable(Sum)


class Hermitian(Observable):
    """Hermitian matrix as an observable."""

    # Cache of eigenpairs
    _eigenpairs: ClassVar = {}

    def __init__(
        self,
        matrix: np.ndarray,
        display_name: str = "Hermitian",
        targets: QubitSetInput | None = None,
    ):
        """Inits a `Hermitian`.

        Args:
            matrix (np.ndarray): Hermitian matrix that defines the observable.
            display_name (str): Name to use for an instance of this Hermitian matrix
                observable for circuit diagrams. Defaults to `Hermitian`.
            targets (QubitSetInput | None): The target qubits to measure the observable on.
                If not provided, this needs to be provided from the enclosing result type.
                Default: `None`.

        Raises:
            ValueError: If `matrix` is not a two-dimensional square matrix,
                is not Hermitian, or has a dimension length that is either not a positive power of 2
                or, if targets is supplied, doesn't match the size of targets.

        Examples:
            >>> observables.Hermitian(matrix=np.array([[0, 1], [1, 0]]), targets=[0])
            >>> observables.Hermitian(matrix=np.array([[0, 1], [1, 0]]))
        """
        verify_quantum_operator_matrix_dimensions(matrix)
        self._matrix = np.array(matrix, dtype=complex)
        if not is_hermitian(self._matrix):
            raise ValueError(f"{self._matrix} is not hermitian")

        qubit_count = int(np.log2(self._matrix.shape[0]))
        eigendecomposition = Hermitian._get_eigendecomposition(self._matrix)
        self._eigenvalues = eigendecomposition["eigenvalues"]
        self._diagonalizing_gates = (
            Gate.Unitary(matrix=eigendecomposition["eigenvectors"].conj().T),
        )

        super().__init__(
            qubit_count=qubit_count, ascii_symbols=[display_name] * qubit_count, targets=targets
        )

    def _unscaled(self) -> Observable:
        return Hermitian(
            matrix=self._matrix, display_name=self.ascii_symbols[0], targets=self._targets
        )

    def _to_jaqcd(self) -> list[list[list[list[float]]]]:
        if self.coefficient != 1:
            raise ValueError("Observable coefficients not supported with Jaqcd")
        return [
            [[[element.real, element.imag] for element in row] for row in self._matrix.tolist()]
        ]

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        coef_prefix = f"{self.coefficient} * " if self.coefficient != 1 else ""
        target = target or self._targets
        if target:
            qubit_target = ", ".join([
                serialization_properties.format_target(int(t)) for t in target
            ])
            return (
                f"{coef_prefix}"
                f"hermitian({self._serialized_matrix_openqasm_matrix()}) {qubit_target}"
            )
        return f"{coef_prefix}hermitian({self._serialized_matrix_openqasm_matrix()}) all"

    def _serialized_matrix_openqasm_matrix(self) -> str:
        serialized = str([[f"{complex(elem)}" for elem in row] for row in self._matrix.tolist()])
        for replacements in [("(", ""), (")", ""), ("'", ""), ("j", "im")]:
            serialized = serialized.replace(replacements[0], replacements[1])
        return serialized

    def to_matrix(self) -> np.ndarray:
        return self.coefficient * self._matrix

    def __eq__(self, other: Hermitian) -> bool:
        return self.matrix_equivalence(other)

    @property
    def basis_rotation_gates(self) -> tuple[Gate, ...]:
        return self._diagonalizing_gates

    @property
    def eigenvalues(self) -> np.ndarray:
        """Returns the eigenvalues of this observable.

        Returns:
            np.ndarray: The eigenvalues of this observable.
        """
        return self._eigenvalues

    def eigenvalue(self, index: int) -> float:
        return self._eigenvalues[index]

    @staticmethod
    def _get_eigendecomposition(matrix: np.ndarray) -> dict[str, np.ndarray]:
        """Decomposes the Hermitian matrix into its eigenvectors and associated eigenvalues.
        The eigendecomposition is cached so that if another Hermitian observable
        is created with the same matrix, the eigendecomposition doesn't have to
        be recalculated.

        Args:
            matrix (ndarray): The Hermitian matrix.

        Returns:
            dict[str, ndarray]: The keys are "eigenvectors_conj_t", mapping to the
            conjugate transpose of a matrix whose columns are the eigenvectors of the matrix,
            and "eigenvalues", a list of associated eigenvalues in the order of their
            corresponding eigenvectors in the "eigenvectors" matrix. These cached values
            are immutable.
        """
        mat_key = tuple(matrix.flatten().tolist())
        if mat_key not in Hermitian._eigenpairs:
            eigenvalues, eigenvectors = np.linalg.eigh(matrix)
            eigenvalues.setflags(write=False)
            Hermitian._eigenpairs[mat_key] = {
                "eigenvectors": eigenvectors,
                "eigenvalues": eigenvalues,
            }
        return Hermitian._eigenpairs[mat_key]

    def __repr__(self):
        matrix_str = np.array2string(self.to_matrix()).replace("\n", ",")
        return f"{self.name}('qubit_count': {self.qubit_count}, 'matrix': {matrix_str})"


Observable.register_observable(Hermitian)


def observable_from_ir(ir_observable: list[str | list[list[list[float]]]]) -> Observable:
    """Create an observable from the IR observable list. This can be a tensor product of
    observables or a single observable.

    Args:
        ir_observable (list[Union[str, list[list[list[float]]]]]): observable as defined in IR

    Returns:
        Observable: observable object
    """
    if len(ir_observable) == 1:
        return _observable_from_ir_list_item(ir_observable[0])
    return TensorProduct([_observable_from_ir_list_item(obs) for obs in ir_observable])


def _observable_from_ir_list_item(observable: str | list[list[list[float]]]) -> Observable:
    if observable == "i":
        return I()
    if observable == "h":
        return H()
    if observable == "x":
        return X()
    if observable == "y":
        return Y()
    if observable == "z":
        return Z()
    try:
        matrix = np.array([
            [complex(element[0], element[1]) for element in row] for row in observable
        ])
        return Hermitian(matrix)
    except Exception as e:
        raise ValueError(f"Invalid observable specified: {observable} error: {e}") from e
