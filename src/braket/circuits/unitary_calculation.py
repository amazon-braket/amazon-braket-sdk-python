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


def calculate_unitary(instructions: Iterable[Instruction], used_qubits: QubitSet) -> np.ndarray:
    """
    Returns the unitary matrix representation for all the `instructions` on qubits `used_qubits`.

    Note:
        The performance of this method degrades with qubit count. It might be slow for
        `len(used_qubits)` > 10.

    Args:
        instructions (Iterable[Instruction]): The instructions for which the unitary matrix
            will be calculated.
        used_qubits (QubitSet, optional): The actual qubits used by the instructions.

    Returns:
        np.ndarray: A numpy array with shape (2^qubit_count, 2^qubit_count) representing the
        `instructions` as a unitary matrix.

    Raises:
        TypeError: If `instructions` is not composed only of `Gate` instances,
            i.e. a circuit with `Noise` operators will raise this error.
    """
    qubits = sorted(used_qubits)
    qubit_count = len(qubits)
    index_substitutions = {qubits[i]: i for i in range(qubit_count)}

    rank = 2**qubit_count
    unitary = np.eye(rank).reshape([2] * 2 * qubit_count)

    for instruction in instructions:
        if not isinstance(instruction.operator, Gate):
            raise TypeError("Only Gate operators are supported to build the unitary")
        targets = tuple(index_substitutions[qubit] for qubit in instruction.target)
        unitary = multiply_matrix(unitary, instruction.operator.to_matrix(), targets)

    return unitary.reshape(rank, rank)
