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
from enum import Enum
from typing import List

import numpy as np

from braket.task_result import AnalogHamiltonianSimulationTaskResult, TaskMetadata


class AnalogHamiltonianSimulationShotStatus(str, Enum):
    SUCCESS = "Success"
    PARTIAL_SUCCESS = "Partial Success"
    FAILURE = "Failure"


@dataclass
class ShotResult:
    status: AnalogHamiltonianSimulationShotStatus
    pre_sequence: np.ndarray = None
    post_sequence: np.ndarray = None

    def __eq__(self, other) -> bool:
        if isinstance(other, ShotResult):
            return (
                self.status == other.status
                and _equal_sequences(self.pre_sequence, other.pre_sequence)
                and _equal_sequences(self.post_sequence, other.post_sequence)
            )
        return NotImplemented


@dataclass
class AnalogHamiltonianSimulationQuantumTaskResult:
    task_metadata: TaskMetadata
    measurements: List[ShotResult] = None

    def __eq__(self, other) -> bool:
        if isinstance(other, AnalogHamiltonianSimulationQuantumTaskResult):
            return (
                self.task_metadata.id == other.task_metadata.id
                and self.measurements == other.measurements
            )
        return NotImplemented

    @staticmethod
    def from_object(
        result: AnalogHamiltonianSimulationTaskResult,
    ) -> AnalogHamiltonianSimulationQuantumTaskResult:
        return AnalogHamiltonianSimulationQuantumTaskResult._from_object_internal(result)

    @staticmethod
    def from_string(result: str) -> AnalogHamiltonianSimulationQuantumTaskResult:
        return AnalogHamiltonianSimulationQuantumTaskResult._from_object_internal(
            AnalogHamiltonianSimulationTaskResult.parse_raw(result)
        )

    @classmethod
    def _from_object_internal(
        cls, result: AnalogHamiltonianSimulationTaskResult
    ) -> AnalogHamiltonianSimulationQuantumTaskResult:
        if result.measurements is not None:
            measurements = AnalogHamiltonianSimulationQuantumTaskResult._get_measurements(result)
        else:
            measurements = None
        return cls(
            task_metadata=result.taskMetadata,
            measurements=measurements,
        )

    @classmethod
    def _get_measurements(cls, result: AnalogHamiltonianSimulationTaskResult) -> List[ShotResult]:
        measurements = []
        for measurement in result.measurements:
            status = AnalogHamiltonianSimulationShotStatus(measurement.shotMetadata.shotStatus)
            if measurement.shotResult.preSequence:
                pre_sequence = np.asarray(measurement.shotResult.preSequence, dtype=int)
            else:
                pre_sequence = None
            if measurement.shotResult.postSequence:
                post_sequence = np.asarray(measurement.shotResult.postSequence, dtype=int)
            else:
                post_sequence = None
            measurements.append(ShotResult(status, pre_sequence, post_sequence))
        return measurements


def _equal_sequences(sequence0, sequence1) -> bool:
    if sequence0 is None and sequence1 is None:
        return True
    if sequence0 is None or sequence1 is None:
        return False
    return np.allclose(sequence0, sequence1)
