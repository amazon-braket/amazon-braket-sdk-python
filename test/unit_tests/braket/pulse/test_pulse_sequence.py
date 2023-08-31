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

from braket.circuits import FreeParameter, QubitSet
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
    return Port(port_id="device_port_x0", dt=1e-3, properties={})


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


@pytest.fixture
def conflicting_user_defined_frame():
    return Frame(
        frame_id="user_defined_frame_0",
        port=Port("wrong_port", dt=1e-9),
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
            "    frame user_defined_frame_0 = newframe(device_port_x0, 10000000.0, 3.14);",
            "    set_frequency(user_defined_frame_0, 6000000.0);",
            "}",
        ]
    )
    assert pulse_sequence.to_ir() == expected_str


def test_pulse_sequence_make_bound_pulse_sequence(predefined_frame_1, predefined_frame_2):
    param = FreeParameter("a") + 2 * FreeParameter("b")
    pulse_sequence = (
        PulseSequence()
        .set_frequency(predefined_frame_1, param)
        .shift_frequency(predefined_frame_1, param)
        .set_phase(predefined_frame_1, param)
        .shift_phase(predefined_frame_1, param)
        .set_scale(predefined_frame_1, param)
        .capture_v0(predefined_frame_1)
        .delay([predefined_frame_1, predefined_frame_2], param)
        .delay(predefined_frame_1, param)
        .delay(predefined_frame_1, 1e-3)
        .barrier([predefined_frame_1, predefined_frame_2])
        .play(
            predefined_frame_1,
            GaussianWaveform(
                length=FreeParameter("length_g"), sigma=FreeParameter("sigma_g"), id="gauss_wf"
            ),
        )
        .play(
            predefined_frame_2,
            DragGaussianWaveform(
                length=FreeParameter("length_dg"),
                sigma=FreeParameter("sigma_dg"),
                beta=0.2,
                id="drag_gauss_wf",
            ),
        )
        .play(
            predefined_frame_1,
            ConstantWaveform(
                length=FreeParameter("length_c"), iq=complex(2, 0.3), id="constant_wf"
            ),
        )
        .play(
            predefined_frame_2,
            ArbitraryWaveform([complex(1, 0.4), 0, 0.3, complex(0.1, 0.2)], id="arb_wf"),
        )
        .capture_v0(predefined_frame_2)
    )
    expected_str_unbound = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    waveform gauss_wf = gaussian((1000000000.0*length_g)ns, (1000000000.0*sigma_g)ns, "
            "1, false);",
            "    waveform drag_gauss_wf = "
            "drag_gaussian((1000000000.0*length_dg)ns, (1000000000.0*sigma_dg)ns, 0.2, 1, false);",
            "    waveform constant_wf = constant((1000000000.0*length_c)ns, 2.0 + 0.3im);",
            "    waveform arb_wf = {1.0 + 0.4im, 0, 0.3, 0.1 + 0.2im};",
            "    bit[2] psb;",
            "    set_frequency(predefined_frame_1, a + 2*b);",
            "    shift_frequency(predefined_frame_1, a + 2*b);",
            "    set_phase(predefined_frame_1, a + 2*b);",
            "    shift_phase(predefined_frame_1, a + 2*b);",
            "    set_scale(predefined_frame_1, a + 2*b);",
            "    psb[0] = capture_v0(predefined_frame_1);",
            (
                "    delay[(1000000000.0*a + 2000000000.0*b)ns]"
                " predefined_frame_1, predefined_frame_2;"
            ),
            "    delay[(1000000000.0*a + 2000000000.0*b)ns] predefined_frame_1;",
            "    delay[1000000.0ns] predefined_frame_1;",
            "    barrier predefined_frame_1, predefined_frame_2;",
            "    play(predefined_frame_1, gauss_wf);",
            "    play(predefined_frame_2, drag_gauss_wf);",
            "    play(predefined_frame_1, constant_wf);",
            "    play(predefined_frame_2, arb_wf);",
            "    psb[1] = capture_v0(predefined_frame_2);",
            "}",
        ]
    )
    assert pulse_sequence.to_ir() == expected_str_unbound
    assert pulse_sequence.parameters == set(
        [
            FreeParameter("a"),
            FreeParameter("b"),
            FreeParameter("length_g"),
            FreeParameter("length_dg"),
            FreeParameter("sigma_g"),
            FreeParameter("sigma_dg"),
            FreeParameter("length_c"),
        ]
    )
    b_bound = pulse_sequence.make_bound_pulse_sequence(
        {"b": 2, "length_g": 1e-3, "length_dg": 3e-3, "sigma_dg": 0.4, "length_c": 4e-3}
    )
    b_bound_call = pulse_sequence(b=2, length_g=1e-3, length_dg=3e-3, sigma_dg=0.4, length_c=4e-3)
    expected_str_b_bound = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    waveform gauss_wf = gaussian(1000000.0ns, (1000000000.0*sigma_g)ns, 1, false);",
            "    waveform drag_gauss_wf = drag_gaussian(3000000.0ns, 400000000.0ns, 0.2, 1,"
            " false);",
            "    waveform constant_wf = constant(4000000.0ns, 2.0 + 0.3im);",
            "    waveform arb_wf = {1.0 + 0.4im, 0, 0.3, 0.1 + 0.2im};",
            "    bit[2] psb;",
            "    set_frequency(predefined_frame_1, a + 4);",
            "    shift_frequency(predefined_frame_1, a + 4);",
            "    set_phase(predefined_frame_1, a + 4);",
            "    shift_phase(predefined_frame_1, a + 4);",
            "    set_scale(predefined_frame_1, a + 4);",
            "    psb[0] = capture_v0(predefined_frame_1);",
            "    delay[(1000000000.0*a + 4000000000.0)ns] predefined_frame_1, predefined_frame_2;",
            "    delay[(1000000000.0*a + 4000000000.0)ns] predefined_frame_1;",
            "    delay[1000000.0ns] predefined_frame_1;",
            "    barrier predefined_frame_1, predefined_frame_2;",
            "    play(predefined_frame_1, gauss_wf);",
            "    play(predefined_frame_2, drag_gauss_wf);",
            "    play(predefined_frame_1, constant_wf);",
            "    play(predefined_frame_2, arb_wf);",
            "    psb[1] = capture_v0(predefined_frame_2);",
            "}",
        ]
    )
    assert b_bound.to_ir() == b_bound_call.to_ir() == expected_str_b_bound
    assert pulse_sequence.to_ir() == expected_str_unbound
    assert b_bound.parameters == set([FreeParameter("sigma_g"), FreeParameter("a")])
    both_bound = b_bound.make_bound_pulse_sequence({"a": 1, "sigma_g": 0.7})
    both_bound_call = b_bound_call(1, sigma_g=0.7)  # use arg 1 for a
    expected_str_both_bound = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    waveform gauss_wf = gaussian(1000000.0ns, 700000000.0ns, 1, false);",
            "    waveform drag_gauss_wf = drag_gaussian(3000000.0ns, 400000000.0ns, 0.2, 1,"
            " false);",
            "    waveform constant_wf = constant(4000000.0ns, 2.0 + 0.3im);",
            "    waveform arb_wf = {1.0 + 0.4im, 0, 0.3, 0.1 + 0.2im};",
            "    bit[2] psb;",
            "    set_frequency(predefined_frame_1, 5);",
            "    shift_frequency(predefined_frame_1, 5);",
            "    set_phase(predefined_frame_1, 5);",
            "    shift_phase(predefined_frame_1, 5);",
            "    set_scale(predefined_frame_1, 5);",
            "    psb[0] = capture_v0(predefined_frame_1);",
            "    delay[5000000000.00000ns] predefined_frame_1, predefined_frame_2;",
            "    delay[5000000000.00000ns] predefined_frame_1;",
            "    delay[1000000.0ns] predefined_frame_1;",
            "    barrier predefined_frame_1, predefined_frame_2;",
            "    play(predefined_frame_1, gauss_wf);",
            "    play(predefined_frame_2, drag_gauss_wf);",
            "    play(predefined_frame_1, constant_wf);",
            "    play(predefined_frame_2, arb_wf);",
            "    psb[1] = capture_v0(predefined_frame_2);",
            "}",
        ]
    )
    assert both_bound.to_ir() == both_bound_call.to_ir() == expected_str_both_bound
    assert b_bound.to_ir() == b_bound_call.to_ir() == expected_str_b_bound
    assert pulse_sequence.to_ir() == expected_str_unbound


@pytest.mark.parametrize(
    "method_name, method_kwargs",
    [
        ("set_frequency", {"frequency": 1e4}),
        ("shift_frequency", {"frequency": 2e4}),
        ("set_phase", {"phase": 0.3}),
        ("shift_phase", {"phase": 0.2}),
        ("set_scale", {"scale": 0.7}),
        ("delay", {"duration": 1e-5}),
        ("barrier", None),
        ("play", {"waveform": ConstantWaveform(1e-3, complex(1, 2), "wf_id")}),
    ],
)
def test_pulse_sequence_conflicting_frames(
    user_defined_frame, conflicting_user_defined_frame, method_name, method_kwargs
):
    ps = PulseSequence().shift_frequency(user_defined_frame, 1e2)
    method = getattr(ps, method_name)

    with pytest.raises(ValueError):
        if method_kwargs:
            method(conflicting_user_defined_frame, **method_kwargs)
        else:
            method(conflicting_user_defined_frame)


def test_pulse_sequence_conflicting_wf(user_defined_frame):
    wf = ConstantWaveform(1e-3, complex(1, 2), "wf_id")
    conflicting_wf = ConstantWaveform(1e-4, complex(1, 2), "wf_id")
    ps = PulseSequence().play(user_defined_frame, wf)

    with pytest.raises(ValueError):
        ps.play(user_defined_frame, conflicting_wf)


def test_pulse_sequence_to_time_trace_program_mutation(user_defined_frame):
    wf = ConstantWaveform(1e-3, complex(1, 2), "wf_id")
    ps = PulseSequence().play(user_defined_frame, wf)
    initial_vars = dict(ps._program.undeclared_vars)
    ps.to_time_trace()
    assert initial_vars == ps._program.undeclared_vars


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
        .delay(QubitSet(0), 1e-3)
        .barrier(QubitSet([0, 1]))
        .barrier([predefined_frame_1, predefined_frame_2])
        .play(predefined_frame_1, GaussianWaveform(length=1e-3, sigma=0.7, id="gauss_wf"))
        .play(
            predefined_frame_2,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf"),
        )
        .play(
            predefined_frame_1,
            ConstantWaveform(length=4e-3, iq=complex(2, 0.3), id="constant_wf"),
        )
        .play(
            predefined_frame_2,
            ArbitraryWaveform([complex(1, 0.4), 0, 0.3, complex(0.1, 0.2)], id="arb_wf"),
        )
        .capture_v0(predefined_frame_2)
    )
    expected_str = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    waveform gauss_wf = gaussian(1000000.0ns, 700000000.0ns, 1, false);",
            "    waveform drag_gauss_wf = drag_gaussian(3000000.0ns, 400000000.0ns, 0.2, 1,"
            " false);",
            "    waveform constant_wf = constant(4000000.0ns, 2.0 + 0.3im);",
            "    waveform arb_wf = {1.0 + 0.4im, 0, 0.3, 0.1 + 0.2im};",
            "    bit[2] psb;",
            "    set_frequency(predefined_frame_1, 3000000000.0);",
            "    shift_frequency(predefined_frame_1, 1000000000.0);",
            "    set_phase(predefined_frame_1, -0.5);",
            "    shift_phase(predefined_frame_1, 0.1);",
            "    set_scale(predefined_frame_1, 0.25);",
            "    psb[0] = capture_v0(predefined_frame_1);",
            "    delay[2.0ns] predefined_frame_1, predefined_frame_2;",
            "    delay[1000.0ns] predefined_frame_1;",
            "    delay[1000000.0ns] $0;",
            "    barrier $0, $1;",
            "    barrier predefined_frame_1, predefined_frame_2;",
            "    play(predefined_frame_1, gauss_wf);",
            "    play(predefined_frame_2, drag_gauss_wf);",
            "    play(predefined_frame_1, constant_wf);",
            "    play(predefined_frame_2, arb_wf);",
            "    psb[1] = capture_v0(predefined_frame_2);",
            "}",
        ]
    )
    assert pulse_sequence.to_ir() == expected_str


def test_parse_from_calibration_schema(predefined_frame_1, predefined_frame_2):
    waveforms = {
        "drag_gauss_wf": DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf")
    }
    frames = {predefined_frame_1.id: predefined_frame_1, predefined_frame_2.id: predefined_frame_2}

    calibration_instrs = [
        {
            "name": "barrier",
            "arguments": [{"name": "qubit", "value": "0", "type": "string"}],
        },
        {
            "name": "play",
            "arguments": [
                {"name": "frame", "value": "predefined_frame_1", "type": "frame"},
                {
                    "name": "waveform",
                    "value": "drag_gauss_wf",
                    "type": "waveform",
                },
            ],
        },
        {
            "name": "barrier",
            "arguments": [
                {"name": "frame", "value": "predefined_frame_1", "type": "frame"},
                {"name": "frame", "value": "predefined_frame_2", "type": "frame"},
            ],
        },
        {
            "name": "barrier",
            "arguments": None,
        },
        {
            "name": "delay",
            "arguments": [
                {"name": "duration", "value": 3e-07, "type": "float"},
                {"name": "qubit", "value": "0", "type": "string"},
                {"name": "qubit", "value": "1", "type": "string"},
            ],
        },
        {
            "name": "delay",
            "arguments": [
                {"name": "frame", "value": "predefined_frame_1", "type": "frame"},
                {"name": "duration", "value": 3e-07, "type": "float"},
            ],
        },
        {
            "name": "shift_phase",
            "arguments": [
                {"name": "frame", "value": "predefined_frame_1", "type": "frame"},
                {"name": "phase", "value": 3e-07, "type": "float"},
            ],
        },
        {
            "name": "shift_frequency",
            "arguments": [
                {"name": "frequency", "value": "theta", "type": "expr"},
                {"name": "frame", "value": "predefined_frame_1", "type": "frame"},
                {"name": "extra", "value": "predefined_frame_1", "type": "string"},
            ],
        },
    ]

    expected_pulse_sequence = (
        PulseSequence()
        .barrier(QubitSet(0))
        .play(predefined_frame_1, waveforms["drag_gauss_wf"])
        .barrier([predefined_frame_1, predefined_frame_2])
        .barrier([])
        .delay(QubitSet([0, 1]), 3e-07)
        .delay([predefined_frame_1], 3e-07)
        .shift_phase(predefined_frame_1, 3e-07)
        .shift_frequency(predefined_frame_1, FreeParameter("theta"))
    )

    assert (
        PulseSequence._parse_from_calibration_schema(calibration_instrs, waveforms, frames)
        == expected_pulse_sequence
    )
