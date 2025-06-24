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

from braket.default_simulator.operation import GateOperation, Observable
from braket.default_simulator.simulation import Simulation
from braket.default_simulator.simulation_strategies import (
    batch_operation_strategy,
    single_operation_strategy,
)


class StateVectorSimulation(Simulation):
    """
    This class tracks the evolution of a quantum system with `qubit_count` qubits.
    The state of system the evolves by application of `GateOperation`s using the `evolve()` method.

    How operations are applied is determined by the `batch_size` argument in `__init__`.

    If `batch_size` is set to 1, operations are applied one at a time.

    If `batch_size` is greater than 1, the operation list is first partitioned into a sequence of
    contiguous batches, each of size `batch_size`. If the number of operations is not evenly
    divisible by `batch_size`, then the number of operations in the last batch will just be the
    remainder. The operations in each batch are then applied (contracted) together. The order of the
    operations in the batches are the same as the original order of the operations. In most cases,
    tasks complete faster when run on a larger batch, but require more memory. For more details, see
    the module `batch_operation_strategy`.
    """

    def __init__(self, qubit_count: int, shots: int, batch_size: int):
        r"""
        Args:
            qubit_count (int): The number of qubits being simulated.
                All the qubits start in the :math:`\ket{\mathbf{0}}` computational basis state.
            shots (int): The number of samples to take from the simulation.
                If set to 0, only results that do not require sampling, such as state vector
                or expectation, are generated.
            batch_size (int): The size of the partitions to contract; if set to 1,
                the gates are applied one at a time, without any optimization of
                contraction order. Must be a positive integer.
        """
        if not isinstance(batch_size, int):
            raise TypeError(f"batch_size must be of type `int`, but {type(batch_size)} provided")
        if batch_size < 1:
            raise ValueError(f"batch_size must be a positive integer, but {batch_size} provided")

        super().__init__(qubit_count=qubit_count, shots=shots)
        initial_state = np.zeros(2**qubit_count, dtype=complex)
        initial_state[0] = 1
        self._state_vector = initial_state
        self._batch_size = batch_size
        self._post_observables = None

    def evolve(self, operations: list[GateOperation]) -> None:
        self._state_vector = StateVectorSimulation._apply_operations(
            self._state_vector, self._qubit_count, operations, self._batch_size
        )

    def apply_observables(self, observables: list[Observable]) -> None:
        """Applies the diagonalizing matrices of the given observables
        to the state of the simulation.

        This method can only be called once.

        Args:
            observables (list[Observable]): The observables to apply

        Raises:
            RuntimeError: If this method is called more than once
        """
        if self._post_observables is not None:
            raise RuntimeError("Observables have already been applied.")
        operations = list(
            sum(
                [observable.diagonalizing_gates(self._qubit_count) for observable in observables],
                (),
            )
        )
        self._post_observables = StateVectorSimulation._apply_operations(
            self._state_vector, self._qubit_count, operations, self._batch_size
        )

    @staticmethod
    def _apply_operations(
        state: np.ndarray, qubit_count: int, operations: list[GateOperation], batch_size: int
    ) -> np.ndarray:
        state_tensor = np.reshape(state, [2] * qubit_count)
        final = (
            single_operation_strategy.apply_operations(state_tensor, qubit_count, operations)
            if batch_size == 1
            else batch_operation_strategy.apply_operations(
                state_tensor, qubit_count, operations, batch_size
            )
        )
        return np.reshape(final, 2**qubit_count)

    def retrieve_samples(self) -> list[int]:
        rng_generator = np.random.default_rng()
        return rng_generator.choice(len(self._state_vector), p=self.probabilities, size=self._shots)

    @property
    def state_vector(self) -> np.ndarray:
        """
        np.ndarray: The state vector specifying the current state of the simulation.

        Note:
            Mutating this array will mutate the state of the simulation.
        """
        return self._state_vector

    @property
    def density_matrix(self) -> np.ndarray:
        """
        np.ndarray: The density matrix specifying the current state of the simulation.
        """
        return np.outer(self._state_vector, self._state_vector.conj())

    @property
    def state_with_observables(self) -> np.ndarray:
        """
        np.ndarray: The state vector diagonalized in the basis of the measured observables.

        Raises:
            RuntimeError: If observables have not been applied
        """
        if self._post_observables is None:
            raise RuntimeError("No observables applied")
        return self._post_observables

    def expectation(self, observable: Observable) -> float:
        qubit_count = self._qubit_count
        with_observables = observable.apply(np.reshape(self._state_vector, [2] * qubit_count))
        return complex(
            np.dot(self._state_vector.conj(), np.reshape(with_observables, 2**qubit_count))
        ).real

    @property
    def probabilities(self) -> np.ndarray:
        """
        np.ndarray: The probabilities of each computational basis state of the current state
            vector of the simulation.
        """
        return self._probabilities(self.state_vector)

    @staticmethod
    def _probabilities(state: np.ndarray) -> np.ndarray:
        """The probabilities of each computational basis state of a given state vector.

        Args:
            state (np.ndarray): The state vector from which probabilities are extracted.

        Returns:
            np.ndarray: The probabilities of each computational basis state.
        """
        return np.abs(state) ** 2
