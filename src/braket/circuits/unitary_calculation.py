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

from collections.abc import Iterable

import numpy as np
from scipy.linalg import fractional_matrix_power

from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.default_simulator.linalg_utils import multiply_matrix
from braket.registers.qubit_set import QubitSet


def calculate_unitary_big_endian(
    instructions: Iterable[Instruction], qubits: QubitSet
) -> np.ndarray:
    """Returns the unitary matrix representation for all the `instruction`s on qubits `qubits`.

    Note:
        The performance of this method degrades with qubit count. It might be slow for
        `len(qubits)` > 10.

    Args:
        instructions (Iterable[Instruction]): The instructions for which the unitary matrix
            will be calculated.
        qubits (QubitSet): The actual qubits used by the instructions.

    Returns:
        np.ndarray: A numpy array with shape (2^qubit_count, 2^qubit_count) representing the
        `instructions` as a unitary matrix.

    Raises:
        TypeError: If `instructions` is not composed only of `Gate` instances,
            i.e. a circuit with `Noise` operators will raise this error.
            Any `CompilerDirective` instructions will be ignored, as these should
            not affect the unitary representation of the circuit.
    """
    qubits_sorted = sorted(qubits)
    qubit_count = len(qubits_sorted)
    # Map qubits to contiguous indices starting from 0
    index_substitutions = {qubits_sorted[i]: i for i in range(qubit_count)}
    rank = 2**qubit_count
    # Initialize identity unitary as type (rank, rank) tensor
    unitary = np.eye(rank, dtype=complex).reshape([2] * 2 * qubit_count)

    for instruction in instructions:
        if isinstance(instruction.operator, CompilerDirective):
            continue
        if not isinstance(instruction.operator, Gate):
            raise TypeError("Only Gate operators are supported to build the unitary")

        base_gate_matrix = instruction.operator.to_matrix()
        if int(instruction.power) == instruction.power:
            gate_matrix = np.linalg.matrix_power(base_gate_matrix, int(instruction.power))
        else:
            gate_matrix = fractional_matrix_power(base_gate_matrix, instruction.power)

        unitary = multiply_matrix(
            unitary,
            gate_matrix,
            tuple(index_substitutions[qubit] for qubit in instruction.target),
            controls=instruction.control,
            control_state=instruction.control_state,
        )

    return unitary.reshape(rank, rank)
