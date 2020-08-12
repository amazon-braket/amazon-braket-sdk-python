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

from typing import Any, List, Sequence

import numpy as np

from braket.circuits.operator import Operator


class QuantumOperator(Operator):
    """A quantum operator is the definition of a quantum operation for a quantum device."""

    def __init__(self, qubit_count: int, ascii_symbols: Sequence[str]):
        """
        Args:
            qubit_count (int): Number of qubits this quantum operator interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the quantum operator.
                These are used when printing a diagram of circuits.
                Length must be the same as `qubit_count`, and index ordering is expected
                to correlate with target ordering on the instruction.
                For instance, if CNOT instruction has the control qubit on the first index and
                target qubit on the second index. Then ASCII symbols would have ["C", "X"] to
                correlate a symbol with that index.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`
        """

        if qubit_count < 1:
            raise ValueError(f"qubit_count, {qubit_count}, must be greater than zero")
        self._qubit_count = qubit_count

        if ascii_symbols is None:
            raise ValueError("ascii_symbols must not be None")

        if len(ascii_symbols) != qubit_count:
            msg = f"ascii_symbols, {ascii_symbols}, length must equal qubit_count, {qubit_count}"
            raise ValueError(msg)
        self._ascii_symbols = tuple(ascii_symbols)

    @property
    def qubit_count(self) -> int:
        """int: Returns number of qubits this quantum operator interacts with."""
        return self._qubit_count

    @property
    def ascii_symbols(self) -> List[str]:
        """List[str]: Returns the ascii symbols for the quantum operator."""
        return self._ascii_symbols

    @property
    def name(self) -> str:
        """
        Returns the name of the quantum operator

        Returns:
            The name of the quantum operator as a string
        """
        return self.__class__.__name__

    def to_ir(self, *args, **kwargs) -> Any:
        """Returns IR representation of quantum operator

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        raise NotImplementedError("to_ir has not been implemented yet.")

    def to_matrix(self, *args, **kwargs) -> Any:
        """Returns a matrix representation of the quantum operator

        Returns:
            np.ndarray: A matrix representation of the quantum operator
        """
        raise NotImplementedError("to_matrix has not been implemented yet.")

    def matrix_equivalence(self, other: QuantumOperator):
        """
        Whether the matrix form of two quantum operators are equivalent

        Args:
            other (QuantumOperator): Quantum operator instance to compare this quantum operator to

        Returns:
            bool: If matrix forms of this quantum operator and the other quantum operator
            are equivalent
        """
        if not isinstance(other, QuantumOperator):
            return NotImplemented
        try:
            return np.allclose(self.to_matrix(), other.to_matrix())
        except ValueError:
            return False

    def __repr__(self):
        return f"{self.name}('qubit_count': {self.qubit_count})"
