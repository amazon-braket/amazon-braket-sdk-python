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

import uuid

import pytest
from braket.tasks import GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask

RESULT = GateModelQuantumTaskResult.from_dict(
    {
        "StateVector": {
            "00": complex(0.2, 0.2),
            "01": complex(0.3, 0.1),
            "10": complex(0.1, 0.3),
            "11": complex(0.2, 0.2),
        },
        "Measurements": [[0, 0], [0, 1], [0, 1], [0, 1]],
        "TaskMetadata": {"Id": "UUID_blah_1", "Status": "COMPLETED"},
    }
)

TASK = LocalQuantumTask(RESULT)


def test_id():
    # Task ID is valid UUID
    uuid.UUID(TASK.id)


def test_state():
    assert TASK.state() == "COMPLETED"


def test_result():
    assert TASK.result == RESULT


@pytest.mark.xfail(raises=NotImplementedError)
def test_cancel():
    TASK.cancel()


@pytest.mark.xfail(raises=NotImplementedError)
def test_async():
    TASK.async_result()
