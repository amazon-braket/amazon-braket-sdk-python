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
    """

    measurements: np.ndarray

    def __post_init__(self):
        self._measurement_counts = None
        self._measurement_probabilities = None

    def measurement_counts(self) -> Counter:
        """
        A Counter of results. This data is lazily loaded, populated based on `measurements`,
        and cached for further calls.

        Returns:
            Counter: Counts based on self. Key is the measurements in a big endian binary string.
            Value is the number of times that measurement occurred.

        Examples:
            >>> measurements: np.ndarray = np.array(
                [[1, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 1, 0]]
            )
            >>> result = QuantumTaskResult(measurements)
            >>> result.measurement_counts()
            {"1010": 3, "0000": 1, "1000": 2}
        """

        if self._measurement_counts is None:
            bitstrings = []
            for j in range(len(self.measurements)):
                bitstrings.append("".join([str(element) for element in self.measurements[j]]))
            self._measurement_counts = Counter(bitstrings)

        return self._measurement_counts

    def measurement_probabilities(self) -> Dict[str, float]:
        """
        A dictionary of probabilistic results. This data is lazily loaded, populated based on
        `measurement_counts`, and cached for further calls.

        Returns:
            Dict[str, float]: Key is the measurements in a big endian binary string.
            Value is the probability the measurement occurred.

        Examples:
            >>> result = QuantumTaskResult(measurements)
            >>> result.measurement_counts()
            {"00": 1, "01": 1, "10": 1, "11": 97}
            >>> print(result.measurement_probabilities())
            {"00": 0.01, "01": 0.01, "10": 0.01, "11": 0.97}
        """

        if self._measurement_probabilities is None:
            self._measurement_probabilities = {}
            shots = sum(self.measurement_counts().values())

            for key, count in self.measurement_counts().items():
                self._measurement_probabilities[key] = count / shots

        return self._measurement_probabilities

    def __eq__(self, other) -> bool:
        if isinstance(other, QuantumTaskResult):
            # __eq__ on numpy arrays results in an array of booleans and therefore can't use
            # the default dataclass __eq__ implementation. Override equals to check if all
            # elements in the array are equal.
            return (self.measurements == other.measurements).all()
        return NotImplemented
