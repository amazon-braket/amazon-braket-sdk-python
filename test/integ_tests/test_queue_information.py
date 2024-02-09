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
from braket.aws.queue_information import (
    HybridJobQueueInfo,
    QuantumTaskQueueInfo,
    QueueDepthInfo,
    QueueType,
)
from braket.circuits import Circuit
from braket.devices import Devices


def test_task_queue_position():
    device = AwsDevice(Devices.Amazon.SV1)

    bell = Circuit().h(0).cnot(0, 1)
    task = device.run(bell, shots=10)

    # call the queue_position method.
    queue_information = task.queue_position()

    # data type validations
    assert isinstance(queue_information, QuantumTaskQueueInfo)
    assert isinstance(queue_information.queue_type, QueueType)
    assert isinstance(queue_information.queue_position, (str, type(None)))

    # assert queue priority
    assert queue_information.queue_type in [QueueType.NORMAL, QueueType.PRIORITY]

    # assert message
    if queue_information.queue_position is None:
        assert queue_information.message is not None
        assert isinstance(queue_information.message, (str, type(None)))
    else:
        assert queue_information.message is None


def test_job_queue_position(aws_session, completed_quantum_job):
    job = completed_quantum_job

    # Check the job is complete
    job.result()

    # call the queue_position method.
    queue_information = job.queue_position()

    # data type validations
    assert isinstance(queue_information, HybridJobQueueInfo)

    # assert message
    assert queue_information.queue_position is None
    assert isinstance(queue_information.message, str)


def test_queue_depth():
    device = AwsDevice(Devices.Amazon.SV1)

    # call the queue_depth method.
    queue_information = device.queue_depth()

    # data type validations
    assert isinstance(queue_information, QueueDepthInfo)
    assert isinstance(queue_information.quantum_tasks, dict)
    assert isinstance(queue_information.jobs, str)

    for key, value in queue_information.quantum_tasks.items():
        assert isinstance(key, QueueType)
        assert isinstance(value, str)
