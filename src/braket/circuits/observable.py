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

import numbers
from copy import deepcopy
from typing import List, Sequence, Tuple, Union

import numpy as np

from braket.circuits.gate import Gate
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.qubit_set import QubitSet
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    SerializationProperties,
)


class Observable(QuantumOperator):
    """
    Class `Observable` to represent a quantum observable.

    Objects of this type can be used as input to `ResultType.Sample`, `ResultType.Variance`,
    `ResultType.Expectation` to specify the measurement basis.
    """

    def __init__(self, qubit_count: int, ascii_symbols: Sequence[str]):
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        self._coef = 1

    def _unscaled(self):
        return Observable(qubit_count=self.qubit_count, ascii_symbols=self.ascii_symbols)

    def to_ir(
        self,
        target: QubitSet = None,
        ir_type: IRType = IRType.JAQCD,
        serialization_properties: SerializationProperties = None,
    ) -> Union[str, List[Union[str, List[List[List[float]]]]]]:
        """Returns the IR representation for the observable

        Args:
            target (QubitSet): target qubit(s). Defaults to None.
            ir_type(IRType) : The IRType to use for converting the result type object to its
                IR representation. Defaults to IRType.JAQCD.
            serialization_properties (SerializationProperties): The serialization properties to use
                while serializing the object to the IR representation. The serialization properties
                supplied must correspond to the supplied `ir_type`. Defaults to None.

        Returns:
            Union[str, List[Union[str, List[List[List[float]]]]]]: The IR representation for
            the observable.

        Raises:
            ValueError: If the supplied `ir_type` is not supported, or if the supplied serialization
            properties don't correspond to the `ir_type`.
        """
        if ir_type == IRType.JAQCD:
            return self._to_jaqcd()
        elif ir_type == IRType.OPENQASM:
            if serialization_properties and not isinstance(
                serialization_properties, OpenQASMSerializationProperties
            ):
                raise ValueError(
                    "serialization_properties must be of type OpenQASMSerializationProperties "
                    "for IRType.OPENQASM."
                )
            return self._to_openqasm(
                serialization_properties or OpenQASMSerializationProperties(), target
            )
        else:
            raise ValueError(f"Supplied ir_type {ir_type} is not supported.")

    def _to_jaqcd(self) -> List[Union[str, List[List[List[float]]]]]:
        """Returns the JAQCD representation of the observable."""
        raise NotImplementedError("to_jaqcd has not been implemented yet.")

    def _to_openqasm(
        self, serialization_properties: OpenQASMSerializationProperties, target: QubitSet = None
    ) -> str:
        """
        Returns the openqasm string representation of the result type.

        Args:
            serialization_properties (OpenQASMSerializationProperties): The serialization properties
                to use while serializing the object to the IR representation.
            target (QubitSet): target qubit(s). Defaults to None.

        Returns:
            str: Representing the openqasm representation of the result type.
        """
        raise NotImplementedError("to_openqasm has not been implemented yet.")

    @property
    def coefficient(self):
        return self._coef

    @property
    def basis_rotation_gates(self) -> Tuple[Gate, ...]:
        """Returns the basis rotation gates for this observable.
        Returns:
            Tuple[Gate, ...]: The basis rotation gates for this observable.
        """
        raise NotImplementedError

    @property
    def eigenvalues(self) -> np.ndarray:
        """Returns the eigenvalues of this observable.
        Returns:
            ndarray: The eigenvalues of this observable.
        """
        raise NotImplementedError

    def eigenvalue(self, index: int) -> float:
        """Returns the eigenvalue of this observable at the given index.

        The eigenvalues are ordered by their corresponding computational basis state
        after diagonalization.

        Args:
            index (int): The index of the desired eigenvalue

        Returns:
            float: The `index`th eigenvalue of the observable.
        """
        raise NotImplementedError

    @classmethod
    def register_observable(cls, observable: Observable) -> None:
        """Register an observable implementation by adding it into the `Observable` class.

        Args:
            observable (Observable): Observable class to register.
        """
        setattr(cls, observable.__name__, observable)

    def __matmul__(self, other) -> Observable.TensorProduct:
        if isinstance(other, Observable):
            return Observable.TensorProduct([self, other])

        raise ValueError("Can only perform tensor products between observables.")

    def __mul__(self, other) -> Observable:
        """Scalar multiplication"""
        if isinstance(other, numbers.Number):
            observable_copy = deepcopy(self)
            observable_copy._coef *= other
            return observable_copy
        raise TypeError("Observable coefficients must be numbers.")

    def __rmul__(self, other) -> Observable:
        return self * other

    def __add__(self, other):
        if not isinstance(other, Observable):
            raise ValueError("Can only perform addition between observables.")

        return Observable.Sum([self, other])

    def __sub__(self, other):
        if not isinstance(other, Observable):
            raise ValueError("Can only perform subtraction between observables.")

        return self + (-1 * other)

    def __repr__(self) -> str:
        return f"{self.name}('qubit_count': {self.qubit_count})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Observable):
            return self.name == other.name
        return NotImplemented


class StandardObservable(Observable):
    """
    Class `StandardObservable` to represent a Pauli-like quantum observable with
    eigenvalues of (+1, -1).
    """

    def __init__(self, ascii_symbols: Sequence[str]):
        super().__init__(qubit_count=1, ascii_symbols=ascii_symbols)
        self._eigenvalues = (1.0, -1.0)  # immutable

    def _unscaled(self):
        return StandardObservable(ascii_symbols=self.ascii_symbols)

    @property
    def eigenvalues(self) -> np.ndarray:
        return self.coefficient * np.array(self._eigenvalues)

    def eigenvalue(self, index: int) -> float:
        return self.coefficient * self._eigenvalues[index]

    @property
    def ascii_symbols(self) -> Tuple[str, ...]:
        return tuple(
            f"{self.coefficient if self.coefficient != 1 else ''}{ascii_symbol}"
            for ascii_symbol in self._ascii_symbols
        )
