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

from braket.pulse import (
    ArbitraryWaveform,
    ConstantWaveform,
    DragGaussianWaveform,
    Frame,
    GaussianWaveform,
    Port,
    PulseSequence,
)


@pytest.fixture
def port():
    return Port(port_id="device_port_x0", properties={})


@pytest.fixture
def predefined_frame_1(port):
    return Frame(
        frame_id="predefined_frame_1", frequency=2e9, port=port, phase=0, is_predefined=True
    )


@pytest.fixture
def predefined_frame_2(port):
    return Frame(frame_id="predefined_frame_2", frequency=1e6, port=port, is_predefined=True)


@pytest.fixture
def user_defined_frame(port):
    return Frame(
        frame_id="user_defined_frame_0",
        port=port,
        frequency=1e7,
        phase=3.14,
        is_predefined=False,
        properties={"associatedGate": "rz"},
    )


def test_pulse_sequence_with_user_defined_frame(user_defined_frame):
    pulse_sequence = PulseSequence().set_frequency(user_defined_frame, 6e6)
    expected_str = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    port device_port_x0;",
            "    frame user_defined_frame_0 = newframe(device_port_x0, 10000000.0, 3.14);",
            "    set_frequency(user_defined_frame_0, 6000000.0);",
            "}",
        ]
    )
    assert pulse_sequence.to_ir() == expected_str


def test_pulse_sequence_to_ir(predefined_frame_1, predefined_frame_2):
    pulse_sequence = (
        PulseSequence()
        .set_frequency(predefined_frame_1, 3e9)
        .shift_frequency(predefined_frame_1, 1e9)
        .set_phase(predefined_frame_1, -0.5)
        .shift_phase(predefined_frame_1, 0.1)
        .set_scale(predefined_frame_1, 0.25)
        .capture_v0(predefined_frame_1)
        .delay([predefined_frame_1, predefined_frame_2], 2e-9)
        .delay(predefined_frame_1, 1e-6)
        .barrier([predefined_frame_1, predefined_frame_2])
        .play(predefined_frame_1, GaussianWaveform(length=1e-3, sigma=0.7, name="gauss_wf"))
        .play(
            predefined_frame_2,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, name="drag_gauss_wf"),
        )
        .play(
            predefined_frame_1,
            ConstantWaveform(length=4e-3, iq=complex(2, 0.3), name="constant_wf"),
        )
        .play(
            predefined_frame_2,
            ArbitraryWaveform([complex(1, 0.4), 0, 0.3, complex(0.1, 0.2)], name="arb_wf"),
        )
        .capture_v0(predefined_frame_2)
    )
    expected_str = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    waveform gauss_wf = gaussian(1000000.0ns, 0.7, 1, true);",
            "    waveform drag_gauss_wf = drag_gaussian(3000000.0ns, 0.4, 0.2, 1, true);",
            "    waveform constant_wf = constant(4000000.0ns, 2.0 + 0.3im);",
            "    waveform arb_wf = {1.0 + 0.4im, 0, 0.3, 0.1 + 0.2im};",
            "    bit[2] b;",
            "    set_frequency(predefined_frame_1, 3000000000.0);",
            "    shift_frequency(predefined_frame_1, 1000000000.0);",
            "    set_phase(predefined_frame_1, -0.5);",
            "    shift_phase(predefined_frame_1, 0.1);",
            "    set_scale(predefined_frame_1, 0.25);",
            "    b[0] = capture_v0(predefined_frame_1);",
            "    delay[2.0ns] predefined_frame_1, predefined_frame_2;",
            "    delay[1000.0ns] predefined_frame_1;",
            "    barrier predefined_frame_1, predefined_frame_2;",
            "    play(predefined_frame_1, gauss_wf);",
            "    play(predefined_frame_2, drag_gauss_wf);",
            "    play(predefined_frame_1, constant_wf);",
            "    play(predefined_frame_2, arb_wf);",
            "    b[1] = capture_v0(predefined_frame_2);",
            "}",
        ]
    )
    assert pulse_sequence.to_ir() == expected_str
