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

import json
from typing import Any, Counter, Dict
from unittest.mock import patch

import numpy as np
import pytest
from aqx.qdk.aws.aws_quantum_task_result import AwsQuantumTaskResult

from common_test_utils import MockS3


@pytest.fixture
def result_str_1():
    return MockS3.MOCK_S3_RESULT_1


@pytest.fixture
def result_str_2():
    return MockS3.MOCK_S3_RESULT_2


def test_state_vector():
    state_vector: Dict[str, float] = {"00": 0.00, "01": 0.50, "10": 0.50, "11": 0.00}
    result: AwsQuantumTaskResult = AwsQuantumTaskResult(
        measurements=None, task_metadata=None, state_vector=state_vector
    )
    assert result.state_vector == state_vector


def test_task_metadata():
    task_metadata: Dict[str, Any] = {
        "Id": "UUID_blah",
        "Status": "COMPLETED",
        "BackendArn": "Rigetti_Arn",
        "CwLogGroupArn": "blah",
        "Program": "....",
        "CreatedAt": "02/12/22 21:23",
        "UpdatedAt": "02/13/22 21:23",
    }
    result: AwsQuantumTaskResult = AwsQuantumTaskResult(
        measurements=None, task_metadata=task_metadata
    )
    assert result.task_metadata == task_metadata


def test_measurement_counts():
    measurement: np.ndarray = np.array(
        [[1, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 1, 0]]
    )
    result: AwsQuantumTaskResult = AwsQuantumTaskResult(measurement, task_metadata=None)
    expected_counts: Counter = {"1010": 3, "0000": 1, "1000": 2}
    assert expected_counts == result.measurement_counts()


def test_measurement_probabilities():
    counts = {"00": 1, "01": 1, "10": 1, "11": 97}
    probabilities = {"00": 0.01, "01": 0.01, "10": 0.01, "11": 0.97}

    with patch.object(AwsQuantumTaskResult, "measurement_counts") as mock_method:
        mock_method.return_value = counts
        result = AwsQuantumTaskResult(measurements=None, task_metadata=None)

        assert result.measurement_counts() == counts
        assert result.measurement_probabilities() == probabilities


def test_from_string(result_str_1):
    result_obj = json.loads(result_str_1)
    task_result = AwsQuantumTaskResult.from_string(result_str_1)
    expected_measurements = np.asarray(result_obj["Measurements"], dtype=int)
    assert task_result.task_metadata == result_obj["TaskMetadata"]
    assert task_result.state_vector == result_obj["StateVector"]
    assert np.array2string(task_result.measurements) == np.array2string(expected_measurements)


def test_equality(result_str_1, result_str_2):
    result_1 = AwsQuantumTaskResult.from_string(result_str_1)
    result_2 = AwsQuantumTaskResult.from_string(result_str_1)
    other_result = AwsQuantumTaskResult.from_string(result_str_2)
    non_result = "not a aws quantum task result"

    assert result_1 == result_2
    assert result_1 is not result_2
    assert result_1 != other_result
    assert result_1 != non_result
