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


class QueuePriority(str, Enum):
    """
    Enumerates the possible priorities for the queue.

    Values:
        NORMAL: Represents normal queue for the device.
        PRIORITY: Represents priority queue for the device.
    """

    NORMAL = "Normal"
    PRIORITY = "Priority"


@dataclass
class QueuePosition:
    """
    Represents information related to data fetched from metadata.

    Attributes:
        queue_position (str): current position of your quantum task within a respective
        device queue. This value can be "None" based on the state of the task.
        queue_priority (QueuePriority): priority of the quantum_task in the queue,
        either 'Normal' or 'Priority'.
        message (Optional[str]): Additional message information. This key is present only
        if 'queue_position' is "None". Default: None.
    """

    queue_position: Optional[str]
    queue_priority: QueuePriority
    message: Optional[str] = None
