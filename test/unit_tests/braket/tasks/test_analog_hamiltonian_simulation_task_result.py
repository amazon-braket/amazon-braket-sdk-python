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

import numpy as np
import pytest

from braket.task_result import (
    AnalogHamiltonianSimulationShotMeasurement,
    AnalogHamiltonianSimulationShotMetadata,
    AnalogHamiltonianSimulationShotResult,
    AnalogHamiltonianSimulationTaskResult,
    TaskMetadata,
)
from braket.tasks import (
    AnalogHamiltonianSimulationQuantumTaskResult,
    AnalogHamiltonianSimulationShotStatus,
)
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import ShotResult


@pytest.fixture
def task_metadata():
    return TaskMetadata(**{"id": "task_arn", "deviceId": "arn1", "shots": 100})


@pytest.fixture
def success_measurement():
    return AnalogHamiltonianSimulationShotMeasurement(
        shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Success"),
        shotResult=AnalogHamiltonianSimulationShotResult(
            preSequence=[1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
            postSequence=[0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0],
        ),
    )


@pytest.fixture
def partial_success_measurement():
    return AnalogHamiltonianSimulationShotMeasurement(
        shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Partial Success"),
        shotResult=AnalogHamiltonianSimulationShotResult(
            preSequence=[1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1], postSequence=None
        ),
    )


@pytest.fixture
def error_measurement():
    return AnalogHamiltonianSimulationShotMeasurement(
        shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Failure"),
        shotResult=AnalogHamiltonianSimulationShotResult(preSequence=None, postSequence=None),
    )


@pytest.fixture
def measurements(success_measurement, partial_success_measurement, error_measurement):
    return [success_measurement, partial_success_measurement, error_measurement]


@pytest.fixture
def result_str_1(task_metadata, measurements):
    result = AnalogHamiltonianSimulationTaskResult(
        taskMetadata=task_metadata,
        measurements=measurements,
    )
    return result.json()


@pytest.fixture
def result_str_2(task_metadata, measurements):
    result = AnalogHamiltonianSimulationTaskResult(
        taskMetadata=task_metadata,
        measurements=None,
    )
    return result.json()


def validate_result_from_str_1(result):
    assert len(result.measurements) == 3
    assert result.measurements[0].status == AnalogHamiltonianSimulationShotStatus.SUCCESS
    np.testing.assert_equal(result.measurements[0].pre_sequence, [1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1])
    np.testing.assert_equal(result.measurements[0].post_sequence, [0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0])
    assert result.measurements[1].status == AnalogHamiltonianSimulationShotStatus.PARTIAL_SUCCESS
    np.testing.assert_equal(result.measurements[1].pre_sequence, [1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1])
    assert result.measurements[1].post_sequence is None
    assert result.measurements[2].status == AnalogHamiltonianSimulationShotStatus.FAILURE
    assert result.measurements[2].pre_sequence is None
    assert result.measurements[2].post_sequence is None


def test_from_object(result_str_1, task_metadata):
    result = AnalogHamiltonianSimulationQuantumTaskResult.from_object(
        AnalogHamiltonianSimulationTaskResult.parse_raw(result_str_1)
    )
    assert result.task_metadata == task_metadata
    validate_result_from_str_1(result)


def test_from_string(result_str_1, task_metadata):
    result = AnalogHamiltonianSimulationQuantumTaskResult.from_string(result_str_1)
    assert result.task_metadata == task_metadata
    validate_result_from_str_1(result)


def test_from_object_equal_to_from_string(result_str_1):
    assert AnalogHamiltonianSimulationQuantumTaskResult.from_object(
        AnalogHamiltonianSimulationTaskResult.parse_raw(result_str_1)
    ) == AnalogHamiltonianSimulationQuantumTaskResult.from_string(result_str_1)


def test_equality(task_metadata, result_str_1, result_str_2):
    result_1 = AnalogHamiltonianSimulationQuantumTaskResult.from_string(result_str_1)
    result_2 = AnalogHamiltonianSimulationQuantumTaskResult.from_string(result_str_1)
    other_result = AnalogHamiltonianSimulationQuantumTaskResult.from_string(result_str_2)
    non_result = "not a quantum task result"

    assert result_1 == result_2
    assert result_1 is not result_2
    assert result_1 != other_result
    assert result_1 != AnalogHamiltonianSimulationQuantumTaskResult(
        task_metadata=task_metadata,
        measurements=[result_1.measurements[1], result_1.measurements[0]],
    )
    assert result_1 != non_result


@pytest.mark.parametrize(
    "shot0, shot1",
    [
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [], []),
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [], []),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.FAILURE, [1], [2]),
            ShotResult(AnalogHamiltonianSimulationShotStatus.FAILURE, [1], [2]),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, None, None),
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, None, None),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, None, [1, 2]),
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, None, [1, 2]),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [1, 2], None),
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [1, 2], None),
        ),
    ],
)
def test_shot_result_equals(shot0, shot1):
    assert shot0 == shot1


@pytest.mark.parametrize(
    "shot0, shot1",
    [
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [], []),
            ShotResult(AnalogHamiltonianSimulationShotStatus.FAILURE, [], []),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [1], [2]),
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [2], [1]),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [1], [2]),
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, None, [2]),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [1], None),
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [1], [2]),
        ),
        (
            ShotResult(AnalogHamiltonianSimulationShotStatus.SUCCESS, [1], None),
            "not a shot",
        ),
    ],
)
def test_shot_result_not_equals(shot0, shot1):
    assert shot0 != shot1
