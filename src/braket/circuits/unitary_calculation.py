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

import numpy as np

from braket.circuits.circuit import Circuit
from braket.circuits.gate import Gate
from braket.circuits.qubit_set import QubitSet


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


def as_unitary(circuit: Circuit) -> np.ndarray:
    """
    Returns the unitary matrix representation of the entire `circuit`.
    *Note*: The performance of this method degrades with qubit count. It might be slow for
    qubit count > 10.

    Args:
        circuit (Circuit): The circuit from which to get the unitary matrix.

    Returns:
        np.ndarray: A numpy array with shape (2^qubit_count, 2^qubit_count) representing the
            `circuit` as a unitary. *Note*: For an empty `circuit`, an empty numpy array is
            returned (`array([], dtype=complex128)`).

    Raises:
        TypeError: If `circuit` is not composed only of `Gate` instances,
            i.e. a circuit with `Noise` operators will raise this error.

    Examples:
        >>> circ = Circuit().h(0).cnot(0, 1)
        >>> as_unitary(circ)
        array([[ 0.70710678+0.j,  0.70710678+0.j,  0.        +0.j,
                 0.        +0.j],
               [ 0.        +0.j,  0.        +0.j,  0.70710678+0.j,
                -0.70710678+0.j],
               [ 0.        +0.j,  0.        +0.j,  0.70710678+0.j,
                 0.70710678+0.j],
               [ 0.70710678+0.j, -0.70710678+0.j,  0.        +0.j,
                 0.        +0.j]])
    """
    qubits = circuit.qubits
    if not qubits:
        return np.zeros(0, dtype=complex)
    qubit_count = max(qubits) + 1

    unitary = np.eye(2 ** qubit_count, dtype=complex)
    un_tensor = np.reshape(unitary, qubit_count * [2, 2])

    for instr in circuit.instructions:
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

    return np.reshape(un_tensor, 2 * [2 ** qubit_count])
