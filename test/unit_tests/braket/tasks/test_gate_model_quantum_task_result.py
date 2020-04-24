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

import copy
import json
from typing import Any, Counter, Dict

import numpy as np
import pytest
from braket.aws.aws_qpu_arns import AwsQpuArns
from braket.circuits import Observable, ResultType
from braket.tasks import GateModelQuantumTaskResult


@pytest.fixture
def result_dict_1():
    return {
        "Measurements": [[0, 0], [0, 1], [0, 1], [0, 1]],
        "TaskMetadata": {
            "Id": "UUID_blah_1",
            "Status": "COMPLETED",
            "BackendArn": AwsQpuArns.RIGETTI,
            "Shots": 1000,
            "Ir": json.dumps({"results": []}),
        },
    }


@pytest.fixture
def result_str_1(result_dict_1):
    return json.dumps(result_dict_1)


@pytest.fixture
def result_str_2():
    return json.dumps(
        {
            "Measurements": [[0, 0], [0, 0], [0, 0], [1, 1]],
            "TaskMetadata": {
                "Id": "UUID_blah_2",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.RIGETTI,
                "Shots": 1000,
                "Ir": json.dumps({"results": []}),
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
                "Ir": json.dumps({"results": []}),
            },
            "MeasurementProbabilities": {"011000": 0.9999999999999982},
        }
    )


@pytest.fixture
def result_dict_4():
    return {
        "TaskMetadata": {
            "Id": "1231231",
            "Shots": 0,
            "GateModelConfig": {"QubitCount": 2},
            "Ir": json.dumps({"results": []}),
        },
        "ResultTypes": [
            {"Type": {"targets": [0], "type": "probability"}, "Value": np.array([0.5, 0.5])},
            {
                "Type": {"type": "statevector"},
                "Value": np.array([complex(0.70710678, 0), 0, 0, complex(0.70710678, 0)]),
            },
            {"Type": {"targets": [0], "type": "expectation", "observable": ["y"]}, "Value": 0.0},
            {"Type": {"targets": [0], "type": "variance", "observable": ["y"]}, "Value": 0.1},
            {
                "Type": {"type": "amplitude", "states": ["00"]},
                "Value": {"00": complex(0.70710678, 0)},
            },
        ],
    }


@pytest.fixture
def result_str_4(result_dict_4):
    result = copy.deepcopy(result_dict_4)
    result["ResultTypes"] = [
        {"Type": {"targets": [0], "type": "probability"}, "Value": [0.5, 0.5]},
        {
            "Type": {"type": "statevector"},
            "Value": [(0.70710678, 0), (0, 0), (0, 0), (0.70710678, 0)],
        },
        {"Type": {"targets": [0], "type": "expectation", "observable": ["y"]}, "Value": 0.0},
        {"Type": {"targets": [0], "type": "variance", "observable": ["y"]}, "Value": 0.1},
        {"Type": {"type": "amplitude", "states": ["00"]}, "Value": {"00": (0.70710678, 0)}},
    ]
    return json.dumps(result)


@pytest.fixture
def malformatted_results():
    return {
        "TaskMetadata": {
            "Id": "UUID_blah_1",
            "Status": "COMPLETED",
            "BackendArn": AwsQpuArns.RIGETTI,
            "Shots": 1000,
            "Ir": json.dumps({"results": []}),
        },
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


def test_from_dict_measurements(result_dict_1):
    task_result = GateModelQuantumTaskResult.from_dict(result_dict_1)
    expected_measurements = np.asarray(result_dict_1["Measurements"], dtype=int)
    assert task_result.task_metadata == result_dict_1["TaskMetadata"]
    assert np.array2string(task_result.measurements) == np.array2string(expected_measurements)
    assert not task_result.measurement_counts_copied_from_device
    assert not task_result.measurement_probabilities_copied_from_device
    assert task_result.measurements_copied_from_device


def test_from_dict_measurement_probabilities(result_str_3):
    result_obj = json.loads(result_str_3)
    task_result = GateModelQuantumTaskResult.from_dict(result_obj)
    assert task_result.measurement_probabilities == result_obj["MeasurementProbabilities"]
    assert task_result.task_metadata == result_obj["TaskMetadata"]
    shots = 100
    measurement_list = [list("011000") for x in range(shots)]
    expected_measurements = np.asarray(measurement_list, dtype=int)
    assert np.allclose(task_result.measurements, expected_measurements)
    assert task_result.measurement_counts == Counter(["011000" for x in range(shots)])
    assert not task_result.measurement_counts_copied_from_device
    assert task_result.measurement_probabilities_copied_from_device
    assert not task_result.measurements_copied_from_device


def test_from_string_measurements(result_str_1):
    result_obj = json.loads(result_str_1)
    task_result = GateModelQuantumTaskResult.from_string(result_str_1)
    expected_measurements = np.asarray(result_obj["Measurements"], dtype=int)
    assert task_result.task_metadata == result_obj["TaskMetadata"]
    assert np.array2string(task_result.measurements) == np.array2string(expected_measurements)
    assert not task_result.measurement_counts_copied_from_device
    assert not task_result.measurement_probabilities_copied_from_device
    assert task_result.measurements_copied_from_device


def test_from_string_measurement_probabilities(result_str_3):
    result_obj = json.loads(result_str_3)
    task_result = GateModelQuantumTaskResult.from_string(result_str_3)
    assert task_result.measurement_probabilities == result_obj["MeasurementProbabilities"]
    assert task_result.task_metadata == result_obj["TaskMetadata"]
    shots = 100
    measurement_list = [list("011000") for x in range(shots)]
    expected_measurements = np.asarray(measurement_list, dtype=int)
    assert np.allclose(task_result.measurements, expected_measurements)
    assert task_result.measurement_counts == Counter(["011000" for x in range(shots)])
    assert not task_result.measurement_counts_copied_from_device
    assert task_result.measurement_probabilities_copied_from_device
    assert not task_result.measurements_copied_from_device


def test_from_dict_equal_to_from_string(result_dict_1, result_str_1, result_str_3):
    assert GateModelQuantumTaskResult.from_dict(
        result_dict_1
    ) == GateModelQuantumTaskResult.from_string(result_str_1)
    assert GateModelQuantumTaskResult.from_dict(
        json.loads(result_str_3)
    ) == GateModelQuantumTaskResult.from_string(result_str_3)


def test_equality(result_str_1, result_str_2):
    result_1 = GateModelQuantumTaskResult.from_string(result_str_1)
    result_2 = GateModelQuantumTaskResult.from_string(result_str_1)
    other_result = GateModelQuantumTaskResult.from_string(result_str_2)
    non_result = "not a quantum task result"

    assert result_1 == result_2
    assert result_1 is not result_2
    assert result_1 != other_result
    assert result_1 != non_result


def test_from_string_simulator_only(result_dict_4, result_str_4):
    result = GateModelQuantumTaskResult.from_string(result_str_4)
    assert len(result.result_types) == len(result_dict_4["ResultTypes"])
    for i in range(len(result.result_types)):
        rt = result.result_types[i]
        expected_rt = result_dict_4["ResultTypes"][i]
        assert rt["Type"] == expected_rt["Type"]
        if isinstance(rt["Value"], np.ndarray):
            assert np.allclose(rt["Value"], expected_rt["Value"])
        else:
            assert rt["Value"] == expected_rt["Value"]
    assert result.task_metadata == result.task_metadata


def test_get_value_by_result_type(result_dict_4):
    result = GateModelQuantumTaskResult.from_dict(result_dict_4)
    assert np.allclose(
        result.get_value_by_result_type(ResultType.Probability(target=0)), result.values[0]
    )
    assert np.allclose(result.get_value_by_result_type(ResultType.StateVector()), result.values[1])
    assert (
        result.get_value_by_result_type(ResultType.Expectation(observable=Observable.Y(), target=0))
        == result.values[2]
    )
    assert (
        result.get_value_by_result_type(ResultType.Variance(observable=Observable.Y(), target=0))
        == result.values[3]
    )
    assert result.get_value_by_result_type(ResultType.Amplitude(state=["00"])) == result.values[4]


@pytest.mark.xfail(raises=ValueError)
def test_get_value_by_result_type_value_error(result_dict_4):
    result = GateModelQuantumTaskResult.from_dict(result_dict_4)
    result.get_value_by_result_type(ResultType.Probability(target=[0, 1]))


@pytest.mark.xfail(raises=ValueError)
def test_bad_dict(malformatted_results):
    GateModelQuantumTaskResult.from_dict(malformatted_results)


@pytest.mark.xfail(raises=ValueError)
def test_bad_string(malformatted_results):
    results_string = json.dumps(malformatted_results)
    GateModelQuantumTaskResult.from_string(results_string)
