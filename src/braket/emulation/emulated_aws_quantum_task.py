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

from braket.tasks.local_quantum_task import LocalQuantumTask
from typing import Any, Union

from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
    QuantumTask,
)
from braket.aws.queue_information import QuantumTaskQueueInfo, QueueType


class EmulatedAwsQuantumTask(QuantumTask):
    def __init__(self, local_task: LocalQuantumTask):
        self._local_task = local_task

    @property
    def id(self) -> str:
        return f"emulation:quantum-task/{str(self._local_task.id)}"

    def cancel(self) -> None:
        """Cancel the quantum task."""
        raise NotImplementedError("Cannot cancel completed local task")

    def state(self) -> str:
        return "COMPLETED"

    def result(
        self,
    ) -> Union[
        GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult
    ]:
        return self._local_task.result()

    def async_result(self) -> asyncio.Task:
        try:
            loop = asyncio.get_event_loop()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._create_future())

    def __repr__(self) -> str:
        return f"EmulatedAwsQuantumTask('id':{self.id})"

    def queue_position(self) -> QuantumTaskQueueInfo:
        return QuantumTaskQueueInfo(QueueType.NORMAL)

    def metadata(self, use_cached_value: bool = False) -> dict[str, Any]:
        return {}

    async def _create_future(self) -> asyncio.Task:
        return asyncio.create_task(self._wait_for_completion())

    async def _wait_for_completion(
        self,
    ) -> Union[
        GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult
    ]:
        return self.result()
