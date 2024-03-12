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

"""Tests for the pulse control module."""

import textwrap

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import rx
from braket.experimental.autoqasm.pulse import (
    barrier,
    capture_v0,
    delay,
    play,
    set_frequency,
    set_phase,
    set_scale,
    shift_frequency,
    shift_phase,
)
from braket.parametric import FreeParameter
from braket.pulse import ArbitraryWaveform, Frame, Port

PORT = Port(port_id="device_port_x0", dt=1e-9, properties={})
FRAME1 = Frame(frame_id="predefined_frame_1", frequency=2e9, port=PORT, phase=0, is_predefined=True)
FRAME2 = Frame(frame_id="predefined_frame_2", frequency=1e6, port=PORT, is_predefined=True)
WAVEFORM = ArbitraryWaveform([complex(1, 0.4), 0, 0.3, complex(0.1, 0.2)], id="arb_wf")


def test_mix_gate_pulse() -> None:
    """Test mixed usage of gates and pulses."""

    @aq.main
    def my_program():
        shift_frequency(FRAME1, 0.1234)
        rx(1, 0.1)
        play(FRAME1, WAVEFORM)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        cal {
            waveform arb_wf = {1.0 + 0.4im, 0, 0.3, 0.1 + 0.2im};
        }
        qubit[2] __qubits__;
        cal {
            shift_frequency(predefined_frame_1, 0.1234);
        }
        rx(0.1) __qubits__[1];
        cal {
            play(predefined_frame_1, arb_wf);
        }
        """
    ).strip()
    assert my_program.build().to_ir() == expected


def test_merge_cal_box() -> None:
    """Test subsequent cal boxes are merged."""

    @aq.main
    def my_program():
        barrier("$0")
        delay(["$3", "$4"], 0.34)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        cal {
            barrier $0;
            delay[340.0ms] $3, $4;
        }
        """
    ).strip()
    assert my_program.build().to_ir() == expected


@pytest.mark.parametrize(
    "instruction,qubits_or_frames,params,expected_qasm",
    [
        (
            shift_frequency,
            FRAME1,
            [0.12],
            "\ncal {\n    shift_frequency(predefined_frame_1, 0.12);\n}",
        ),
        (
            set_frequency,
            FRAME1,
            [0.12],
            "\ncal {\n    set_frequency(predefined_frame_1, 0.12);\n}",
        ),
        (
            shift_phase,
            FRAME1,
            [0.12],
            "\ncal {\n    shift_phase(predefined_frame_1, 0.12);\n}",
        ),
        (
            set_phase,
            FRAME1,
            [0.12],
            "\ncal {\n    set_phase(predefined_frame_1, 0.12);\n}",
        ),
        (
            set_scale,
            FRAME1,
            [0.12],
            "\ncal {\n    set_scale(predefined_frame_1, 0.12);\n}",
        ),
        (delay, "$3", [0.34], "\ncal {\n    delay[340.0ms] $3;\n}"),
        (delay, ["$3", "$4"], [0.34], "\ncal {\n    delay[340.0ms] $3, $4;\n}"),
        (
            delay,
            FRAME1,
            [0.34],
            "\ncal {\n    delay[340.0ms] predefined_frame_1;\n}",
        ),
        (
            delay,
            [FRAME1, FRAME2],
            [0.34],
            "\ncal {\n    delay[340.0ms] predefined_frame_1, predefined_frame_2;\n}",
        ),
        (barrier, "$3", [], "\ncal {\n    barrier $3;\n}"),
        (barrier, ["$3", "$4"], [], "\ncal {\n    barrier $3, $4;\n}"),
        (barrier, FRAME1, [], "\ncal {\n    barrier predefined_frame_1;\n}"),
        (
            barrier,
            [FRAME1, FRAME2],
            [],
            "\ncal {\n    barrier predefined_frame_1, predefined_frame_2;\n}",
        ),
        (
            play,
            FRAME1,
            [WAVEFORM],
            (
                "\ncal {\n    waveform arb_wf = {1.0 + 0.4im, 0, 0.3, 0.1 + 0.2im};"
                "\n    play(predefined_frame_1, arb_wf);\n}"
            ),
        ),
        (
            capture_v0,
            FRAME1,
            [],
            ("\nbit __bit_0__;" "\ncal {\n    __bit_0__ = capture_v0(predefined_frame_1);\n}"),
        ),
    ],
)
def test_pulse_control(instruction, qubits_or_frames, params, expected_qasm) -> None:
    """Test pulse control operations."""
    with aq.build_program() as program_conversion_context:
        instruction(qubits_or_frames, *params)

    assert expected_qasm in program_conversion_context.make_program().to_ir()


@pytest.mark.parametrize(
    "instruction,qubits_or_frames,params",
    [
        (barrier, "1", []),
        (barrier, 1, []),
        (barrier, ["1", "2"], []),
        (barrier, [1, 2], []),
    ],
)
def test_pulse_control_invalid_physical_qubit(instruction, qubits_or_frames, params) -> None:
    """Test pulse control operations with invalid lables for physical qubits."""
    with pytest.raises(ValueError):
        with aq.build_program():
            instruction(qubits_or_frames, *params)


def test_pulse_freeparameter() -> None:
    """Test pulse program with free parameter."""

    @aq.main
    def my_program(duration):
        delay(["$3", "$4"], duration)
        delay(["$3", "$4"], FreeParameter("duration2"))

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        input float duration;
        input float duration2;
        cal {
            delay[duration * 1s] $3, $4;
            delay[duration2 * 1s] $3, $4;
        }
        """
    ).strip()
    assert my_program.build().to_ir() == expected


def test_pulse_freeparameter_bound() -> None:
    """Test pulse program with freeparameter bound with values."""

    @aq.main
    def my_program(duration):
        delay(["$3", "$4"], duration)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        float duration = 0.123;
        cal {
            delay[duration * 1s] $3, $4;
        }
        """
    ).strip()
    qasm = my_program.build().make_bound_program({"duration": 0.123}).to_ir()
    assert qasm == expected


def test_pulse_freeparameter_condition() -> None:
    """Test pulse program with freeparameter in condition."""

    @aq.main
    def my_program(duration, duration2):
        delay(["$3", "$4"], duration)
        if duration > duration2:
            delay(["$3", "$4"], duration2)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        input float duration;
        input float duration2;
        cal {
            delay[duration * 1s] $3, $4;
        }
        bool __bool_0__;
        __bool_0__ = duration > duration2;
        if (__bool_0__) {
            cal {
                delay[duration2 * 1s] $3, $4;
            }
        }
        """
    ).strip()
    assert my_program.build().to_ir() == expected
