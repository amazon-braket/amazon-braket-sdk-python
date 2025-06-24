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

from typing import Any, Optional

from pydantic.v1 import BaseModel


class Frame(BaseModel):
    """
    Defines the pre-built frames for the given hardware.  For more details on frames
    refer to the OpenQasm/OpenPulse documentation

    Attributes:
        frameId: The id name of the frame that may be loaded in OpenQasm
        portId: The id of the associated hardware port the frame uses
        frequency: The initial frequency of the frame
        phase: The initial phase of the frame
        associatedGate: Optional detail if the frame is associated with a gate
        qubitMappings:  Optional list of associated qubits for the frame

    """

    frameId: str
    portId: str
    frequency: float
    centerFrequency: Optional[float]
    phase: float
    associatedGate: Optional[str]
    qubitMappings: Optional[list[int]]
    qhpSpecificProperties: Optional[dict[str, Any]]
