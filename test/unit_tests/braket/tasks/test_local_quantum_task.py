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
import asyncio
import uuid

import numpy as np

from braket.circuits import Circuit
from braket.task_result import TaskMetadata
from braket.tasks import GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask

RESULT = GateModelQuantumTaskResult(
    task_metadata=TaskMetadata(**{"id": str(uuid.uuid4()), "deviceId": "default", "shots": 100}),
    additional_metadata=None,
    measurements=np.array([[0, 1], [1, 0]]),
    measured_qubits=[0, 1],
    result_types=None,
    values=None,
)


def test_id():
    # Task ID is valid UUID
    TASK = LocalQuantumTask(RESULT)
    TASK.result()
    uuid.UUID(TASK.id)


def test_state():
    TASK = LocalQuantumTask(RESULT)
    assert TASK.state() == "CREATED"


def test_result():
    TASK = LocalQuantumTask(RESULT)
    result = TASK.result()
    assert result == RESULT
    assert RESULT.task_metadata.id == TASK.id


def test_cancel():
    task = LocalQuantumTask().create(Circuit().h(0), "dummy_oq3", 100000)
    task.cancel()
    assert task.state() == "CANCELLED"


def test_async():
    TASK = LocalQuantumTask(RESULT)
    assert isinstance(TASK.async_result(), asyncio.Task)


def test_str():
    TASK = LocalQuantumTask(RESULT)
    expected = "LocalQuantumTask('id':{})".format(TASK.id)
    assert str(TASK) == expected
