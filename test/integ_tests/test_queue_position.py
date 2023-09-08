# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.devices import Devices
from braket.queue_information import QueuePosition, QueuePriority


def test_task_queue_position():
    device = AwsDevice(Devices.Amazon.SV1)

    bell = Circuit().h(0).cnot(0, 1)
    task = device.run(bell, shots=10)

    # call the queue_position method.
    queue_information = task.queue_position()

    # data type validations
    assert isinstance(queue_information, QueuePosition)
    assert isinstance(queue_information.queue_priority, QueuePriority)
    assert isinstance(queue_information.queue_position, str)

    # assert queue priority
    assert queue_information.queue_priority in [QueuePriority.NORMAL, QueuePriority.PRIORITY]

    # assert message
    if queue_information.queue_position == "None":
        assert queue_information.message is not None
        assert isinstance(queue_information.message, str)
    else:
        assert queue_information.message is None
