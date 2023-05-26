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
from abc import ABC, abstractmethod
from typing import Any, Dict, Union, List

from braket.tasks.annealing_quantum_task_result import AnnealingQuantumTaskResult
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult
from braket.tasks.photonic_model_quantum_task_result import PhotonicModelQuantumTaskResult


class QuantumTaskBatch(ABC):
    """An abstraction over a quantum task batch on a quantum device."""

    @abstractmethod
    def results(
        self,
    ) -> List[Union[
        GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult
    ]]:
        """Get the quantum task results.
        Returns:
            List[Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult]]:: # noqa
            Get the quantum task results. Call async_result if you want the result in an
            asynchronous way.
        """

    @abstractmethod
    def async_results(self) -> asyncio.Task:
        """Get the quantum task result asynchronously.
        Returns:
            Task: Get the quantum task result asynchronously.
        """
