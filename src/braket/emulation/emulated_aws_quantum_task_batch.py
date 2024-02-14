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

from typing import Union

from braket.tasks.local_quantum_task_batch import LocalQuantumTaskBatch
from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
    QuantumTaskBatch,
)


class EmulatedAwsQuantumTaskBatch(QuantumTaskBatch):
    def __init__(self, local_task: LocalQuantumTaskBatch):
        self._local_task = local_task

    def results(
        self,
    ) -> list[
        Union[
            GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult
        ]
    ]:
        return self._local_task.results()