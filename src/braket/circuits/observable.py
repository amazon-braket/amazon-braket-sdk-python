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

from typing import List, Sequence, Tuple, Union

import numpy as np

from braket.circuits.gate import Gate
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.qubit_set import QubitSet
from braket.circuits.serialization import IRType


class Observable(QuantumOperator):
    """
    Class `Observable` to represent a quantum observable.

    Objects of this type can be used as input to `ResultType.Sample`, `ResultType.Variance`,
    `ResultType.Expectation` to specify the measurement basis.
    """

    def __init__(self, qubit_count: int, ascii_symbols: Sequence[str]):
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    def to_ir(
        self,
        target: QubitSet = None,
        ir_type: IRType = IRType.JAQCD,
        qubit_reference_format: str = "${}",
    ) -> Union[str, List[Union[str, List[List[List[float]]]]]]:
        """Returns the IR representation for the observable

        Args:
            target (QubitSet): target qubit(s). Defaults to None.
            ir_type(IRType) : The IRType to use for converting the result type object to its
                IR representation. Defaults to IRType.JAQCD.
            qubit_reference_format (str): The string format to use for referencing the qubits
                within the gate. Defaults to "${}" for referencing qubits physically.

        Returns:
            Union[str, List[Union[str, List[List[List[float]]]]]]: The IR representation for
            the observable.

        Raises:
            ValueError: If the supplied `ir_type` is not supported.
        """
        if ir_type == IRType.JAQCD:
            return self.to_jaqcd()
        elif ir_type == IRType.OPENQASM:
            return self.to_openqasm(qubit_reference_format, target)
        else:
            raise ValueError(f"Supplied ir_type {ir_type} is not supported.")

    def to_jaqcd(self) -> List[Union[str, List[List[List[float]]]]]:
        """Returns the JAQCD representation of the observable."""
        raise NotImplementedError("to_jaqcd has not been implemented yet.")

    def to_openqasm(self, qubit_reference_format: str, target: QubitSet = None) -> str:
        """
        Returns the openqasm string representation of the result type.

        Args:
            qubit_reference_format(str): The string format to use for referencing the qubits
                within the gate.
            target (QubitSet): target qubit(s). Defaults to None.

        Returns:
            str: Representing the openqasm representation of the result type.
        """
        raise NotImplementedError("to_openqasm has not been implemented yet.")

    @property
    def basis_rotation_gates(self) -> Tuple[Gate, ...]:
        """Tuple[Gate]: Returns the basis rotation gates for this observable."""
        raise NotImplementedError

    @property
    def eigenvalues(self) -> np.ndarray:
        """np.ndarray: Returns the eigenvalues of this observable."""
        raise NotImplementedError

    def eigenvalue(self, index: int) -> float:
        """Returns the the eigenvalue of this observable at the given index.

        The eigenvalues are ordered by their corresponding computational basis state
        after diagonalization.

        Args:
            index: The index of the desired eigenvalue

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

    @property
    def eigenvalues(self) -> np.ndarray:
        return np.array(self._eigenvalues)

    def eigenvalue(self, index: int) -> float:
        return self._eigenvalues[index]
