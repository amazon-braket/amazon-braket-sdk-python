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

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class QueueType(str, Enum):
    """Enumerates the possible priorities for the queue.

    Values:
        NORMAL: Represents normal queue for the device.
        PRIORITY: Represents priority queue for the device.
    """

    NORMAL = "Normal"
    PRIORITY = "Priority"


@dataclass()
class QueueDepthInfo:
    """Represents quantum tasks and hybrid jobs queue depth information.

    Attributes:
        quantum_tasks (dict[QueueType, str]): number of quantum tasks waiting
            to run on a device. This includes both 'Normal' and 'Priority' tasks.
            For Example, {'quantum_tasks': {QueueType.NORMAL: '7', QueueType.PRIORITY: '3'}}
        jobs (str): number of hybrid jobs waiting to run on a device. Additionally, for QPUs if
            hybrid jobs queue depth is 0, we display information about priority and count of the
            running hybrid jobs. Example, 'jobs': '0 (1 prioritized job(s) running)'
    """

    quantum_tasks: dict[QueueType, str]
    jobs: str


@dataclass
class QuantumTaskQueueInfo:
    """Represents quantum tasks queue information.

    Attributes:
        queue_type (QueueType): type of the quantum_task queue either 'Normal'
            or 'Priority'.
        queue_position (Optional[str]): current position of your quantum task within a respective
            device queue. This value can be None based on the state of the task. Default: None.
        message (Optional[str]): Additional message information. This key is present only
            if 'queue_position' is None. Default: None.
    """

    queue_type: QueueType
    queue_position: Optional[str] = None
    message: Optional[str] = None


@dataclass
class HybridJobQueueInfo:
    """Represents hybrid job queue information.

    Attributes:
        queue_position (Optional[str]): current position of your hybrid job within a respective
            device queue. If the queue position of the hybrid job is greater than 15, we
            return '>15' as the queue_position return value. The queue_position is only
            returned when hybrid job is not in RUNNING/CANCELLING/TERMINAL states, else
            queue_position is returned as None.
        message (Optional[str]): Additional message information. This key is present only
            if 'queue_position' is None. Default: None.
    """

    queue_position: Optional[str] = None
    message: Optional[str] = None
