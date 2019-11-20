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

from dataclasses import dataclass
from typing import Counter, Dict

import numpy as np


@dataclass
class QuantumTaskResult:
    """
    Result of a quantum task execution. This class is intended
    to be initialized by a QuantumTask class.

    Args:
        measurements (numpy.ndarray): 2d array - row is shot, column is qubit.
        measurement_counts (Counter): A Counter of measurements. Key is the measurements
            in a big endian binary string. Value is the number of times that measurement occurred.
        measurement_probabilities (Dict[str, float]): A dictionary of probabilistic results.
            Key is the measurements in a big endian binary string.
            Value is the probability the measurement occurred.
        measurements_copied_from_device (bool): flag whether `measurements` were copied from device.
            If false, `measurements` are calculated from device data.
        measurement_counts_copied_from_device (bool): flag whether `measurement_counts` were copied
            from device. If false, `measurement_counts` are calculated from device data.
        measurement_probabilities_copied_from_device (bool): flag whether
            `measurement_probabilities` were copied from device. If false,
            `measurement_probabilities` are calculated from device data.
    """

    measurements: np.ndarray
    measurement_counts: Counter
    measurement_probabilities: Dict[str, float]
    measurements_copied_from_device: bool
    measurement_counts_copied_from_device: bool
    measurement_probabilities_copied_from_device: bool

    def __eq__(self, other) -> bool:
        if isinstance(other, QuantumTaskResult):
            # __eq__ on numpy arrays results in an array of booleans and therefore can't use
            # the default dataclass __eq__ implementation. Override equals to check if all
            # elements in the array are equal.
            return (self.measurements == other.measurements).all()
        return NotImplemented

    @staticmethod
    def measurement_counts_from_measurements(measurements: np.ndarray) -> Counter:
        """
        Creates measurement counts from measurements

        Args:
            measurements (numpy.ndarray): 2d array - row is shot, column is qubit.

        Returns:
            Counter: A Counter of measurements. Key is the measurements in a big endian binary
                string. Value is the number of times that measurement occurred.
        """
        bitstrings = []
        for j in range(len(measurements)):
            bitstrings.append("".join([str(element) for element in measurements[j]]))
        return Counter(bitstrings)

    @staticmethod
    def measurement_probabilities_from_measurement_counts(
        measurement_counts: Counter,
    ) -> Dict[str, float]:
        """
        Creates measurement probabilities from measurement counts

        Args:
            measurement_counts (Counter): A Counter of measurements. Key is the measurements
                in a big endian binary string. Value is the number of times that measurement
                occurred.

        Returns:
            Dict[str, float]: A dictionary of probabilistic results. Key is the measurements
                in a big endian binary string. Value is the probability the measurement occurred.
        """
        measurement_probabilities = {}
        shots = sum(measurement_counts.values())

        for key, count in measurement_counts.items():
            measurement_probabilities[key] = count / shots
        return measurement_probabilities

    @staticmethod
    def measurements_from_measurement_probabilities(
        measurement_probabilities: Dict[str, float], shots: int
    ) -> np.ndarray:
        """
        Creates measurements from measurement probabilities

        Args:
            measurement_probabilities (Dict[str, float]): A dictionary of probabilistic results.
                Key is the measurements in a big endian binary string.
                Value is the probability the measurement occurred.
            shots (int): number of iterations on device

        Returns:
            Dict[str, float]: A dictionary of probabilistic results.
                Key is the measurements in a big endian binary string.
                Value is the probability the measurement occurred.
        """
        measurements_list = []
        for bitstring in measurement_probabilities:
            measurement = list(bitstring)
            individual_measurement_list = [measurement] * int(
                round(measurement_probabilities[bitstring] * shots)
            )
            measurements_list.extend(individual_measurement_list)
        return np.asarray(measurements_list, dtype=int)
