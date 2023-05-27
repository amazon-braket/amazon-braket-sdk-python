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
from typing import List, Union

from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
    QuantumTaskBatch,
)


class LocalQuantumTaskBatch(QuantumTaskBatch):
    """Executes a batch of quantum tasks in parallel.

    Since this class is instantiated with the results, cancel() and run_async() are unsupported.
    """

    def __init__(
        self,
        results: List[
            Union[
                GateModelQuantumTaskResult,
                AnnealingQuantumTaskResult,
                PhotonicModelQuantumTaskResult,
            ]
        ],
    ):
        self._results = results

    def results(
        self,
    ) -> List[
        Union[
            GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult
        ]
    ]:
        return self._results

    def async_results(self) -> asyncio.Task:
        """Get the quantum task results asynchronously.
        Returns:
            Task: Get the quantum task results asynchronously.
        """
        # TODO: Allow for asynchronous simulation
        raise NotImplementedError("Asynchronous local simulation unsupported")
