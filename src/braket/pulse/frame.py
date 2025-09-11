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

from __future__ import annotations

import math
from typing import Any

from oqpy import FrameVar as OQFrame
from oqpy.base import OQPyExpression

from braket.pulse.port import Port


class Frame:
    """Frame tracks the frame of reference, when interacting with the qubits, throughout the
    execution of a program. See https://openqasm.com/language/openpulse.html#frames for more
    details.
    """

    def __init__(
        self,
        frame_id: str,
        port: Port,
        frequency: float,
        phase: float = 0,
        is_predefined: bool = False,
        properties: dict[str, Any] | None = None,
    ):
        """Initializes a Frame.

        Args:
            frame_id (str): str identifying a unique frame.
            port (Port): port that this frame is attached to.
            frequency (float): frequency to which this frame should be initialized.
            phase (float): phase to which this frame should be initialized. Defaults to 0.
            is_predefined (bool): bool indicating whether this is a predefined frame on
                the device. Defaults to False.
            properties (Optional[dict[str, Any]]): Dict containing properties of this frame.
                Defaults to None.
        """
        self._frame_id = frame_id
        self.port = port
        self.frequency = frequency
        self.phase = phase
        self.is_predefined = is_predefined
        self.properties = properties

    @property
    def id(self) -> str:
        """Returns a str indicating the frame id."""
        return self._frame_id

    def __eq__(self, other: Frame) -> bool:
        return (
            (
                (self.id == other.id)
                and (self.port == other.port)
                and math.isclose(self.frequency, other.frequency)
                and math.isclose(self.phase, other.phase)
            )
            if isinstance(other, Frame)
            else False
        )

    def _to_oqpy_expression(self) -> OQPyExpression:
        return OQFrame(
            port=self.port._to_oqpy_expression(),
            frequency=self.frequency,
            phase=self.phase,
            name=self.id,
            needs_declaration=not self.is_predefined,
        )
