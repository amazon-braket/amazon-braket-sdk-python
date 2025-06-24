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

import numpy as np

from braket.task_result.analog_hamiltonian_simulation_task_result_v1 import (
    AnalogHamiltonianSimulationShotMeasurement,
    AnalogHamiltonianSimulationShotMetadata,
    AnalogHamiltonianSimulationShotResult,
    AnalogHamiltonianSimulationTaskResult,
)
from braket.task_result.task_metadata_v1 import TaskMetadata


def convert_result(
    dist: np.ndarray,
    pre_sequence: list[int],
    configurations: list[str],
    task_Metadata: TaskMetadata,
) -> AnalogHamiltonianSimulationTaskResult:
    """Convert a given sampled distribution to the analog simulation result schema

    Args:
        dist (ndarray): The sample results to convert
        pre_sequence (list[int]): the same pre-sequence measurement results used for all shots
        configurations (list[str]): The list of configurations that comply with the blockade
            approximation.
        task_Metadata (TaskMetadata): The metadata for the task

    Returns:
        AnalogHamiltonianSimulationTaskResult: Results from sampling a distribution
    """
    measurements = []

    pre_sequence_arr = np.array(pre_sequence)
    non_empty_sites = np.where(pre_sequence_arr == 1)[0]

    for configuration, count in zip(configurations, dist):
        post_sequence = [0] * len(pre_sequence)
        for site, state in zip(non_empty_sites, list(configuration)):
            if state == "g":
                post_sequence[site] = 1
            else:  # state == "r":
                post_sequence[site] = 0

        shot_measurement = AnalogHamiltonianSimulationShotMeasurement(
            shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Success"),
            shotResult=AnalogHamiltonianSimulationShotResult(
                preSequence=pre_sequence, postSequence=post_sequence
            ),
        )
        measurements += [shot_measurement for _ in range(count)]

    return AnalogHamiltonianSimulationTaskResult(
        taskMetadata=task_Metadata, measurements=measurements
    )
