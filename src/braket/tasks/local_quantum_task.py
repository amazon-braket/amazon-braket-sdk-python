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
from __future__ import annotations

import asyncio

from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
    QuantumTask,
)


class LocalQuantumTask(QuantumTask):
    """A quantum task containing the results of a local simulation.

    Since this class is instantiated with the results, cancel() and run_async() are unsupported.
    """

    def __init__(
        self,
        result: GateModelQuantumTaskResult
        | AnnealingQuantumTaskResult
        | PhotonicModelQuantumTaskResult,
    ):
        self._id = result.task_metadata.id
        self._result = result

    @property
    def id(self) -> str:
        """Gets the task ID.

        Returns:
            str: The ID of the task.
        """
        return str(self._id)

    def cancel(self) -> None:
        """Cancel the quantum task."""
        raise NotImplementedError("Cannot cancel completed local task")

    def state(self) -> str:
        """Gets the state of the task.

        Returns:
            str: Returns COMPLETED
        """
        return "COMPLETED"

    def result(
        self,
    ) -> GateModelQuantumTaskResult | AnnealingQuantumTaskResult | PhotonicModelQuantumTaskResult:
        return self._result

    def async_result(self) -> asyncio.Task:
        """Get the quantum task result asynchronously.

        Raises:
            NotImplementedError: Asynchronous local simulation unsupported

        Returns:
            asyncio.Task: Get the quantum task result asynchronously.
        """
        # TODO: Allow for asynchronous simulation
        raise NotImplementedError("Asynchronous local simulation unsupported")

    def __repr__(self) -> str:
        return f"LocalQuantumTask('id':{self.id})"
