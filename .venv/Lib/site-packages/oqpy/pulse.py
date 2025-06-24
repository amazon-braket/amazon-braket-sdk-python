############################################################################
#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
############################################################################
"""Classes representing OpenPulse variable types."""

from __future__ import annotations

from typing import Any, Sequence

from openpulse import ast

from oqpy.base import AstConvertible
from oqpy.classical_types import OQFunctionCall, _ClassicalVar

__all__ = ["PortVar", "WaveformVar", "FrameVar", "port", "waveform", "frame"]

port = ast.PortType()
waveform = ast.WaveformType()
frame = ast.FrameType()


class PortVar(_ClassicalVar):
    """A variable type corresponding to an OpenPulse port."""

    type_cls = ast.PortType

    def __init__(self, name: str | None = None, **kwargs: Any):
        super().__init__(name=name, **kwargs)


class WaveformVar(_ClassicalVar):
    """A variable type corresponding to an OpenPulse waveform."""

    type_cls = ast.WaveformType

    def __init__(
        self, init_expression: AstConvertible | None = None, name: str | None = None, **kwargs: Any
    ):
        super().__init__(
            init_expression=init_expression,
            name=name,
            **kwargs,
        )


class FrameVar(_ClassicalVar):
    """A variable type corresponding to an OpenPulse frame."""

    type_cls = ast.FrameType

    def __init__(
        self,
        port: PortVar | None = None,
        frequency: AstConvertible | None = None,
        phase: AstConvertible = 0,
        name: str | None = None,
        needs_declaration: bool = True,
        annotations: Sequence[str | tuple[str, str]] = (),
    ):
        if (port is None) != (frequency is None):
            raise ValueError("Must declare both port and frequency or neither.")
        if port is None:
            init_expression = None
        else:
            assert frequency is not None
            init_expression = OQFunctionCall(
                "newframe", {"port": port, "frequency": frequency, "phase": phase}, ast.FrameType
            )
        super().__init__(
            init_expression, name, needs_declaration=needs_declaration, annotations=annotations
        )
