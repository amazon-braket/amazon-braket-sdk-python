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
# language governing permissions and limitations under the License

from enum import Enum
from typing import Any, Optional

from pydantic.v1 import BaseModel


class Direction(Enum):
    """
    Specifies the direction of port.
    """

    tx = "tx"
    rx = "rx"


class Port(BaseModel):
    """
    Represents a hardware port that may be used for pulse control. For more details on ports
    refer to the OpenQasm/OpenPulse documentation

    Attributes:
        portId: The id of the associated hardware port the frame uses
        direction: The directionality of the port
        portType: The port type of the control hardware
        dt: The smallest time step that may be used on the control hardware

    """

    portId: str
    direction: Direction
    portType: str
    dt: float
    qubitMappings: Optional[list[int]]
    centerFrequencies: Optional[set[float]]
    qhpSpecificProperties: Optional[dict[str, Any]]
