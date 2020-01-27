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
from unittest.mock import Mock

import pytest
from braket.aws import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit
from braket.tasks import GateModelQuantumTaskResult
from common_test_utils import MockS3

S3_TARGET = AwsSession.S3DestinationFolder("foo", "bar")


@pytest.fixture
def aws_session():
    mock = Mock()
    _mock_state(mock, "RUNNING")
    return mock


@pytest.fixture
def quantum_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2)


@pytest.fixture
def arn():
    return "foo:bar:arn"


@pytest.fixture
def circuit():
    return Circuit().h(0).cnot(0, 1)


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
    hash(quantum_task) == hash(quantum_task.id)


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
    _mock_state(quantum_task._aws_session, state_1)
    assert quantum_task.state() == state_1
    quantum_task._aws_session.get_quantum_task.assert_called_with(quantum_task.id)

    state_2 = "COMPLETED"
    _mock_state(quantum_task._aws_session, state_2)
    assert quantum_task.state(use_cached_value=True) == state_1


def test_cancel(quantum_task):
    future = quantum_task.async_result()

    assert not future.done()
    quantum_task.cancel()

    assert quantum_task.result() is None
    assert future.cancelled()
    quantum_task._aws_session.cancel_quantum_task.assert_called_with(quantum_task.id)


def test_result(quantum_task):
    _mock_state(quantum_task._aws_session, "COMPLETED")
    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_1)

    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)
    assert quantum_task.result() == expected

    s3_bucket = quantum_task.metadata()["resultsS3Bucket"]
    s3_object_key = quantum_task.metadata()["resultsS3ObjectKey"]
    quantum_task._aws_session.retrieve_s3_object_body.assert_called_with(s3_bucket, s3_object_key)


def test_result_is_cached(quantum_task):
    _mock_state(quantum_task._aws_session, "COMPLETED")
    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_1)
    quantum_task.result()

    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_2)
    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)
    assert quantum_task.result() == expected


def test_async_result(quantum_task):
    def set_result_from_callback(future):
        # Set the result_from_callback variable in the enclosing functions scope
        nonlocal result_from_callback
        result_from_callback = future.result()

    _mock_state(quantum_task._aws_session, "RUNNING")
    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_1)

    future = quantum_task.async_result()

    # test the different ways to get the result from async

    # via callback
    result_from_callback = None
    future.add_done_callback(set_result_from_callback)

    # via asyncio waiting for result
    _mock_state(quantum_task._aws_session, "COMPLETED")
    event_loop = asyncio.get_event_loop()
    result_from_waiting = event_loop.run_until_complete(future)

    # via future.result(). Note that this would fail if the future is not complete.
    result_from_future = future.result()

    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)
    assert result_from_callback == expected
    assert result_from_waiting == expected
    assert result_from_future == expected


def test_failed_task(quantum_task):
    _mock_state(quantum_task._aws_session, "FAILED")
    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_1)
    result = quantum_task.result()
    assert result is None


def test_timeout(aws_session):
    _mock_state(aws_session, "RUNNING")
    _mock_s3(aws_session, MockS3.MOCK_S3_RESULT_1)

    # Setup the poll timing such that the timeout will occur after one API poll
    quantum_task = AwsQuantumTask(
        "foo:bar:arn", aws_session, poll_timeout_seconds=0.5, poll_interval_seconds=1
    )
    assert quantum_task.result() is None

    _mock_state(aws_session, "COMPLETED")
    assert quantum_task.result() == GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_1)


@pytest.mark.xfail(raises=ValueError)
def test_from_circuit_invalid_s3_folder(aws_session, arn, circuit):
    AwsQuantumTask.from_circuit(aws_session, arn, circuit, ("bucket",))


def test_from_circuit_default_shots(aws_session, arn, circuit):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn

    task = AwsQuantumTask.from_circuit(aws_session, arn, circuit, S3_TARGET)
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)

    _assert_create_quantum_task_called_with(
        aws_session, arn, circuit, S3_TARGET, AwsQuantumTask.DEFAULT_SHOTS
    )


def test_from_circuit_with_shots(aws_session, arn, circuit):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 53

    task = AwsQuantumTask.from_circuit(aws_session, arn, circuit, S3_TARGET)
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)

    _assert_create_quantum_task_called_with(aws_session, arn, circuit, S3_TARGET, shots)


def _assert_create_quantum_task_called_with(aws_session, arn, circuit, s3_results_prefix, shots):
    aws_session.create_quantum_task.assert_called_with(
        **{
            "backendArn": arn,
            "resultsS3Bucket": s3_results_prefix[0],
            "resultsS3Prefix": s3_results_prefix[1],
            "ir": circuit.to_ir().json(),
            "irType": AwsQuantumTask.GATE_IR_TYPE,
            "backendParameters": {"gateModelParameters": {"qubitCount": circuit.qubit_count}},
            "shots": AwsQuantumTask.DEFAULT_SHOTS,
        }
    )


def _mock_state(aws_session, state):
    return_value = {
        "status": state,
        "resultsS3Bucket": S3_TARGET.bucket,
        "resultsS3ObjectKey": S3_TARGET.key,
    }
    aws_session.get_quantum_task.return_value = return_value


def _mock_s3(aws_session, result):
    aws_session.retrieve_s3_object_body.return_value = result
