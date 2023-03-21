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

import logging
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

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

    @staticmethod
    def get_counts(result: AnalogHamiltonianSimulationQuantumTaskResult) -> Dict[str, int]:
        """Aggregate state counts from AHS shot results
        Args:
            result (AnalogHamiltonianSimulationQuantumTaskResult): The result
                from which the aggregated state counts are obtained
        Returns:
            Dict[str, int]: number of times each state configuration is measured.
            Returns None if the shot measurements are not successfull.
        Notes: We use the following convention to denote the state of an atom (site):
            e: empty site
            r: Rydberg state atom
            g: ground state atom
        """

        state_counts = Counter()
        states = ["e", "r", "g"]
        for shot in result.measurements:
            if shot.status != AnalogHamiltonianSimulationShotStatus.SUCCESS:
                state = None
                raise logging.warning(f"Shot status: {shot.status}. Skipping.")
            else:
                pre = shot.pre_sequence
                post = shot.post_sequence
                # converting presequence and postsequence measurements to state_idx
                state_idx = [
                    0 if pre_i == 0 else 1 if post_i == 0 else 2 for pre_i, post_i in zip(pre, post)
                ]
                state = "".join(map(lambda s_idx: states[s_idx], state_idx))
            state_counts.update((state,))

        return dict(state_counts)

    @staticmethod
    def get_avg_density(result: AnalogHamiltonianSimulationQuantumTaskResult) -> np.ndarray:
        """Get the average Rydberg state densities from the result
        Args:
            result (AnalogHamiltonianSimulationQuantumTaskResult): The result
                from which the aggregated state counts are obtained
        Returns:
            ndarray (float): The average densities from the result
        Notes:
            Shot result '0' corresponds to the Rydberg state (r) and contributes to the density.
            Shot result '1' corresponds to the ground state and does not contribute to the density.
        """

        postSeqs = []
        for shot in result.measurements:
            if shot.status != AnalogHamiltonianSimulationShotStatus.SUCCESS:
                raise logging.warning(f"Shot status: {shot.status}. Skipping.")
            else:
                postSeqs.append(shot.post_sequence)

        avg_density = np.sum(1 - np.array(postSeqs), axis=0) / len(postSeqs)
        return avg_density


def _equal_sequences(sequence0: np.ndarray, sequence1: np.ndarray) -> bool:
    if sequence0 is None and sequence1 is None:
        return True
    if sequence0 is None or sequence1 is None:
        return False
    return np.allclose(sequence0, sequence1)
