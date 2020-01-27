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

import numpy as np
import pytest
from braket.aws.aws_qpu_arns import AwsQpuArns
from braket.tasks import GateModelQuantumTaskResult


@pytest.fixture
def result_str_1():
    return json.dumps(
        {
            "StateVector": {"00": [0.2, 0.2], "01": [0.3, 0.1], "10": [0.1, 0.3], "11": [0.2, 0.2]},
            "Measurements": [[0, 0], [0, 1], [0, 1], [0, 1]],
            "TaskMetadata": {
                "Id": "UUID_blah_1",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.RIGETTI,
            },
        }
    )


@pytest.fixture
def result_str_2():
    return json.dumps(
        {
            "StateVector": {"00": [0.2, 0.2], "01": [0.3, 0.1], "10": [0.1, 0.3], "11": [0.2, 0.2]},
            "Measurements": [[0, 0], [0, 0], [0, 0], [1, 1]],
            "TaskMetadata": {
                "Id": "UUID_blah_2",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.RIGETTI,
            },
        }
    )


@pytest.fixture
def result_str_3():
    return json.dumps(
        {
            "TaskMetadata": {
                "Id": "1231231",
                "Status": "COMPLETED",
                "BackendArn": "test_arn",
                "BackendTranslation": "...",
                "Created": 1574140385.0697668,
                "Modified": 1574140388.6908717,
                "Shots": 100,
                "GateModelConfig": {"QubitCount": 6},
            },
            "MeasurementProbabilities": {"011000": 0.9999999999999982},
        }
    )


@pytest.fixture
def parsed_state_vector():
    return {
        "00": complex(0.2, 0.2),
        "01": complex(0.3, 0.1),
        "10": complex(0.1, 0.3),
        "11": complex(0.2, 0.2),
    }


def test_measurement_counts_from_measurements():
    measurements: np.ndarray = np.array(
        [[1, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 1, 0]]
    )
    measurement_counts = GateModelQuantumTaskResult.measurement_counts_from_measurements(
        measurements
    )
    expected_counts: Counter = {"1010": 3, "0000": 1, "1000": 2}
    assert expected_counts == measurement_counts


def test_measurement_probabilities_from_measurement_counts():
    counts = {"00": 1, "01": 1, "10": 1, "11": 97}
    probabilities = {"00": 0.01, "01": 0.01, "10": 0.01, "11": 0.97}

    m_probabilities = GateModelQuantumTaskResult.measurement_probabilities_from_measurement_counts(
        counts
    )

    assert m_probabilities == probabilities


def test_measurements_from_measurement_probabilities():
    shots = 5
    probabilities = {"00": 0.2, "01": 0.2, "10": 0.2, "11": 0.4}
    measurements_list = [["0", "0"], ["0", "1"], ["1", "0"], ["1", "1"], ["1", "1"]]
    expected_results = np.asarray(measurements_list, dtype=int)

    measurements = GateModelQuantumTaskResult.measurements_from_measurement_probabilities(
        probabilities, shots
    )

    assert np.allclose(measurements, expected_results)


def test_state_vector(parsed_state_vector):
    result: GateModelQuantumTaskResult = GateModelQuantumTaskResult(
        measurements=None,
        task_metadata=None,
        state_vector=parsed_state_vector,
        measurement_counts=None,
        measurement_probabilities=None,
        measurements_copied_from_device=False,
        measurement_counts_copied_from_device=False,
        measurement_probabilities_copied_from_device=False,
    )
    assert result.state_vector == parsed_state_vector


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
    result: GateModelQuantumTaskResult = GateModelQuantumTaskResult(
        measurements=None,
        task_metadata=task_metadata,
        measurement_counts=None,
        measurement_probabilities=None,
        measurements_copied_from_device=False,
        measurement_counts_copied_from_device=False,
        measurement_probabilities_copied_from_device=False,
    )
    assert result.task_metadata == task_metadata


def test_from_string_measurements(result_str_1, parsed_state_vector):
    result_obj = json.loads(result_str_1)
    task_result = GateModelQuantumTaskResult.from_string(result_str_1)
    expected_measurements = np.asarray(result_obj["Measurements"], dtype=int)
    assert task_result.task_metadata == result_obj["TaskMetadata"]
    assert task_result.state_vector == parsed_state_vector
    assert np.array2string(task_result.measurements) == np.array2string(expected_measurements)
    assert not task_result.measurement_counts_copied_from_device
    assert not task_result.measurement_probabilities_copied_from_device
    assert task_result.measurements_copied_from_device


def test_from_string_measurement_probabilities(result_str_3):
    result_obj = json.loads(result_str_3)
    task_result = GateModelQuantumTaskResult.from_string(result_str_3)
    assert task_result.measurement_probabilities == result_obj["MeasurementProbabilities"]
    assert task_result.task_metadata == result_obj["TaskMetadata"]
    assert task_result.state_vector is None
    shots = 100
    measurement_list = [list("011000") for x in range(shots)]
    expected_measurements = np.asarray(measurement_list, dtype=int)
    assert np.allclose(task_result.measurements, expected_measurements)
    assert task_result.measurement_counts == Counter(["011000" for x in range(shots)])
    assert not task_result.measurement_counts_copied_from_device
    assert task_result.measurement_probabilities_copied_from_device
    assert not task_result.measurements_copied_from_device


def test_equality(result_str_1, result_str_2):
    result_1 = GateModelQuantumTaskResult.from_string(result_str_1)
    result_2 = GateModelQuantumTaskResult.from_string(result_str_1)
    other_result = GateModelQuantumTaskResult.from_string(result_str_2)
    non_result = "not a quantum task result"

    assert result_1 == result_2
    assert result_1 is not result_2
    assert result_1 != other_result
    assert result_1 != non_result
