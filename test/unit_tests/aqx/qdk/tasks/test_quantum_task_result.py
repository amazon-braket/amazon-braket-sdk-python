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
from unittest.mock import patch

import numpy as np
from aqx.qdk.tasks import QuantumTaskResult


def test_measurement_counts_build_from_measurement():
    measurements: np.ndarray = np.array(
        [[1, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 1, 0]]
    )
    result: QuantumTaskResult = QuantumTaskResult(measurements)
    expected_counts: Counter = {"1010": 3, "0000": 1, "1000": 2}
    assert expected_counts == result.measurement_counts()


def test_measurement_counts_caches_result():
    measurements: np.ndarray = np.array(
        [[1, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 1, 0]]
    )
    result: QuantumTaskResult = QuantumTaskResult(measurements)
    expected_counts: Counter = {"1010": 3, "0000": 1, "1000": 2}

    # Assert lazily loaded
    assert result._measurement_counts is None
    assert result.measurement_counts() == expected_counts

    # Assert uses now cached value
    assert result._measurement_counts == result.measurement_counts()


def test_measurement_probabilities_built_from_counts():
    counts = {"00": 1, "01": 1, "10": 1, "11": 97}
    probabilities = {"00": 0.01, "01": 0.01, "10": 0.01, "11": 0.97}

    with patch.object(QuantumTaskResult, "measurement_counts") as mock_method:
        mock_method.return_value = counts
        result = QuantumTaskResult(measurements=None)

        assert result.measurement_counts() == counts
        assert result.measurement_probabilities() == probabilities


def test_measurement_probabilities_caches_result():
    counts = {"00": 1, "01": 1, "10": 1, "11": 97}
    probabilities = {"00": 0.01, "01": 0.01, "10": 0.01, "11": 0.97}

    with patch.object(QuantumTaskResult, "measurement_counts") as mock_method:
        mock_method.return_value = counts
        result = QuantumTaskResult(measurements=None)

        # Assert lazily loaded
        assert result._measurement_probabilities is None
        assert result.measurement_probabilities() == probabilities
        assert result._measurement_probabilities is not None

        # Assert uses now cached value
        assert result._measurement_probabilities == result.measurement_probabilities()


def test_equality():
    measurements_1 = np.array([[0, 0], [1, 1]])
    measurements_2 = np.array([[0, 0], [0, 0]])

    result_1 = QuantumTaskResult(measurements_1)
    result_2 = QuantumTaskResult(measurements_1)
    other_result = QuantumTaskResult(measurements_2)
    non_result = "not a quantum task result"

    assert result_1 == result_2
    assert result_1 is not result_2
    assert result_1 != other_result
    assert result_1 != non_result
