# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import json
from dataclasses import dataclass
from typing import Any, Dict

import numpy as np
from aqx.qdk.tasks.quantum_task_result import QuantumTaskResult


@dataclass
class AwsQuantumTaskResult(QuantumTaskResult):
    """
    Result of an AWS quantum task execution. This class is intended
    to be initialized by a QuantumTask class.

    Args:
        measurements (numpy.ndarray): 2d array - row is shot, column is qubit.
        task_metadata (Dict[str, Any]): Dictionary of task metadata. TODO: Link boto3 docs.
        state_vector (Dict[str, float]): Dictionary where key is state and value is probability.
    """

    task_metadata: Dict[str, Any]
    state_vector: Dict[str, float] = None

    @staticmethod
    def from_string(result: str) -> "AwsQuantumTaskResult":
        """
        Create AwsQuantumTaskResult from string with the S3 format defined by the AWS Qx Service.
        TODO: Link AWS Qx S3 format docs.

        Args:
            result (str): JSON object string, whose keys are AwsQuantumTaskResult attributes.

        Returns:
            AwsQuantumTaskResult: A AwsQuantumTaskResult based on a string loaded from S3.
        """
        json_obj = json.loads(result)
        state_vector = json_obj.get("StateVector", None)
        task_metadata = json_obj["TaskMetadata"]
        measurements = np.asarray(json_obj["Measurements"], dtype=int)
        return AwsQuantumTaskResult(
            state_vector=state_vector, task_metadata=task_metadata, measurements=measurements
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, AwsQuantumTaskResult):
            self_fields = (self.task_metadata, self.state_vector)
            other_fields = (other.task_metadata, other.state_vector)
            return self_fields == other_fields and super().__eq__(other)
        return NotImplemented
