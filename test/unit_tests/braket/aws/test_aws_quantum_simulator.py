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

from unittest.mock import Mock, patch

import pytest
from common_test_utils import SIMULATOR_ARN, MockDevices, run_and_assert

from braket.aws import AwsQuantumSimulator
from braket.circuits import Circuit


@pytest.fixture
def simulator():
    def _simulator(arn):
        mock_session = Mock()
        mock_session.get_simulator_metadata.return_value = MockDevices.MOCK_QS1_SIMULATOR_1
        return AwsQuantumSimulator(arn, mock_session)

    return _simulator


@pytest.fixture
def circuit():
    return Circuit().h(0)


@pytest.fixture
def s3_destination_folder():
    return ("bucket-foo", "key-bar")


def test_simulator_refresh_metadata_success():
    mock_session = Mock()
    expected_metadata = MockDevices.MOCK_QS1_SIMULATOR_1
    mock_session.get_simulator_metadata.return_value = expected_metadata
    simulator = AwsQuantumSimulator(SIMULATOR_ARN, mock_session)
    assert simulator.arn == expected_metadata.get("arn")
    assert simulator.name == expected_metadata.get("name")
    assert simulator.properties["qubitCount"] == expected_metadata.get("qubitCount")
    assert simulator.properties["supportedQuantumOperations"] == expected_metadata.get(
        "supportedQuantumOperations"
    )
    assert simulator.properties["supportedResultTypes"] == expected_metadata.get(
        "supportedResultTypes"
    )
    assert simulator.status == expected_metadata.get("status")
    assert simulator.status_reason is None

    # describe_simulators now returns new metadata
    expected_metadata = MockDevices.MOCK_QS1_SIMULATOR_2
    mock_session.get_simulator_metadata.return_value = expected_metadata
    simulator.refresh_metadata()
    assert simulator.arn == expected_metadata.get("arn")
    assert simulator.name == expected_metadata.get("name")
    assert simulator.properties["qubitCount"] == expected_metadata.get("qubitCount")
    assert simulator.properties["supportedQuantumOperations"] == expected_metadata.get(
        "supportedQuantumOperations"
    )
    assert simulator.properties["supportedResultTypes"] == expected_metadata.get(
        "supportedResultTypes"
    )
    assert simulator.status == expected_metadata.get("status")
    assert simulator.status_reason == expected_metadata.get("statusReason")


def test_simulator_refresh_metadata_error():
    mock_session = Mock()
    err_message = "nooo!"
    mock_session.get_simulator_metadata.side_effect = RuntimeError(err_message)
    with pytest.raises(RuntimeError) as excinfo:
        AwsQuantumSimulator(SIMULATOR_ARN, mock_session)
    assert err_message in str(excinfo.value)


def test_equality(simulator):
    simulator_1 = simulator(SIMULATOR_ARN)
    simulator_2 = simulator(SIMULATOR_ARN)
    other_simulator = Mock(spec=AwsQuantumSimulator)
    other_simulator.arn.return_value = "OTHER_ARN"
    non_simulator = "HI"

    assert simulator_1 == simulator_2
    assert simulator_1 is not simulator_2
    assert simulator_1 != other_simulator
    assert simulator_1 != non_simulator


def test_repr(simulator):
    simulator = simulator(SIMULATOR_ARN)
    expected = "QuantumSimulator('name': {}, 'arn': {})".format(simulator.name, simulator.arn)
    assert repr(simulator) == expected


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_positional_args(aws_quantum_task_mock, simulator, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock, simulator, circuit, s3_destination_folder, 1000, 300, 1, ["foo"]
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_kwargs(aws_quantum_task_mock, simulator, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        simulator,
        circuit,
        s3_destination_folder,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots(aws_quantum_task_mock, simulator, circuit, s3_destination_folder):
    _run_and_assert(aws_quantum_task_mock, simulator, circuit, s3_destination_folder, 1000)


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots_kwargs(aws_quantum_task_mock, simulator, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        simulator,
        circuit,
        s3_destination_folder,
        1000,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots_poll_timeout_kwargs(
    aws_quantum_task_mock, simulator, circuit, s3_destination_folder
):
    _run_and_assert(
        aws_quantum_task_mock,
        simulator,
        circuit,
        s3_destination_folder,
        1000,
        300,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_positional_args_and_kwargs(
    aws_quantum_task_mock, simulator, circuit, s3_destination_folder
):
    _run_and_assert(
        aws_quantum_task_mock,
        simulator,
        circuit,
        s3_destination_folder,
        1000,
        300,
        1,
        ["foo"],
        {"bar": 1, "baz": 2},
    )


def _run_and_assert(
    aws_quantum_task_mock,
    simulator_factory,
    circuit,
    s3_destination_folder,
    shots=None,  # Treated as positional arg
    poll_timeout_seconds=None,  # Treated as positional arg
    poll_interval_seconds=None,  # Treated as positional arg
    extra_args=None,
    extra_kwargs=None,
):
    run_and_assert(
        aws_quantum_task_mock,
        simulator_factory(SIMULATOR_ARN),
        AwsQuantumSimulator.DEFAULT_SHOTS_SIMULATOR,
        AwsQuantumSimulator.DEFAULT_RESULTS_POLL_TIMEOUT_SIMULATOR,
        AwsQuantumSimulator.DEFAULT_RESULTS_POLL_INTERVAL_SIMULATOR,
        circuit,
        s3_destination_folder,
        shots,
        poll_timeout_seconds,
        poll_interval_seconds,
        extra_args,
        extra_kwargs,
    )
