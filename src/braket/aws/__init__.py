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

"""A device represents a QPU or simulator that you can call to run quantum tasks.
A quantum task is the atomic request to a device, including the quantum circuit,
measurement instructions, and shot count. This module provides classes for
interacting with the Amazon Braket service, including AwsDevice for accessing
devices, AwsQuantumTask and AwsQuantumTaskBatch for task submission and parallel
execution, AwsQuantumJob for hybrid job management, AwsSession for managing AWS
connections, and DirectReservation for exclusive device access.
"""

from braket.aws.aws_device import AwsDevice, AwsDeviceType  # ruff:ignore[unused-import]
from braket.aws.aws_quantum_job import AwsQuantumJob  # ruff:ignore[unused-import]
from braket.aws.aws_quantum_task import AwsQuantumTask  # ruff:ignore[unused-import]
from braket.aws.aws_quantum_task_batch import AwsQuantumTaskBatch  # ruff:ignore[unused-import]
from braket.aws.aws_session import AwsSession  # ruff:ignore[unused-import]
from braket.aws.direct_reservations import DirectReservation  # ruff:ignore[unused-import]
