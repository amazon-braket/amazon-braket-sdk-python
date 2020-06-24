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

import asyncio
import threading
import time
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from braket.annealing.problem import Problem, ProblemType
from braket.aws import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult
from common_test_utils import MockS3

S3_TARGET = AwsSession.S3DestinationFolder("foo", "bar")


@pytest.fixture
def aws_session():
    mock = Mock()
    _mock_metadata(mock, "RUNNING")
    return mock


@pytest.fixture
def quantum_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2)


@pytest.fixture
def circuit_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2)


@pytest.fixture
def annealing_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2)


@pytest.fixture
def arn():
    return "foo:bar:arn"


@pytest.fixture
def circuit():
    return Circuit().h(0).cnot(0, 1)


@pytest.fixture
def problem():
    return Problem(ProblemType.ISING, linear={1: 3.14}, quadratic={(1, 2): 10.08})


def test_equality(arn, aws_session):
    quantum_task_1 = AwsQuantumTask(arn, aws_session)
    quantum_task_2 = AwsQuantumTask(arn, aws_session)
    other_quantum_task = AwsQuantumTask("different:arn", aws_session)
    non_quantum_task = quantum_task_1.id

    assert quantum_task_1 == quantum_task_2
    assert quantum_task_1 is not quantum_task_2
    assert quantum_task_1 != other_quantum_task
    assert quantum_task_1 != non_quantum_task


def test_str(quantum_task):
    expected = "AwsQuantumTask('id':{})".format(quantum_task.id)
    assert str(quantum_task) == expected


def test_hash(quantum_task):
    assert hash(quantum_task) == hash(quantum_task.id)


def test_id_getter(arn, aws_session):
    quantum_task = AwsQuantumTask(arn, aws_session)
    assert quantum_task.id == arn


@pytest.mark.xfail(raises=AttributeError)
def test_no_id_setter(quantum_task):
    quantum_task.id = 123


def test_metadata(quantum_task):
    metadata_1 = {"status": "RUNNING"}
    quantum_task._aws_session.get_quantum_task.return_value = metadata_1
    assert quantum_task.metadata() == metadata_1
    quantum_task._aws_session.get_quantum_task.assert_called_with(quantum_task.id)

    metadata_2 = {"status": "COMPLETED"}
    quantum_task._aws_session.get_quantum_task.return_value = metadata_2
    assert quantum_task.metadata(use_cached_value=True) == metadata_1


def test_state(quantum_task):
    state_1 = "RUNNING"
    _mock_metadata(quantum_task._aws_session, state_1)
    assert quantum_task.state() == state_1
    quantum_task._aws_session.get_quantum_task.assert_called_with(quantum_task.id)

    state_2 = "COMPLETED"
    _mock_metadata(quantum_task._aws_session, state_2)
    assert quantum_task.state(use_cached_value=True) == state_1


def test_cancel(quantum_task):
    future = quantum_task.async_result()

    assert not future.done()
    quantum_task.cancel()

    assert quantum_task.result() is None
    assert future.cancelled()
    quantum_task._aws_session.cancel_quantum_task.assert_called_with(quantum_task.id)


def test_result_circuit(circuit_task):
    _mock_metadata(circuit_task._aws_session, "COMPLETED")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_1)

    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)
    assert circuit_task.result() == expected

    s3_bucket = circuit_task.metadata()["resultsS3Bucket"]
    s3_object_key = circuit_task.metadata()["resultsS3ObjectKey"]
    circuit_task._aws_session.retrieve_s3_object_body.assert_called_with(s3_bucket, s3_object_key)


@pytest.mark.xfail(raises=ValueError)
def test_result_unknown_ir_type(circuit_task):
    _mock_metadata(circuit_task._aws_session, "COMPLETED", "unsupported_ir_type")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_1)
    circuit_task.result()


def test_result_annealing(annealing_task):
    _mock_metadata(annealing_task._aws_session, "COMPLETED", "annealing")
    _mock_s3(annealing_task._aws_session, MockS3.MOCK_S3_RESULT_4)

    expected = AnnealingQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_4)
    assert annealing_task.result() == expected

    s3_bucket = annealing_task.metadata()["resultsS3Bucket"]
    s3_object_key = annealing_task.metadata()["resultsS3ObjectKey"]
    annealing_task._aws_session.retrieve_s3_object_body.assert_called_with(s3_bucket, s3_object_key)


def test_result_is_cached(circuit_task):
    _mock_metadata(circuit_task._aws_session, "COMPLETED")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_1)
    circuit_task.result()

    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_2)
    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)
    assert circuit_task.result() == expected


def test_async_result(circuit_task):
    def set_result_from_callback(future):
        # Set the result_from_callback variable in the enclosing functions scope
        nonlocal result_from_callback
        result_from_callback = future.result()

    _mock_metadata(circuit_task._aws_session, "RUNNING")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_1)

    future = circuit_task.async_result()

    # test the different ways to get the result from async

    # via callback
    result_from_callback = None
    future.add_done_callback(set_result_from_callback)

    # via asyncio waiting for result
    _mock_metadata(circuit_task._aws_session, "COMPLETED")
    event_loop = asyncio.get_event_loop()
    result_from_waiting = event_loop.run_until_complete(future)

    # via future.result(). Note that this would fail if the future is not complete.
    result_from_future = future.result()

    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)
    assert result_from_callback == expected
    assert result_from_waiting == expected
    assert result_from_future == expected


def test_async_result_with_partial_failures(circuit_task):
    def set_result_from_callback(future):
        # Set the result_from_callback variable in the enclosing functions scope
        nonlocal result_from_callback
        result_from_callback = future.result()

    _mock_metadata_partial_error(circuit_task._aws_session, "RUNNING", "COMPLETED")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_1)

    future = circuit_task.async_result()

    # test the different ways to get the result from async

    # via callback
    result_from_callback = None
    future.add_done_callback(set_result_from_callback)

    # via asyncio waiting for result
    event_loop = asyncio.get_event_loop()
    result_from_waiting = event_loop.run_until_complete(future)

    # via future.result(). Note that this would fail if the future is not complete.
    result_from_future = future.result()

    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)
    assert result_from_callback == expected
    assert result_from_waiting == expected
    assert result_from_future == expected


def test_failed_task(quantum_task):
    _mock_metadata(quantum_task._aws_session, "FAILED")
    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_1)
    result = quantum_task.result()
    assert result is None


def test_timeout_completed(aws_session):
    _mock_metadata(aws_session, "RUNNING")
    _mock_s3(aws_session, MockS3.MOCK_S3_RESULT_1)

    # Setup the poll timing such that the timeout will occur after one API poll
    quantum_task = AwsQuantumTask(
        "foo:bar:arn", aws_session, poll_timeout_seconds=0.5, poll_interval_seconds=1,
    )
    assert quantum_task.result() is None
    _mock_metadata(aws_session, "COMPLETED")
    assert quantum_task.state() == "COMPLETED"
    assert quantum_task.result() == GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)


def test_timeout_no_result_terminal_state(aws_session):
    _mock_metadata(aws_session, "RUNNING")
    _mock_s3(aws_session, MockS3.MOCK_S3_RESULT_1)

    # Setup the poll timing such that the timeout will occur after one API poll
    quantum_task = AwsQuantumTask(
        "foo:bar:arn", aws_session, poll_timeout_seconds=0.5, poll_interval_seconds=1,
    )
    assert quantum_task.result() is None

    _mock_metadata(aws_session, "FAILED")
    assert quantum_task.result() is None


@pytest.mark.xfail(raises=ValueError)
def test_create_invalid_s3_folder(aws_session, arn, circuit):
    AwsQuantumTask.create(aws_session, arn, circuit, ("bucket",), 1000)


@pytest.mark.xfail(raises=TypeError)
def test_create_invalid_task_specification(aws_session, arn):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    AwsQuantumTask.create(aws_session, arn, "foo", S3_TARGET, 1000)


def test_from_circuit_with_shots(aws_session, arn, circuit):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 53

    task = AwsQuantumTask.create(aws_session, arn, circuit, S3_TARGET, shots)
    assert task == AwsQuantumTask(
        mocked_task_arn, aws_session, GateModelQuantumTaskResult.from_string
    )

    _assert_create_quantum_task_called_with(
        aws_session,
        arn,
        circuit,
        AwsQuantumTask.GATE_IR_TYPE,
        S3_TARGET,
        shots,
        {"gateModelParameters": {"qubitCount": circuit.qubit_count}},
    )


@pytest.mark.xfail(raises=ValueError)
def test_from_circuit_with_shots_value_error(aws_session, arn, circuit):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    AwsQuantumTask.create(aws_session, arn, circuit, S3_TARGET, 0)


def test_from_annealing(aws_session, arn, problem):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn

    task = AwsQuantumTask.create(
        aws_session,
        arn,
        problem,
        S3_TARGET,
        1000,
        backend_parameters={"dWaveParameters": {"postprocessingType": "OPTIMIZATION"}},
    )
    assert task == AwsQuantumTask(
        mocked_task_arn, aws_session, AnnealingQuantumTaskResult.from_string
    )

    _assert_create_quantum_task_called_with(
        aws_session,
        arn,
        problem,
        AwsQuantumTask.ANNEALING_IR_TYPE,
        S3_TARGET,
        1000,
        {"annealingModelParameters": {"dWaveParameters": {"postprocessingType": "OPTIMIZATION"}}},
    )


def test_init_new_thread(aws_session, arn):
    tasks_list = []
    threading.Thread(target=_init_and_add_to_list, args=(aws_session, arn, tasks_list)).start()
    time.sleep(0.1)
    assert len(tasks_list) == 1


@patch("braket.aws.aws_quantum_task.boto3.Session")
def test_aws_session_for_task_arn(mock_session):
    region = "us-west-2"
    arn = f"arn:aws:aqx:{region}:account_id:quantum-task:task_id"
    mock_boto_session = Mock()
    mock_session.return_value = mock_boto_session
    mock_boto_session.region_name = region
    aws_session = AwsQuantumTask._aws_session_for_task_arn(arn)
    mock_session.assert_called_with(region_name=region)
    assert aws_session.boto_session == mock_boto_session


def _init_and_add_to_list(aws_session, arn, task_list):
    task_list.append(AwsQuantumTask(arn, aws_session, GateModelQuantumTaskResult.from_string))


def _assert_create_quantum_task_called_with(
    aws_session, arn, task_description, ir_type, s3_results_prefix, shots, backend_parameters
):
    aws_session.create_quantum_task.assert_called_with(
        **{
            "backendArn": arn,
            "resultsS3Bucket": s3_results_prefix[0],
            "resultsS3Prefix": s3_results_prefix[1],
            "ir": task_description.to_ir().json(),
            "irType": ir_type,
            "backendParameters": backend_parameters,
            "shots": shots,
        }
    )


def _mock_metadata(aws_session, state, irType="jaqcd"):
    return_value = {
        "status": state,
        "resultsS3Bucket": S3_TARGET.bucket,
        "resultsS3ObjectKey": S3_TARGET.key,
        "irType": irType,
    }
    aws_session.get_quantum_task.return_value = return_value


def _mock_metadata_partial_error(aws_session, *states, irType="jaqcd"):
    first_return_value = {
        "status": states[0],
        "resultsS3Bucket": S3_TARGET.bucket,
        "resultsS3ObjectKey": S3_TARGET.key,
        "irType": irType,
    }
    second_return_value = {
        "status": states[1],
        "resultsS3Bucket": S3_TARGET.bucket,
        "resultsS3ObjectKey": S3_TARGET.key,
        "irType": irType,
    }
    resource_not_found_response = {
        "Error": {"Code": "ResourceNotFoundException", "Message": "unit-test-error",}
    }
    throttling_response = {
        "Error": {"Code": "ResourceNotFoundException", "Message": "unit-test-error",}
    }
    aws_session.get_quantum_task.side_effect = [
        first_return_value,
        ClientError(resource_not_found_response, "unit-test"),
        ClientError(throttling_response, "unit-test"),
        second_return_value,
        second_return_value,
    ]


def _mock_s3(aws_session, result):
    aws_session.retrieve_s3_object_body.return_value = result
