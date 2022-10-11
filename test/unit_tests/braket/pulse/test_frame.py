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

import pytest
from oqpy import FrameVar as OQpyFrame
from oqpy import PortVar
from oqpy.base import expr_matches

from braket.pulse import Frame, Port


@pytest.fixture
def port():
    return Port("test_port_ff", dt=1e-9)


@pytest.fixture
def frame_id():
    return "test_frame_rf"


def test_frame_no_properties(frame_id, port):
    frame = Frame(frame_id, port, 1e6, is_predefined=True)
    assert frame.id == frame_id
    assert frame.port == port
    assert frame.frequency == 1e6
    assert frame.phase == 0
    assert frame.is_predefined
    assert frame.properties is None


def test_frame_to_oqpy_expression(port, frame_id):
    frequency = 4e7
    phase = 1.57
    frame = Frame(frame_id, port, frequency, phase, True, {"dummy_property": "foo"})
    expected_expression = OQpyFrame(
        port=PortVar(port.id),
        frequency=frequency,
        phase=phase,
        name=frame_id,
        needs_declaration=False,
    )
    oq_expression = frame._to_oqpy_expression()
    assert expr_matches(oq_expression, expected_expression)


def test_frame_equality(frame_id, port):
    f = Frame(frame_id, port, 1e4, 0.57)
    uneqs = [
        Frame("wrong_id", port, f.frequency, f.phase, {"foo": "bar"}),
        Frame(f.id, Port("foo", dt=1e-9), f.frequency, f.phase),
        Frame(f.id, f.port, 1e5, f.phase),
        Frame(f.id, f.port, f.frequency, 0.23),
    ]
    eqs = [
        Frame(f.id, f.port, f.frequency, f.phase, {"a": "b"}),
        Frame(f.id, f.port, f.frequency, f.phase),
    ]
    for x in uneqs:
        assert f != x
    for x in eqs:
        assert f == x
