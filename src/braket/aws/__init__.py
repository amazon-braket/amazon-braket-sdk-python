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
interacting with Amazon Braket cloud services, including AwsDevice for accessing
devices, AwsQuantumTask and AwsQuantumTaskBatch for task submission and parallel
execution, AwsQuantumJob for hybrid job management, AwsSession for managing AWS
connections, and DirectReservation for exclusive device access.
"""

from braket.aws.aws_device import AwsDevice, AwsDeviceType  # noqa: F401
from braket.aws.aws_quantum_job import AwsQuantumJob  # noqa: F401
from braket.aws.aws_quantum_task import AwsQuantumTask  # noqa: F401
from braket.aws.aws_quantum_task_batch import AwsQuantumTaskBatch  # noqa: F401
from braket.aws.aws_session import AwsSession  # noqa: F401
from braket.aws.direct_reservations import DirectReservation  # noqa: F401
