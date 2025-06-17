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

from braket.ir.ahs import Program
from braket.task_result import (
    AdditionalMetadata,
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
def additional_metadata():
    return AdditionalMetadata(
        action=Program(
            setup={
                "ahs_register": {
                    "sites": [
                        [0.0, 0.0],
                        [0.0, 3.0e-6],
                        [0.0, 6.0e-6],
                        [3.0e-6, 0.0],
                        [3.0e-6, 3.0e-6],
                        [3.0e-6, 6.0e-6],
                    ],
                    "filling": [1, 1, 1, 1, 0, 0],
                }
            },
            hamiltonian={
                "drivingFields": [
                    {
                        "amplitude": {
                            "time_series": {
                                "values": [0.0, 2.51327e7, 2.51327e7, 0.0],
                                "times": [0.0, 3.0e-7, 2.7e-6, 3.0e-6],
                            },
                            "pattern": "uniform",
                        },
                        "phase": {
                            "time_series": {"values": [0, 0], "times": [0.0, 3.0e-6]},
                            "pattern": "uniform",
                        },
                        "detuning": {
                            "time_series": {
                                "values": [-1.25664e8, -1.25664e8, 1.25664e8, 1.25664e8],
                                "times": [0.0, 3.0e-7, 2.7e-6, 3.0e-6],
                            },
                            "pattern": "uniform",
                        },
                    }
                ],
                "localDetuning": [
                    {
                        "magnitude": {
                            "time_series": {
                                "values": [-1.25664e8, 1.25664e8],
                                "times": [0.0, 3.0e-6],
                            },
                            "pattern": [0.5, 1.0, 0.5, 0.5, 0.5, 0.5],
                        }
                    }
                ],
            },
        )
    )


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
def failed_measurement():
    return AnalogHamiltonianSimulationShotMeasurement(
        shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Failure"),
        shotResult=AnalogHamiltonianSimulationShotResult(preSequence=None, postSequence=None),
    )


@pytest.fixture
def success_measurement_extended():
    return AnalogHamiltonianSimulationShotMeasurement(
        shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Success"),
        shotResult=AnalogHamiltonianSimulationShotResult(
            preSequence=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            postSequence=[1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1],
        ),
    )


@pytest.fixture
def measurements(success_measurement, partial_success_measurement, failed_measurement):
    return [success_measurement, partial_success_measurement, failed_measurement]


@pytest.fixture
def measurements_extended(
    success_measurement,
    success_measurement_extended,
):
    return [
        success_measurement,
        success_measurement_extended,
    ]


@pytest.fixture
def result_str_1(task_metadata, additional_metadata, measurements):
    result = AnalogHamiltonianSimulationTaskResult(
        taskMetadata=task_metadata,
        additionalMetadata=additional_metadata,
        measurements=measurements,
    )
    return result.json()


@pytest.fixture
def result_str_2(task_metadata, additional_metadata, measurements):
    result = AnalogHamiltonianSimulationTaskResult(
        taskMetadata=task_metadata,
        additionalMetadata=additional_metadata,
        measurements=None,
    )
    return result.json()


@pytest.fixture
def result_str_3(task_metadata, additional_metadata, measurements_extended):
    result = AnalogHamiltonianSimulationTaskResult(
        taskMetadata=task_metadata,
        additionalMetadata=additional_metadata,
        measurements=measurements_extended,
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
    assert result.additional_metadata.action is not None


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
        additional_metadata=additional_metadata,
        measurements=[result_1.measurements[1], result_1.measurements[0]],
    )
    assert result_1 != non_result


def test_get_counts(result_str_3):
    result = AnalogHamiltonianSimulationQuantumTaskResult.from_string(result_str_3)

    counts = result.get_counts()
    # Partial Success and Failure result status are mapped to counts = None
    expected_counts = {"rrrgeggrrgr": 1, "grggrgrrrrg": 1}
    assert counts == expected_counts


def test_get_counts_failed_task(task_metadata):
    measurement = ShotResult(AnalogHamiltonianSimulationShotStatus.FAILURE, [], [])
    result = AnalogHamiltonianSimulationQuantumTaskResult(
        task_metadata=task_metadata,
        additional_metadata=additional_metadata,
        measurements=[measurement],
    )

    counts = result.get_counts()
    expected_counts = {}
    assert counts == expected_counts


def test_avg_density(result_str_3):
    result = AnalogHamiltonianSimulationQuantumTaskResult.from_string(result_str_3)

    density = result.get_avg_density()
    expected_density = [0.5, 1.0, 0.5, 0.0, 1.0, 0.0, 0.5, 1.0, 1.0, 0.5, 0.5]
    np.testing.assert_almost_equal(density, expected_density)


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
