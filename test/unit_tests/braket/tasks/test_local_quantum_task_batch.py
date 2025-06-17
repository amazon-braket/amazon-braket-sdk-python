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

import uuid

import numpy as np

from braket.task_result import TaskMetadata
from braket.tasks import GateModelQuantumTaskResult
from braket.tasks.local_quantum_task_batch import LocalQuantumTaskBatch

RESULTS = [
    GateModelQuantumTaskResult(
        task_metadata=TaskMetadata(**{
            "id": str(uuid.uuid4()),
            "deviceId": "default",
            "shots": 100,
        }),
        additional_metadata=None,
        measurements=np.array([[0, 1], [1, 0]]),
        measured_qubits=[0, 1],
        result_types=None,
        values=None,
    )
]

TASK_BATCH = LocalQuantumTaskBatch(RESULTS)


def test_results():
    assert TASK_BATCH.results() == RESULTS
    assert len(TASK_BATCH.results()) == 1
