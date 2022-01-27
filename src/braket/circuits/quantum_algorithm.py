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

from typing import List

from braket.circuits.quantum_operator import QuantumOperator


class QuantumAlgorithm(QuantumOperator):
    """
    A circuit that can be distinctly represented in a circuit. Functionally, this is a circuit but
    can retain the identity of the specific algorithm it represents within a larger circuit.

    Generation is done recursively based upon the qubit set.
    """

    def __init__(self, qubit_set, ascii_symbols):
        self._qubit_set = qubit_set
        super().__init__(qubit_count=len(qubit_set), ascii_symbols=ascii_symbols)

    @property
    def qubit_set(self) -> List:
        """
        The qubits the algorithm will act and be generated over

        Returns:
            List: The qubits the algorithm will act and be generated over.
        """
        return self._qubit_set

    def _generator(self, qubit_set: List):
        """
        Recursively generates the Algorithm.

        Args:
            qubit_set (List): target qubit(s)
        Returns:
            A recursively generated circuit of depth equal to the size of the
            qubit set.
        """
        raise NotImplementedError

    def decompose(self):
        """
        Returns the expanded circuit representation of the algorithm.

        Returns:
            The expanded circuit representation of the algorithm.
        """
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, QuantumAlgorithm):
            return self.name == other.name
        return NotImplemented

    @classmethod
    def register_quantum_algorithm(cls, quantum_algorithm: "QuantumAlgorithm"):
        """Register a quantum algorithm implementation by adding it into the QuantumAlgorithm class.

        Args:
            quantum_algorithm (QuantumAlgorithm): QuantumAlgorithm class to register.
        """
        setattr(cls, quantum_algorithm.__name__, quantum_algorithm)
