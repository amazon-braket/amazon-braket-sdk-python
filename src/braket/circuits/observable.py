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

from typing import List, Sequence, Union

from braket.circuits.quantum_operator import QuantumOperator


class Observable(QuantumOperator):
    """
    Class `Observable` to represent a quantum observable.

    Objects of this type can be used as input to `ResultType.Sample`, `ResultType.Variance`,
    `ResultType.Expectation` to specify the measurement basis.
    """

    def __init__(self, qubit_count: int, ascii_symbols: Sequence[str]):
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    def to_ir(self) -> List[Union[str, List[List[List[float]]]]]:
        """List[Union[str, List[List[List[float]]]]]: Returns the IR
            representation for the observable"""
        raise NotImplementedError

    @classmethod
    def register_observable(cls, observable: Observable):
        """Register an observable implementation by adding it into the Observable class.

        Args:
            observable (Observable): Observable class to register.
        """
        setattr(cls, observable.__name__, observable)

    def __matmul__(self, other) -> Observable.TensorProduct:
        if isinstance(other, Observable.TensorProduct):
            return other.__rmatmul__(self)

        if isinstance(other, Observable):
            return Observable.TensorProduct([self, other])

        raise ValueError("Can only perform tensor products between observables.")

    def __repr__(self) -> str:
        return f"{self.name}('qubit_count': {self.qubit_count})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Observable):
            return self.name == other.name
        return NotImplemented
