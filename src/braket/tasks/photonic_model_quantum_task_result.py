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

from dataclasses import dataclass

import numpy as np

from braket.task_result import AdditionalMetadata, PhotonicModelTaskResult, TaskMetadata


@dataclass
class PhotonicModelQuantumTaskResult:
    task_metadata: TaskMetadata
    additional_metadata: AdditionalMetadata
    measurements: np.ndarray = None

    def __eq__(self, other: PhotonicModelQuantumTaskResult) -> bool:
        if isinstance(other, PhotonicModelQuantumTaskResult):
            return self.task_metadata.id == other.task_metadata.id
        return NotImplemented

    @staticmethod
    def from_object(result: PhotonicModelTaskResult) -> PhotonicModelQuantumTaskResult:
        """Create PhotonicModelQuantumTaskResult from PhotonicModelTaskResult object.

        Args:
            result (PhotonicModelTaskResult): PhotonicModelTaskResult object

        Returns:
            PhotonicModelQuantumTaskResult: A PhotonicModelQuantumTaskResult based on the given dict

        Raises:
            ValueError: If "measurements" is not a key in the result dict
        """
        return PhotonicModelQuantumTaskResult._from_object_internal(result)

    @staticmethod
    def from_string(result: str) -> PhotonicModelQuantumTaskResult:
        return PhotonicModelQuantumTaskResult._from_object_internal(
            PhotonicModelTaskResult.parse_raw(result)
        )

    @classmethod
    def _from_object_internal(
        cls, result: PhotonicModelTaskResult
    ) -> PhotonicModelQuantumTaskResult:
        task_metadata = result.taskMetadata
        additional_metadata = result.additionalMetadata
        if result.measurements is not None:
            measurements = np.asarray(result.measurements, dtype=int)
        else:
            measurements = None
        return cls(
            task_metadata=task_metadata,
            additional_metadata=additional_metadata,
            measurements=measurements,
        )
