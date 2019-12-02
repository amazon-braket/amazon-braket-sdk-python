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

from typing import Counter

import numpy as np
from braket.tasks import QuantumTaskResult


def test_measurement_counts_from_measurements():
    measurements: np.ndarray = np.array(
        [[1, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 1, 0]]
    )
    measurement_counts = QuantumTaskResult.measurement_counts_from_measurements(measurements)
    expected_counts: Counter = {"1010": 3, "0000": 1, "1000": 2}
    assert expected_counts == measurement_counts


def test_measurement_probabilities_from_measurement_counts():
    counts = {"00": 1, "01": 1, "10": 1, "11": 97}
    probabilities = {"00": 0.01, "01": 0.01, "10": 0.01, "11": 0.97}

    measurement_probabilities = QuantumTaskResult.measurement_probabilities_from_measurement_counts(
        counts
    )

    assert measurement_probabilities == probabilities


def test_measurements_from_measurement_probabilities():
    shots = 5
    probabilities = {"00": 0.2, "01": 0.2, "10": 0.2, "11": 0.4}
    measurements_list = [["0", "0"], ["0", "1"], ["1", "0"], ["1", "1"], ["1", "1"]]
    expected_results = np.asarray(measurements_list, dtype=int)

    measurements = QuantumTaskResult.measurements_from_measurement_probabilities(
        probabilities, shots
    )

    assert np.allclose(measurements, expected_results)


def test_equality():
    measurements_1 = np.array([[0, 0], [1, 1]])
    measurements_2 = np.array([[0, 0], [0, 0]])

    result_1 = QuantumTaskResult(measurements_1, None, None, False, True, True)
    result_2 = QuantumTaskResult(measurements_1, None, None, False, True, True)
    other_result = QuantumTaskResult(measurements_2, None, None, False, True, True)
    non_result = "not a quantum task result"

    assert result_1 == result_2
    assert result_1 is not result_2
    assert result_1 != other_result
    assert result_1 != non_result
