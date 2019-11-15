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

from typing import Any, Sequence, Tuple

import numpy as np
from aqx.qdk.circuits.operator import Operator
from aqx.qdk.circuits.qubit_set import QubitSet

# TODO: Add parameters support
# TODO: Add printing / visualization capabilities


class Gate(Operator):
    """
    Class `Gate` represents a quantum gate that operates on N qubits and are considered the
    building blocks of quantum circuits. This class is considered the gate definition containing
    the meta-data that defines what a gate is and what it can do.
    """

    def __init__(self, qubit_count: int, ascii_symbols: Sequence[str]):
        """
        Args:
            qubit_count (int): Number of qubits this gate interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the gate, these are used when
                printing a diagram of circuits. Length must be the same as `qubit_count`, and
                index ordering is expected to correlate with target ordering on the instruction.
                For instance, if CNOT instruction has the control qubit on the first index and
                target qubit on the second index. Then ASCII symbols would have ["C", "X"] to
                correlate a symbol with that index.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are None, or
                `ascii_symbols` length != `qubit_count`
        """

        if qubit_count < 1:
            raise ValueError(f"qubit_count, {qubit_count}, must be greater than zero")
        self._qubit_count = qubit_count

        if ascii_symbols is None:
            raise ValueError(f"ascii_symbols must not be None")

        if len(ascii_symbols) != qubit_count:
            msg = f"ascii_symbols, {ascii_symbols}, length must equal qubit_count, {qubit_count}"
            raise ValueError(msg)
        self._ascii_symbols = tuple(ascii_symbols)

    @property
    def qubit_count(self) -> int:
        """int: Returns number of qubits this gate interacts with."""
        return self._qubit_count

    @property
    def ascii_symbols(self) -> Tuple[str]:
        """Tuple[str]: Returns the ascii symbols for the gate."""
        return self._ascii_symbols

    @property
    def name(self) -> str:
        """
        Returns the name of the gate

        Returns:
            name of the gate as a string
        """
        return self.__class__.__name__

    def to_ir(self, target: QubitSet) -> Any:
        """Returns IR object of gate and target

        Args:
            target (QubitSet): target qubit(s)
        Returns:
            IR object of gate and target
        """
        raise NotImplementedError("to_ir has not been implemented yet.")

    def to_matrix(self, *args, **kwargs) -> Any:
        """Returns gate in matrix representation

        Returns:
            np.ndarray: gate in matrix representation
        """
        raise NotImplementedError("to_matrix has not been implemented yet.")

    def __eq__(self, other):
        if not isinstance(other, Gate):
            return NotImplemented
        if self.name == other.name:
            if hasattr(self, "angle"):
                return self.angle == other.angle
            return True
        else:
            return False

    def matrix_equivalence(self, other):
        """
        Return if the matrix form of two gates are equivalent

        Args:
            other (Gate): Gate instance to compare

        Returns:
            true if matrix forms of this gate and the other gate are equivalent
        """
        if not isinstance(other, Gate):
            return NotImplemented
        try:
            return np.allclose(self.to_matrix(), other.to_matrix())
        except ValueError:
            return False

    def __repr__(self):
        if hasattr(self, "angle"):
            return f"{self.name}('angle': {self.angle}, 'qubit_count': {self.qubit_count})"
        return f"{self.name}('qubit_count': {self.qubit_count})"

    @classmethod
    def register_gate(cls, gate: "Gate"):
        """Register a gate implementation by monkey patching into the Gate class.

        Args:
            gate (Gate): Gate instance to register.
        """
        setattr(cls, gate.__name__, gate)
