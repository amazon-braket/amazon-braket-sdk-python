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
from functools import singledispatch
from typing import Any, Optional, Union

import numpy as np

from braket.default_simulator.linalg_utils import marginal_probability, partial_trace
from braket.default_simulator.observables import (
    Hadamard,
    Hermitian,
    Identity,
    PauliX,
    PauliY,
    PauliZ,
    TensorProduct,
)
from braket.default_simulator.operation import Observable
from braket.default_simulator.operation_helpers import ir_matrix_to_ndarray
from braket.default_simulator.simulation import Simulation
from braket.default_simulator.state_vector_simulation import StateVectorSimulation
from braket.ir import jaqcd


def from_braket_result_type(result_type) -> ResultType:
    """Creates a `ResultType` corresponding to the given Braket instruction.

    Args:
        result_type: Result type for a circuit specified using the `braket.ir.jacqd` format.

    Returns:
        ResultType: Instance of specific `ResultType` corresponding to the type of result_type

    Raises:
        NotImplementedError: If no concrete `ResultType` class has been registered
            for the Braket instruction type
    """
    return _from_braket_result_type(result_type)


@singledispatch
def _from_braket_result_type(result_type):
    raise NotImplementedError(f"Result type {result_type} not recognized")


class ResultType(ABC):
    """
    An abstract class that when implemented defines a calculation on a
    quantum state simulation.

    Note:
        All result types are calculated exactly, instead of approximated from samples.
        Sampled results are returned from `Simulation.retrieve_samples`, which can be processed by,
        for example, the Amazon Braket SDK.
    """

    @abstractmethod
    def calculate(self, simulation: Simulation) -> Any:
        # Return type of Any due to lack of sum type support in Python
        """Calculate a result from the given quantum state vector simulation.

        Args:
            simulation (Simulation): The simulation to use in the calculation.

        Returns:
            Any: The result of the calculation.
        """


class TargetedResultType(ResultType, ABC):
    """
    Holds an observable that may target qubits.
    """

    def __init__(self, targets: Optional[list[int]] = None):
        """
        Args:
            targets (list[int], optional): The target qubits of the result type.
                If None, no specific qubits are targeted.
        """
        self._targets = targets

    @property
    def targets(self) -> Optional[tuple[int, ...]]:
        """tuple[int], optional: The target qubits of the result type, if any."""
        return self._targets


class ObservableResultType(TargetedResultType, ABC):
    """
    Holds an observable to perform a calculation in conjunction with a state.
    """

    def __init__(self, observable: Observable):
        """
        Args:
            observable (Observable): The observable for which the desired result is calculated
        """
        super().__init__(observable.measured_qubits)
        self._observable = observable

    @property
    def observable(self):
        """Observable: The observable for which the desired result is calculated."""
        return self._observable

    @property
    def targets(self) -> Optional[tuple[int, ...]]:
        return self._observable.measured_qubits

    def calculate(self, simulation: Simulation) -> Union[float, list[float]]:
        """Calculates the result type using the underlying observable.

        Returns a real number if the observable has defined targets,
        or a list of real numbers, one for the result type on each target,
        if the observable has no target.

        Args:
            simulation (Simulation): The simulation to use in the calculation.

        Returns:
            Union[float, list[float]]: The value of the result type;
            will be a real due to self-adjointness of observable.
        """
        if self._observable.measured_qubits:
            return self._calculate_single_quantity(simulation, self._observable)
        return [
            self._calculate_single_quantity(simulation, self._observable.fix_qubit(qubit))
            for qubit in range(simulation.qubit_count)
        ]

    @staticmethod
    @abstractmethod
    def _calculate_single_quantity(simulation: Simulation, observable: Observable) -> float:
        """Calculates a single real value of the result type.

        Args:
            simulation (Simulation): The simulation to use in the calculation.
            observable (Observable): The observable used to calculate the result type.

        Returns:
            float: The value of the result type.
        """


class StateVector(ResultType):
    """
    Simply returns the given state vector.
    """

    def calculate(self, simulation: StateVectorSimulation) -> np.ndarray:
        """Return the given state vector of the simulation.

        Args:
            simulation (StateVectorSimulation): The simulation whose state vector will be returned

        Returns:
            np.ndarray: The state vector (before observables) of the simulation
        """
        return simulation.state_vector


@_from_braket_result_type.register
def _(_: jaqcd.StateVector):
    return StateVector()


class DensityMatrix(TargetedResultType):
    """
    Simply returns the given density matrix.
    """

    def __init__(self, targets: Optional[list[int]] = None):
        """
        Args:
            targets (Optional[list[int]]): The qubit indices on which the reduced density matrix
                are desired. If no targets are specified, the full density matrix is calculated.
                Default: `None`
        """
        super().__init__(targets)

    def calculate(self, simulation: Simulation) -> np.ndarray:
        """Return the given density matrix of the simulation.

        Args:
            simulation (Simulation): The simulation whose (full or reduced)
                density matrix will be returned.

        Returns:
            np.ndarray: The density matrix (before observables) of the simulation
        """
        if self._targets is None or np.array_equal(self._targets, range(simulation.qubit_count)):
            return simulation.density_matrix
        else:
            if not all(ta in list(range(simulation.qubit_count)) for ta in self._targets):
                raise IndexError(
                    "Input target qubits must be within the range of the qubits in the circuit."
                )
            return partial_trace(
                simulation.density_matrix.reshape(np.array([2] * 2 * simulation.qubit_count)),
                self._targets,
            )


@_from_braket_result_type.register
def _(density_matrix: jaqcd.DensityMatrix):
    return DensityMatrix(density_matrix.targets)


class Amplitude(ResultType):
    """
    Extracts the amplitudes of the desired computational basis states.
    """

    def __init__(self, states: list[str]):
        """
        Args:
            states (list[str]): The computational basis states whose amplitudes are desired
        """
        self._states = states

    def calculate(self, simulation: StateVectorSimulation) -> dict[str, complex]:
        """Return the amplitudes of the desired computational basis states in the state
        of the given simulation.

        Args:
            simulation (StateVectorSimulation): The simulation whose state vector amplitudes
                will be returned

        Returns:
            dict[str, complex]: A dict keyed on computational basis states as bitstrings,
            with corresponding values the amplitudes
        """
        state = simulation.state_vector
        return {basis_state: state[int(basis_state, 2)] for basis_state in self._states}


@_from_braket_result_type.register
def _(amplitude: jaqcd.Amplitude):
    return Amplitude(amplitude.states)


class Probability(TargetedResultType):
    """
    Computes the marginal probabilities of computational basis states on the desired qubits.
    """

    def __init__(self, targets: Optional[list[int]] = None):
        """
        Args:
            targets (Optional[list[int]]): The qubit indices on which probabilities are desired.
                If no targets are specified, the probabilities are calculated on the entire state.
                Default: `None`
        """
        super().__init__(targets)

    def calculate(self, simulation: Simulation) -> np.ndarray:
        """Return the marginal probabilities of computational basis states on the target qubits.

        Probabilities are marginalized over all non-target qubits.

        Args:
            simulation (Simulation): The simulation from which probabilities are calculated.

        Returns:
            np.ndarray: An array of probabilities of length equal to 2^(number of target qubits),
            indexed by the decimal encoding of the computational basis state on the target qubits

        """
        return marginal_probability(
            simulation.probabilities,
            self._targets,
        )


@_from_braket_result_type.register
def _(probability: jaqcd.Probability):
    return Probability(probability.targets)


class Expectation(ObservableResultType):
    """
    Holds an observable :math:`O` to calculate its expected value.
    """

    @staticmethod
    def _calculate_single_quantity(simulation: Simulation, observable: Observable) -> float:
        return simulation.expectation(observable)


@_from_braket_result_type.register
def _(expectation: jaqcd.Expectation):
    return Expectation(_from_braket_observable(expectation.observable, expectation.targets))


class Variance(ObservableResultType):
    """
    Holds an observable :math:`O` to calculate its variance.
    """

    @staticmethod
    def _calculate_single_quantity(simulation: Simulation, observable: Observable) -> float:
        return simulation.expectation(observable**2) - simulation.expectation(observable) ** 2


@_from_braket_result_type.register
def _(variance: jaqcd.Variance):
    return Variance(_from_braket_observable(variance.observable, variance.targets))


def _from_braket_observable(
    ir_observable: list[Union[str, list[list[list[float]]]]], ir_targets: Optional[list[int]] = None
) -> Observable:
    targets = list(ir_targets) if ir_targets else None
    if len(ir_observable) == 1:
        return _from_single_observable(ir_observable[0], targets)
    else:
        observable = TensorProduct(
            [_from_single_observable(factor, targets, is_factor=True) for factor in ir_observable]
        )
        if targets:
            raise ValueError(
                f"Found {len(targets)} more target qubits than the tensor product acts on"
            )
        return observable


def _from_single_observable(
    observable: Union[str, list[list[list[float]]]],
    targets: Optional[list[int]] = None,
    # IR tensor product observables are decoupled from targets
    is_factor: bool = False,
) -> Observable:
    if observable == "i":
        return Identity(_actual_targets(targets, 1, is_factor))
    elif observable == "h":
        return Hadamard(_actual_targets(targets, 1, is_factor))
    elif observable == "x":
        return PauliX(_actual_targets(targets, 1, is_factor))
    elif observable == "y":
        return PauliY(_actual_targets(targets, 1, is_factor))
    elif observable == "z":
        return PauliZ(_actual_targets(targets, 1, is_factor))
    else:
        try:
            matrix = ir_matrix_to_ndarray(observable)
            if is_factor:
                num_qubits = int(np.log2(len(matrix)))
                return Hermitian(matrix, _actual_targets(targets, num_qubits, True))
            else:
                return Hermitian(matrix, targets)
        except Exception:
            raise ValueError(f"Invalid observable specified: {observable}, targets: {targets}")


def _actual_targets(targets: list[int], num_qubits: int, is_factor: bool):
    if not is_factor:
        return targets
    try:
        return [targets.pop(0) for _ in range(num_qubits)]
    except Exception:
        raise ValueError("Insufficient target qubits for tensor product")
