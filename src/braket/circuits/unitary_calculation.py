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

from typing import Iterable

import numpy as np

from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.qubit_set import QubitSet
from braket.default_simulator.linalg_utils import multiply_matrix


def calculate_unitary(instructions: Iterable[Instruction], qubits: QubitSet) -> np.ndarray:
    """
    Returns the unitary matrix representation for all the `instructions` on qubits `qubits`.

    Note:
        The performance of this method degrades with qubit count. It might be slow for
        `len(qubits)` > 10.

    Args:
        instructions (Iterable[Instruction]): The instructions for which the unitary matrix
            will be calculated.
        qubits (QubitSet, optional): The actual qubits used by the instructions.

    Returns:
        np.ndarray: A numpy array with shape (2^qubit_count, 2^qubit_count) representing the
        `instructions` as a unitary matrix.

    Raises:
        TypeError: If `instructions` is not composed only of `Gate` instances,
            i.e. a circuit with `Noise` operators will raise this error.
    """
    qubits_sorted = sorted(qubits)
    qubit_count = len(qubits_sorted)
    # Map qubits to contiguous indices starting from 0
    index_substitutions = {qubits_sorted[i]: i for i in range(qubit_count)}
    rank = 2**qubit_count
    # Initialize identity unitary as type (rank, rank) tensor
    unitary = np.eye(rank).reshape([2] * 2 * qubit_count)

    for instruction in instructions:
        if not isinstance(instruction.operator, Gate):
            raise TypeError("Only Gate operators are supported to build the unitary")
        unitary = multiply_matrix(
            unitary, instruction.operator.to_matrix(),
            tuple(index_substitutions[qubit] for qubit in instruction.target)
        )

    return unitary.reshape(rank, rank)
