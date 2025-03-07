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

from collections import Counter
from dataclasses import dataclass
from enum import Enum

import numpy as np

from braket.task_result import (
    AdditionalMetadata,
    AnalogHamiltonianSimulationTaskResult,
    TaskMetadata,
)


class AnalogHamiltonianSimulationShotStatus(str, Enum):
    SUCCESS = "Success"
    PARTIAL_SUCCESS = "Partial Success"
    FAILURE = "Failure"


@dataclass
class ShotResult:
    status: AnalogHamiltonianSimulationShotStatus
    pre_sequence: np.ndarray = None
    post_sequence: np.ndarray = None

    def __eq__(self, other: ShotResult) -> bool:
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
    additional_metadata: AdditionalMetadata
    measurements: list[ShotResult] = None

    def __eq__(self, other: AnalogHamiltonianSimulationQuantumTaskResult) -> bool:
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
            additional_metadata=result.additionalMetadata,
            measurements=measurements,
        )

    @classmethod
    def _get_measurements(cls, result: AnalogHamiltonianSimulationTaskResult) -> list[ShotResult]:
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

    def get_counts(self) -> dict[str, int]:
        """Aggregate state counts from AHS shot results.

        Notes:
            We use the following convention to denote the state of an atom (site).
            e: empty site
            r: Rydberg state atom
            g: ground state atom

        Returns:
            dict[str, int]: number of times each state configuration is measured.
            Returns None if none of shot measurements are successful.
            Only successful shots contribute to the state count.
        """
        state_counts = Counter()
        states = ["e", "r", "g"]
        for shot in self.measurements:
            if shot.status == AnalogHamiltonianSimulationShotStatus.SUCCESS:
                pre = shot.pre_sequence
                post = shot.post_sequence
                # converting presequence and postsequence measurements to state_idx
                state_idx = [
                    0 if pre_i == 0 else 1 if post_i == 0 else 2 for pre_i, post_i in zip(pre, post)
                ]
                state = "".join(states[s_idx] for s_idx in state_idx)
                state_counts.update([state])

        return dict(state_counts)

    def get_avg_density(self) -> np.ndarray:
        """Get the average Rydberg state densities from the result

        Returns:
            np.ndarray: The average densities from the result
        """
        counts = self.get_counts()

        N_ryd, N_ground = [], []
        for shot, count in counts.items():
            N_ryd.append([count if s == "r" else 0 for s in shot])
            N_ground.append([count if s == "g" else 0 for s in shot])

        N_ryd_cnt = np.sum(N_ryd, axis=0)
        N_ground_cnt = np.sum(N_ground, axis=0)

        return N_ryd_cnt / (N_ryd_cnt + N_ground_cnt)


def _equal_sequences(sequence0: np.ndarray, sequence1: np.ndarray) -> bool:
    if sequence0 is None and sequence1 is None:
        return True
    if sequence0 is None or sequence1 is None:
        return False
    return np.allclose(sequence0, sequence1)
