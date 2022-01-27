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

from typing import List, Sequence

import numpy as np

from braket.circuits import circuit
from braket.circuits.circuit import Circuit
from braket.circuits.instruction import Instruction
from braket.circuits.quantum_algorithm import QuantumAlgorithm
from braket.circuits.qubit_set import QubitSet

"""
To add a new algorithm:
    1. Implement the class and extend `Qu`
    2. Add a method with the `@circuit.subroutine(register=True)` decorator. Method name
       will be added into the `Circuit` class. This method is the default way
       clients add this algorithm to a circuit.
    3. Register the class with the `SubCircuit` class via `SubCircuit.register_subcircuit()`.
"""


class QFT(QuantumAlgorithm):
    """Quantum Fourier Transformation."""

    def __init__(self, qubit_set: List):
        super().__init__(
            qubit_set=qubit_set, ascii_symbols=generate_algo_ascii("QFT", len(qubit_set))
        )

    def _generator(self, qubit_set: List) -> Circuit:
        """
        A recursive generator function for the qft QuantumAlgorithm object.
        The recursion depth is based on the qubit set.

        Args:
            qubit_set (List): The qubits which to generate the algorithm over.

        Returns:
            SubCircuit: A SubCircuit which has the [1, n] generations of the algorithm.

        """
        qft_circuit = Circuit().h(qubit_set[0])
        if len(qubit_set) == 1:
            return qft_circuit
        for qubit in range(len(qubit_set) - 1):
            qft_circuit.cphaseshift(
                (qubit_set[qubit]),
                (qubit_set[qubit + 1]),
                (2 * np.pi) / (2 ** len(qubit_set)),
            )
        del qubit_set[0]
        qft_circuit.add(self._generator(qubit_set))
        return qft_circuit

    def decompose(self) -> Circuit:
        """
        Returns the expanded circuit representation of the algorithm.

        Returns:
            Circuit: The expanded circuit representation of the algorithm.
        """
        return self._generator(self._qubit_set)

    @staticmethod
    @circuit.subroutine(register=True)
    def qft(targets: QubitSet) -> Circuit:
        """Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubits

        Returns:
            Circuit: `Circuit` representing the generated QFT circuit.

        Examples:
            >>> circ = Circuit().qft([0,1,2])
        """
        return Instruction(QFT(targets), target=targets)


QuantumAlgorithm.register_quantum_algorithm(QFT)


def generate_algo_ascii(algo_name: str, qubit_count: int) -> Sequence[str]:
    """

    Args:
        algo_name (str): The name for the algorithm being used.
        qubit_count (int): The number of qubits.

    Returns:

    """
    ascii_rep = []
    for i in range(qubit_count):
        if i != int(qubit_count / 2):
            ascii_rep.append("*")
        else:
            ascii_rep.append(algo_name)
    return ascii_rep
