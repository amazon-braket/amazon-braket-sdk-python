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


def _einsum_subscripts(targets: QubitSet, qubit_count: int) -> str:
    target_count = len(targets)

    gate_left_indexes = list(range(target_count))
    un_left_indexes = list(range(target_count, target_count + qubit_count))
    un_right_indexes = list(range(target_count + qubit_count, target_count + 2 * qubit_count))

    gate_right_indexes = [un_left_indexes[-1 - target] for target in targets]

    result_left_indexes = un_left_indexes.copy()
    for pos, target in enumerate(targets):
        result_left_indexes[-1 - target] = gate_left_indexes[pos]

    return (
        gate_left_indexes + gate_right_indexes,
        un_left_indexes + un_right_indexes,
        result_left_indexes + un_right_indexes,
    )


def calculate_unitary(qubit_count: int, instructions: Iterable[Instruction]) -> np.ndarray:
    """
    Returns the unitary matrix representation for all the `instructions` with a given
    `qubit_count`.
    *Note*: The performance of this method degrades with qubit count. It might be slow for
    qubit count > 10.

    Args:
        qubit_count (int): Total number of qubits, enough for all the `instructions`.
        instructions (Iterable[Instruction]): The instructions for which the unitary matrix
            will be calculated.

    Returns:
        np.ndarray: A numpy array with shape (2^qubit_count, 2^qubit_count) representing the
            `instructions` as a unitary.

    Raises:
        TypeError: If `instructions` is not composed only of `Gate` instances,
            i.e. a circuit with `Noise` operators will raise this error.
    """
    unitary = np.eye(2**qubit_count, dtype=complex)
    un_tensor = np.reshape(unitary, qubit_count * [2, 2])

    for instr in instructions:
        if not isinstance(instr.operator, Gate):
            raise TypeError("Only Gate operators are supported to build the unitary")

        matrix = instr.operator.to_matrix()
        targets = instr.target

        gate_indexes, un_indexes, result_indexes = _einsum_subscripts(targets, qubit_count)
        gate_matrix = np.reshape(matrix, len(targets) * [2, 2])

        un_tensor = np.einsum(
            gate_matrix,
            gate_indexes,
            un_tensor,
            un_indexes,
            result_indexes,
            dtype=complex,
            casting="no",
        )

    return np.reshape(un_tensor, 2 * [2**qubit_count])


def calculate_unitary_big_endian(
    instructions: Iterable[Instruction], qubits: QubitSet
) -> np.ndarray:
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
            unitary,
            instruction.operator.to_matrix(),
            tuple(index_substitutions[qubit] for qubit in instruction.target),
        )

    return unitary.reshape(rank, rank)
