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

import numpy as np
import opt_einsum

from braket.default_simulator.operation import GateOperation


def apply_operations(
    state: np.ndarray, qubit_count: int, operations: list[GateOperation], batch_size: int
) -> np.ndarray:
    r"""Applies operations to a state vector in batches of size :math:`batch\_size`.

    :math:`operations` is partitioned into contiguous batches of size :math:`batch\_size` (with
    remainder). The state vector is treated as a type :math:`(qubit\_count, 0)` tensor, and each
    operation is treated as a type :math:`(target\_length, target\_length)` tensor (where
    :math:`target\_length` is the number of targets the operation acts on), and each batch is
    contracted in an order optimized among the operations in the batch. Larger batches can be
    significantly faster (although this is not guaranteed), but will use more memory.

    For example, if we have a 4-qubit state :math:`S` and a batch with two gates :math:`G1` and
    :math:`G2` that act on qubits 0 and 1 and 1 and 3, respectively, then the state vector after
    applying the batch is :math:`S^{mokp} = S^{ijkl} G1^{mn}_{ij} G2^{op}_{nl}`.

    Depending on the batch size, number of qubits, and the number and types of gates, the speed can
    be more than twice that of applying operations one at a time. Empirically, noticeable
    performance improvements were observed starting with a batch size of 10, with increasing
    performance gains up to a batch size of 50. We tested this with 16 GB of memory. For batch sizes
    greater than 50, consider using an environment with more than 16 GB of memory.

    Args:
        state (np.ndarray): The state vector to apply :math:`operations` to, as a type
            :math:`(qubit\_count, 0)` tensor
        qubit_count (int): The number of qubits in the state
        operations (list[GateOperation]): The operations to apply to the state vector
        batch_size: The number of operations to contract in each batch

    Returns:
        np.ndarray: The state vector after applying the given operations, as a type
        (num_qubits, 0) tensor
    """
    # TODO: Write algorithm to determine partition size based on operations and qubit count
    partitions = [operations[i : i + batch_size] for i in range(0, len(operations), batch_size)]

    for partition in partitions:
        state = _contract_operations(state, qubit_count, partition)

    return state


def _contract_operations(
    state: np.ndarray, qubit_count: int, operations: list[GateOperation]
) -> np.ndarray:
    contraction_parameters = [state, list(range(qubit_count))]
    index_substitutions = {i: i for i in range(qubit_count)}
    next_index = qubit_count
    for operation in operations:
        matrix = operation.matrix
        targets = operation.targets

        # Lower indices, which will be traced out
        covariant = [index_substitutions[i] for i in targets]

        # Upper indices, which will replace the contracted indices in the state vector
        contravariant = list(range(next_index, next_index + len(covariant)))

        indices = contravariant + covariant
        # `matrix` as type-(len(contravariant), len(covariant)) tensor
        matrix_as_tensor = np.reshape(matrix, [2] * len(indices))

        contraction_parameters += [matrix_as_tensor, indices]
        next_index += len(covariant)
        index_substitutions.update({targets[i]: contravariant[i] for i in range(len(targets))})

    # Ensure state is in correct order
    new_indices = [index_substitutions[i] for i in range(qubit_count)]
    contraction_parameters.append(new_indices)
    return opt_einsum.contract(*contraction_parameters)
