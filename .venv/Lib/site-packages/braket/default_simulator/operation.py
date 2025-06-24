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

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
from scipy.linalg import fractional_matrix_power


class Operation(ABC):
    """
    Encapsulates an operation acting on a set of target qubits.
    """

    @property
    @abstractmethod
    def targets(self) -> tuple[int, ...]:
        """tuple[int, ...]: The indices of the qubits the operation applies to.

        Note: For an index to be a target of an observable, the observable must have a nontrivial
        (i.e. non-identity) action on that index. For example, a tensor product observable with a
        Z factor on qubit j acts trivially on j, so j would not be a target. This does not apply to
        gate operations.
        """


class GateOperation(Operation, ABC):
    """
    Encapsulates a unitary quantum gate operation acting on
    a set of target qubits.
    """

    def __init__(self, targets, *params, ctrl_modifiers=(), power=1):
        self._targets = tuple(targets)
        self._ctrl_modifiers = ctrl_modifiers
        self._power = power

    @property
    def targets(self) -> tuple[int, ...]:
        return self._targets

    @property
    @abstractmethod
    def _base_matrix(self) -> np.ndarray:
        """np.ndarray: The matrix representation of the operation."""

    @property
    def matrix(self) -> np.ndarray:
        unitary = self._base_matrix
        if int(self._power) == self._power:
            unitary = np.linalg.matrix_power(unitary, int(self._power))
        else:
            unitary = fractional_matrix_power(unitary, self._power)
        return unitary

    def __eq__(self, other):
        possible_parameters = "_angle", "_angle_1", "_angle_2"
        return self.targets == other.targets and all(
            getattr(self, param, None) == getattr(other, param, None)
            for param in possible_parameters
        )


class KrausOperation(Operation, ABC):
    """
    Encapsulates a quantum channel acting on a set of target qubits in the Kraus operator
    representation.
    """

    @property
    @abstractmethod
    def matrices(self) -> list[np.ndarray]:
        """list[np.ndarray]: A list of matrices representing Kraus operators."""

    def __eq__(self, other):
        return self.targets == other.targets and np.allclose(self.matrices, other.matrices)


class Observable(Operation, ABC):
    """
    Encapsulates an observable to be measured in the computational basis.
    """

    @property
    def measured_qubits(self) -> tuple[int, ...]:
        """tuple[int, ...]: The indices of the qubits that are measured for this observable.

        Unlike `targets`, this includes indices on which the observable acts trivially.
        For example, a tensor product observable made entirely of n Z factors will have
        n measured qubits.
        """
        return self.targets

    @property
    def is_standard(self) -> bool:
        r"""bool: Whether the observable is Pauli-like, that is, has eigenvalues of :math:`\pm 1`.

        Examples include the Pauli and Hadamard observables.
        """
        return False

    def __pow__(self, power: int) -> Observable:
        if not isinstance(power, int):
            raise TypeError("power must be integer")
        return self._pow(power)

    @abstractmethod
    def _pow(self, power: int) -> Observable:
        """Raises this observable to the given power.

        Only defined for integer powers.

        Args:
            power (int): The power to raise the observable to.

        Returns:
            Observable: The observable raised to the given power.
        """

    @property
    @abstractmethod
    def eigenvalues(self) -> np.ndarray:
        """
        np.ndarray: The eigenvalues of the observable ordered by computational basis state.
        """

    @abstractmethod
    def apply(self, state: np.ndarray) -> np.ndarray:
        """Applies this observable to the given state.

        Args:
            state (np.ndarray): The state to apply the observable to.

        Returns:
            np.ndarray: The state after the observable has been applied.
        """

    @abstractmethod
    def fix_qubit(self, qubit: int) -> Observable:
        """Creates a copy of it acting on the given qubit.

        Only defined for observables that act on 1 qubit.

        Args:
            qubit (int): The target qubit of the new observable.

        Returns:
            Observable: A copy of this observable, acting on the new qubit.
        """

    @abstractmethod
    def diagonalizing_gates(self, num_qubits: Optional[int] = None) -> tuple[GateOperation, ...]:
        """The gates that diagonalize the observable in the computational basis.

        Args:
            num_qubits (int, optional): The number of qubits the observable acts on.
                Only used if no target is specified, in which case a gate is created
                for each target qubit. This only makes sense for single-qubit observables.

        Returns:
            tuple[GateOperation, ...]: The gates that diagonalize the observable in the
            computational basis, if it is not already in the computational basis.
            If there is no explicit target, this method returns a tuple of gates
            acting on every qubit.
        """
