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

import random
import uuid
from unittest.mock import Mock, PropertyMock, patch

import pytest
from common_test_utils import MockS3

from braket.aws import AwsQuantumTaskBatch, AwsSession
from braket.circuits import Circuit
from braket.tasks import GateModelQuantumTaskResult

S3_TARGET = AwsSession.S3DestinationFolder("foo", "bar")


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_creation(mock_create):
    task_mock = Mock()
    type(task_mock).id = PropertyMock(side_effect=uuid.uuid4)
    task_mock.state.return_value = "RUNNING"
    mock_create.return_value = task_mock

    batch_size = 10
    batch = AwsQuantumTaskBatch(Mock(), "foo", _circuits(batch_size), S3_TARGET, 1000)
    assert batch.size == batch_size
    assert batch.tasks == [task_mock for _ in range(batch_size)]
    assert len(batch.unfinished) == batch_size
    assert not batch.unsuccessful


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_successful(mock_create):
    task_mock = Mock()
    type(task_mock).id = PropertyMock(side_effect=uuid.uuid4)
    task_mock.state.return_value = "COMPLETED"
    result = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_GATE_MODEL)
    task_mock.result.return_value = result
    mock_create.return_value = task_mock

    batch_size = 15
    batch = AwsQuantumTaskBatch(Mock(), "foo", _circuits(batch_size), S3_TARGET, 1000)
    assert batch.size == batch_size
    assert not batch.unfinished
    assert not batch.unsuccessful
    assert batch.results() == [result for _ in range(batch_size)]


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_unsuccessful(mock_create):
    task_mock = Mock()
    task_id = uuid.uuid4()
    type(task_mock).id = PropertyMock(return_value=task_id)
    task_mock.state.return_value = random.choice(["CANCELLED", "FAILED"])
    task_mock.result.return_value = None
    mock_create.return_value = task_mock

    batch = AwsQuantumTaskBatch(Mock(), "foo", [Circuit().h(0).cnot(0, 1)], S3_TARGET, 1000)
    assert not batch.unfinished
    assert batch.unsuccessful == {task_id}
    assert batch.results() == [None]
    assert batch.results(fail_unsuccessful=True) == [None]  # Result is cached
    batch._unsuccessful = set()
    with pytest.raises(RuntimeError):
        batch.results(fail_unsuccessful=True, retry=True)
    assert batch.unsuccessful == {task_id}


def _circuits(batch_size):
    return [Circuit().h(0).cnot(0, 1) for _ in range(batch_size)]
