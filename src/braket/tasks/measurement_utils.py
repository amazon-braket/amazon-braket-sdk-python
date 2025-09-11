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

from collections import Counter

import numpy as np

from braket.circuits import Observable
from braket.circuits.observable import StandardObservable
from braket.circuits.observables import TensorProduct


def measurement_counts_from_measurements(measurements: np.ndarray) -> Counter:
    """Creates measurement counts from measurements

    Args:
        measurements (np.ndarray): 2d array - row is shot and column is qubit.

    Returns:
        Counter: A Counter of measurements. Key is the measurements in a big endian binary
        string. Value is the number of times that measurement occurred.
    """
    bitstrings = [
        "".join([str(element) for element in measurements[j]]) for j in range(len(measurements))
    ]
    return Counter(bitstrings)


def measurement_probabilities_from_measurement_counts(
    measurement_counts: Counter,
) -> dict[str, float]:
    """Creates measurement probabilities from measurement counts

    Args:
        measurement_counts (Counter): A Counter of measurements. Key is the measurements
            in a big endian binary string. Value is the number of times that measurement
            occurred.

    Returns:
        dict[str, float]: A dictionary of probabilistic results. Key is the measurements
        in a big endian binary string. Value is the probability the measurement occurred.
    """
    shots = sum(measurement_counts.values())
    return {key: count / shots for key, count in measurement_counts.items()}


def measurements_from_measurement_probabilities(
    measurement_probabilities: dict[str, float], shots: int
) -> np.ndarray:
    """Creates measurements from measurement probabilities.

    Args:
        measurement_probabilities (dict[str, float]): A dictionary of probabilistic results.
            Key is the measurements in a big endian binary string.
            Value is the probability the measurement occurred.
        shots (int): number of iterations on device.

    Returns:
        np.ndarray: 2d array of measurements matching the given probability distribution
        and number of shots.
    """
    measurements_list = []
    for bitstring, probability in measurement_probabilities.items():
        measurement = list(bitstring)
        individual_measurement_list = [measurement] * round(probability * shots)
        measurements_list.extend(individual_measurement_list)
    return np.asarray(measurements_list, dtype=int)


def expectation_from_measurements(
    measurements: np.ndarray,
    measured_qubits: list[int],
    observable: Observable,
    targets: list[int],
) -> float:
    samples = samples_from_measurements(measurements, measured_qubits, observable, targets)
    return np.mean(samples)


def samples_from_measurements(
    measurements: np.ndarray,
    measured_qubits: list[int],
    observable: Observable,
    targets: list[int],
) -> np.ndarray:
    measurements = selected_measurements(measurements, measured_qubits, targets)
    if isinstance(observable, StandardObservable):
        # Process samples for observables with eigenvalues {coeff, -coeff} with equal weight
        return observable.coefficient * (1 - 2 * measurements.flatten())
    # Replace the basis state in the computational basis with the correct eigenvalue.
    # Extract only the columns of the basis samples required based on ``targets``.
    indices = measurements_base_10(measurements)
    if isinstance(observable, TensorProduct):
        return np.array([observable.eigenvalue(index).real for index in indices])
    return observable.eigenvalues[indices].real


def selected_measurements(
    measurements: np.ndarray, measured_qubits: list[int], targets: list[int] | None
) -> np.ndarray:
    if targets is not None and targets != measured_qubits:
        # Only some qubits targeted
        columns = [measured_qubits.index(t) for t in targets]
        measurements = measurements[:, columns]
    return measurements


def measurements_base_10(measurements: np.ndarray) -> np.ndarray:
    # convert samples from a list of 0, 1 integers, to base 10 representation
    two_powers = 2 ** np.arange(measurements.shape[-1])[::-1]  # 2^(n-1), ..., 2, 1
    return measurements @ two_powers
