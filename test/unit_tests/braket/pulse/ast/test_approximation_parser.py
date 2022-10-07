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

from typing import List, Union
from unittest.mock import Mock

import numpy as np
import pytest
from oqpy import IntVar
from oqpy.vendor.openpulse import ast

from braket.pulse import ArbitraryWaveform, ConstantWaveform, DragGaussianWaveform, GaussianWaveform
from braket.pulse.ast.approximation_parser import _ApproximationParser
from braket.pulse.frame import Frame
from braket.pulse.port import Port
from braket.pulse.pulse_sequence import PulseSequence
from braket.timings.time_series import TimeSeries, _all_close


@pytest.fixture
def port():
    return Port(port_id="device_port_x0", dt=1e-9, properties={})


def test_bare_pulsequence():
    pulse_seq = PulseSequence()
    results = pulse_seq.generate_approximation()
    verify_results(results, {}, {}, {})


def test_delay(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = PulseSequence().delay(frame, 3e-9)
    # 3 datapoints for delay

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    # 2 datapoints for first delay
    expected_amplitudes["frame1"].put(0, 0).put(2e-9, 0)
    expected_frequencies["frame1"].put(0, 1e8).put(2e-9, 1e8)
    expected_phases["frame1"].put(0, 0).put(2e-9, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_predefined_frame(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=True)
    pulse_seq = PulseSequence().delay(frame, 3e-9)
    # 3 datapoints for delay

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    # 2 datapoints for first delay
    expected_amplitudes["frame1"].put(0, 0).put(2e-9, 0)
    expected_frequencies["frame1"].put(0, 1e8).put(2e-9, 1e8)
    expected_phases["frame1"].put(0, 0).put(2e-9, 0)

    for statement in pulse_seq._program.state.body:
        assert type(statement) != ast.FrameType

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_set_shift_phase(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = (
        PulseSequence()
        .set_phase(frame, 1)
        .delay(frame, 2e-9)
        .shift_phase(frame, 2)
        .delay(frame, 5e-9)
        .set_phase(frame, 0)
    )
    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    # 2 datapoints for first delay
    # Parser does not like delay 2ns
    expected_amplitudes["frame1"].put(0, 0).put(1e-9, 0)
    expected_frequencies["frame1"].put(0, 1e8).put(1e-9, 1e8)
    expected_phases["frame1"].put(0, 1).put(1e-9, 1)

    # set_shift_phase should be instantaneous (result on current or next datapoint?)
    # 5 dt for second delay
    # shift_phase adds 2 to the phase of the last point -> 3
    expected_amplitudes["frame1"].put(2e-9, 0).put(6e-9, 0)
    expected_frequencies["frame1"].put(2e-9, 1e8).put(6e-9, 1e8)
    expected_phases["frame1"].put(2e-9, 3).put(6e-9, 3)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_set_shift_frequency(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = (
        PulseSequence()
        .set_frequency(frame, 2e8)
        .delay(frame, 20e-9)
        .shift_frequency(frame, -0.1e8)
        .delay(frame, 10e-9)
    )
    # 2 datapoints for delay
    # set_shift_phase should be instantaneous (result on current or next datapoint?)
    # shift_phase adds 2 to the phase of the last point -> 3

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    # 2 datapoints for first delay
    expected_amplitudes["frame1"].put(0, 0).put(19e-9, 0)
    expected_frequencies["frame1"].put(0, 2e8).put(19e-9, 2e8)
    expected_phases["frame1"].put(0, 0).put(19e-9, 0)

    # set_shift_phase should be instantaneous (result on current or next datapoint?)
    # 5 dt for second delay
    # shift_phase adds 2 to the phase of the last point -> 3
    expected_amplitudes["frame1"].put(20e-9, 0).put(29e-9, 0)
    expected_frequencies["frame1"].put(20e-9, 1.9e8).put(29e-9, 1.9e8)
    expected_phases["frame1"].put(20e-9, 0).put(29e-9, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_play_arbitrary_waveforms(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    my_arb_wf = ArbitraryWaveform([0.4 + 0.1j, -0.8 + 0.1j, 1 + 0.2j])
    pulse_seq = PulseSequence().play(frame, my_arb_wf)
    # 3 datapoints for arb wf play

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    times = np.arange(0, 4e-9, port.dt)
    for t, v in zip(times, [0.4 + 0.1j, -0.8 + 0.1j, 1 + 0.2j]):
        expected_amplitudes["frame1"].put(t, v)
        expected_frequencies["frame1"].put(t, 1e8)
        expected_phases["frame1"].put(t, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_play_literal(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = PulseSequence()
    pulse_seq._program.play(frame=frame, waveform=[0.4 + 0.1j, -0.8 + 0.1j, 1 + 0.2j])
    # 3 datapoints for arb wf play

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    times = np.arange(0, 4e-9, port.dt)
    for t, v in zip(times, [0.4 + 0.1j, -0.8 + 0.1j, 1 + 0.2j]):
        expected_amplitudes["frame1"].put(t, v)
        expected_frequencies["frame1"].put(t, 1e8)
        expected_phases["frame1"].put(t, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_classical_variable_declaration(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = PulseSequence()
    i = IntVar(5, "i")
    pulse_seq._program.increment(i, 1)

    with pytest.raises(NotImplementedError):
        _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))


def test_play_constant_waveforms(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    length = 6e-9
    pulse_seq = PulseSequence().play(frame, ConstantWaveform(length, 0.75))

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    times = np.arange(0, length, port.dt)
    values = 0.75 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(t, v)
        expected_frequencies["frame1"].put(t, 1e8)
        expected_phases["frame1"].put(t, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_set_scale(port):
    frame = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = (
        PulseSequence()
        .play(frame, ConstantWaveform(10e-9, 0.66))
        .set_scale(frame, 0.5)
        .play(frame, ConstantWaveform(20e-9, 0.66))
    )

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    times = np.arange(0, 10e-9, port.dt)
    values = 0.66 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(t, v)
        expected_frequencies["frame1"].put(t, 1e8)
        expected_phases["frame1"].put(t, 0)

    shift_time = 10e-9
    times = np.arange(0, 20e-9, port.dt)
    values = 0.33 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(shift_time + t, v)
        expected_frequencies["frame1"].put(shift_time + t, 1e8)
        expected_phases["frame1"].put(shift_time + t, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_play_gaussian_waveforms(port):
    frame1 = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)

    # First gaussian with zero_at_edges=False
    gaussian_wf_ZaE_False = GaussianWaveform(
        length=1e-8, sigma=1.69e-9, amplitude=1.0, zero_at_edges=False
    )
    pulse_seq = PulseSequence().play(frame1, gaussian_wf_ZaE_False)
    # X datapoints...

    times = np.arange(0, 1e-8, port.dt)
    values = np.array(
        [
            complex(0.012568049266111367),
            complex(0.06074792381889125),
            complex(0.20688853998666168),
            complex(0.49645839613814063),
            complex(0.839403382587157),
            complex(1.0),
            complex(0.839403382587157),
            complex(0.49645839613814063),
            complex(0.20688853998666168),
            complex(0.06074792381889125),
        ],
        dtype=np.complex128,
    )

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(t, v)
        expected_frequencies["frame1"].put(t, 1e8)
        expected_phases["frame1"].put(t, 0)

    # Add a delay between the two waveforms
    pulse_seq.delay(frame1, 2e-8)
    expected_amplitudes["frame1"].put(1e-8, 0).put(29e-9, 0)
    expected_frequencies["frame1"].put(1e-8, 1e8).put(29e-9, 1e8)
    expected_phases["frame1"].put(1e-8, 0).put(29e-9, 0)

    # Second gaussian with zero_at_edges=True
    gaussian_wf_ZaE_True = GaussianWaveform(
        length=1e-8, sigma=1.69e-9, amplitude=1.0, zero_at_edges=True
    )
    pulse_seq.play(frame1, gaussian_wf_ZaE_True)
    # X datapoints...

    times = np.arange(0, 1e-8, port.dt)
    values = np.array(
        [
            0.0 + 0.0j,
            complex(0.04879311),
            complex(0.1967938),
            complex(0.49004931),
            complex(0.83735931),
            complex(1.0),
            complex(0.83735931),
            complex(0.49004931),
            complex(0.1967938),
            complex(0.04879311),
        ],
        dtype=np.complex128,
    )

    shift_time = 30e-9
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(t + shift_time, v)
        expected_frequencies["frame1"].put(t + shift_time, 1e8)
        expected_phases["frame1"].put(t + shift_time, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame1))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_play_drag_gaussian_waveforms(port):
    frame1 = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)

    expected_amplitudes = {"frame1": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries()}
    expected_phases = {"frame1": TimeSeries()}

    drag_gaussian_wf_ZaE_False = DragGaussianWaveform(
        length=1e-8, sigma=1.69e-9, amplitude=1.0, beta=1e-9, zero_at_edges=False
    )
    drag_gaussian_wf_ZaE_True = DragGaussianWaveform(
        length=1e-8, sigma=1.69e-9, amplitude=1.0, beta=1e-9
    )
    pulse_seq = (
        PulseSequence()
        .play(frame1, drag_gaussian_wf_ZaE_False)
        .delay(frame1, 2e-8)
        .play(frame1, drag_gaussian_wf_ZaE_True)
    )

    # First DRAG_Gaussian with zero_at_edges=False
    times = np.arange(0, 1e-8, port.dt)
    values = np.array(
        [
            complex(0.012568049266111367, 0.02200211698839566),
            complex(0.06074792381889125, 0.08507814687005531),
            complex(0.20688853998666168, 0.21731228597037397),
            complex(0.49645839613814063, 0.3476477687322857),
            complex(0.839403382587157, 0.29389845684225235),
            complex(1.0, 0.0),
            complex(0.839403382587157, -0.29389845684225235),
            complex(0.49645839613814063, -0.3476477687322857),
            complex(0.20688853998666168, -0.21731228597037397),
            complex(0.06074792381889125, -0.08507814687005531),
        ],
        dtype=np.complex128,
    )

    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(t, v)
        expected_frequencies["frame1"].put(t, 1e8)
        expected_phases["frame1"].put(t, 0)

    # Add a delay between the two waveforms
    shift_time = 10e-9
    expected_amplitudes["frame1"].put(shift_time + 0, 0).put(shift_time + 19e-9, 0)
    expected_frequencies["frame1"].put(shift_time + 0, 1e8).put(shift_time + 19e-9, 1e8)
    expected_phases["frame1"].put(shift_time + 0, 0).put(shift_time + 19e-9, 0)

    # Second DRAG_Gaussian with zero_at_edges=True
    times = np.arange(0, 1e-8, port.dt)
    values = np.array(
        [
            0.0 + 0.0j,
            0.04879311 + 0.06833529j,
            0.1967938 + 0.20670894j,
            0.49004931 + 0.34315977j,
            0.83735931 + 0.29318277j,
            1.0 + 0.0j,
            0.83735931 - 0.29318277j,
            0.49004931 - 0.34315977j,
            0.1967938 - 0.20670894j,
            0.04879311 - 0.06833529j,
        ],
        dtype=np.complex128,
    )

    shift_time = shift_time + 20e-9
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(t + shift_time, v)
        expected_frequencies["frame1"].put(t + shift_time, 1e8)
        expected_phases["frame1"].put(t + shift_time, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict(frame1))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_barrier_same_dt(port):
    frame1 = Frame(frame_id="frame1", port=port, frequency=1e8, phase=0, is_predefined=False)
    frame2 = Frame(frame_id="frame2", port=port, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = (
        PulseSequence()
        .play(frame1, ConstantWaveform(12e-9, 0.75))  # Inst1
        .barrier([frame1, frame2])  # Inst2
        .play(frame1, ConstantWaveform(16e-9, 1))  # Inst3
        .play(frame2, ConstantWaveform(8e-9, -1))  # Inst4
    )

    expected_amplitudes = {"frame1": TimeSeries(), "frame2": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries(), "frame2": TimeSeries()}
    expected_phases = {"frame1": TimeSeries(), "frame2": TimeSeries()}

    # Inst1
    shift_time_frame1 = 0
    pulse_length = 12e-9
    times = np.arange(0, pulse_length, port.dt)
    values = 0.75 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(shift_time_frame1 + t, v)
        expected_frequencies["frame1"].put(shift_time_frame1 + t, 1e8)
        expected_phases["frame1"].put(shift_time_frame1 + t, 0)

    # Inst2
    # Delay frame2 from 0ns to 11ns
    shift_time_frame2 = 0

    expected_amplitudes["frame2"].put(0, 0).put(11e-9, 0)
    expected_frequencies["frame2"].put(0, 1e8).put(11e-9, 1e8)
    expected_phases["frame2"].put(0, 0).put(11e-9, 0)

    # Inst3
    shift_time_frame1 = shift_time_frame1 + pulse_length
    pulse_length = 16e-9
    times = np.arange(0, pulse_length, port.dt)
    values = 1 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(shift_time_frame1 + t, v)
        expected_frequencies["frame1"].put(shift_time_frame1 + t, 1e8)
        expected_phases["frame1"].put(shift_time_frame1 + t, 0)

    # Inst4
    shift_time_frame2 = shift_time_frame1
    pulse_length = 8e-9
    times = np.arange(0, pulse_length, port.dt)
    values = -1 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame2"].put(shift_time_frame2 + t, v)
        expected_frequencies["frame2"].put(shift_time_frame2 + t, 1e8)
        expected_phases["frame2"].put(shift_time_frame2 + t, 0)

    # # Pad frame2
    # shift_time_frame2 = shift_time_frame2 + pulse_length
    # last_time_frame1 = expected_amplitudes["frame1"].times()[-1]

    # # Do we need to pad frame1?
    # expected_amplitudes["frame1"].put(last_time_frame1 + port.dt, 0)
    # expected_frequencies["frame1"].put(last_time_frame1 + port.dt, 1e8)
    # expected_phases["frame1"].put(last_time_frame1 + port.dt, 0)

    # expected_amplitudes["frame2"].put(shift_time_frame2, 0).put(
    #     last_time_frame1 + port.dt, 0
    # )
    # expected_frequencies["frame2"].put(shift_time_frame2, 1e8).put(
    #     last_time_frame1 + port.dt, 1e8
    # )
    # expected_phases["frame2"].put(shift_time_frame2, 0).put(last_time_frame1 + port.dt, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict([frame1, frame2]))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)
    # Array retrievable with
    # x=np.arange(0, ts.times()+1e-9, 1e-9)
    # np.interp(x, ts.times(), ts.values()) # See last cells of SDK Testing.ipynb


def test_barrier_different_dt(port):
    port1 = Port(port_id="device_port_x1", dt=5e-9, properties={})
    port2 = Port(port_id="device_port_x2", dt=4e-9, properties={})
    frame1 = Frame(frame_id="frame1", port=port1, frequency=1e8, phase=0, is_predefined=False)
    frame2 = Frame(frame_id="frame2", port=port2, frequency=1e8, phase=0, is_predefined=False)
    pulse_seq = (
        PulseSequence()
        .play(frame1, ConstantWaveform(25e-9, 0.75))  # Inst 1
        .barrier([frame1, frame2])  # Inst 2
        .play(frame1, ConstantWaveform(40e-9, 1))  # Inst 3
        .play(frame2, ConstantWaveform(28e-9, -1))  # Inst 4
    )

    expected_amplitudes = {"frame1": TimeSeries(), "frame2": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries(), "frame2": TimeSeries()}
    expected_phases = {"frame1": TimeSeries(), "frame2": TimeSeries()}

    # Inst1
    shift_time_frame1 = 0
    pulse_length = 25e-9
    times = np.arange(0, pulse_length, port1.dt)
    values = 0.75 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(shift_time_frame1 + t, v)
        expected_frequencies["frame1"].put(shift_time_frame1 + t, 1e8)
        expected_phases["frame1"].put(shift_time_frame1 + t, 0)

    # Inst2
    # barrier at 35ns (first point coinciding with frame2: np.ceil(max(20,0)/np.lcm(dt1=5,dt2=7))*np.lcm(dt1=5,dt2=7)) # noqa
    # reset shift_time_frame1 = shift_time_frame2 = 35
    shift_time_frame1 = shift_time_frame2 = 40e-9

    latest_time_frame1 = expected_amplitudes["frame1"].times()[-1]
    expected_amplitudes["frame1"].put(latest_time_frame1 + port1.dt, 0).put(
        shift_time_frame1 - port1.dt, 0
    )
    expected_frequencies["frame1"].put(latest_time_frame1 + port1.dt, 1e8).put(
        shift_time_frame1 - port1.dt, 1e8
    )
    expected_phases["frame1"].put(latest_time_frame1 + port1.dt, 0).put(
        shift_time_frame1 - port1.dt, 0
    )

    expected_amplitudes["frame2"].put(0, 0).put(shift_time_frame2 - port2.dt, 0)
    expected_frequencies["frame2"].put(0, 1e8).put(shift_time_frame2 - port2.dt, 1e8)
    expected_phases["frame2"].put(0, 0).put(shift_time_frame2 - port2.dt, 0)

    # Inst3
    pulse_length = 40e-9
    times = np.arange(0, pulse_length, port1.dt)
    values = 1 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(shift_time_frame1 + t, v)
        expected_frequencies["frame1"].put(shift_time_frame1 + t, 1e8)
        expected_phases["frame1"].put(shift_time_frame1 + t, 0)

    # Inst4
    pulse_length = 28e-9
    times = np.arange(0, pulse_length, port2.dt)
    values = -1 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame2"].put(shift_time_frame2 + t, v)
        expected_frequencies["frame2"].put(shift_time_frame2 + t, 1e8)
        expected_phases["frame2"].put(shift_time_frame2 + t, 0)

    # # Pad frame2
    # shift_time_frame2 = shift_time_frame2 + pulse_length
    # last_time = 80e-9
    # expected_amplitudes["frame2"].put(shift_time_frame2, 0).put(last_time, 0)
    # expected_frequencies["frame2"].put(shift_time_frame2, 1e8).put(last_time, 1e8)
    # expected_phases["frame2"].put(shift_time_frame2, 0).put(last_time, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict([frame1, frame2]))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


def test_pad_different_dt(port):
    port1 = Port(port_id="device_port_x1", dt=5e-9, properties={})
    port2 = Port(port_id="device_port_x2", dt=4e-9, properties={})
    frame1 = Frame(frame_id="frame1", port=port1, frequency=1e8, phase=0, is_predefined=False)
    frame2 = Frame(frame_id="frame2", port=port2, frequency=1e8, phase=0, is_predefined=False)

    pulse_seq = (
        PulseSequence()
        .play(frame1, ConstantWaveform(20e-9, 0.75))
        .play(frame2, ConstantWaveform(28e-9, -1))
    )

    expected_amplitudes = {"frame1": TimeSeries(), "frame2": TimeSeries()}
    expected_frequencies = {"frame1": TimeSeries(), "frame2": TimeSeries()}
    expected_phases = {"frame1": TimeSeries(), "frame2": TimeSeries()}

    # Inst1
    shift_time_frame1 = 0
    pulse_length = 20e-9
    times = np.arange(0, pulse_length, port1.dt)
    values = 0.75 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame1"].put(shift_time_frame1 + t, v)
        expected_frequencies["frame1"].put(shift_time_frame1 + t, 1e8)
        expected_phases["frame1"].put(shift_time_frame1 + t, 0)

    # Inst2
    shift_time_frame2 = 0
    pulse_length = 28e-9
    times = np.arange(0, pulse_length, port2.dt)
    values = -1 * np.ones_like(times)
    for t, v in zip(times, values):
        expected_amplitudes["frame2"].put(shift_time_frame2 + t, v)
        expected_frequencies["frame2"].put(shift_time_frame2 + t, 1e8)
        expected_phases["frame2"].put(shift_time_frame2 + t, 0)

    # # Pad all frames to end up
    # last_time_frame1 = expected_amplitudes["frame1"].times()[-1]
    # last_time_frame2 = expected_amplitudes["frame2"].times()[-1]

    # last_time = 40e-9
    # expected_amplitudes["frame1"].put(last_time_frame1 + port1.dt, 0).put(last_time, 0)
    # expected_frequencies["frame1"].put(last_time_frame1 + port1.dt, 1e8).put(last_time, 1e8) # noqa
    # expected_phases["frame1"].put(last_time_frame1 + port1.dt, 0).put(last_time, 0)
    # expected_amplitudes["frame2"].put(last_time_frame2 + port2.dt, 0).put(last_time, 0)
    # expected_frequencies["frame2"].put(last_time_frame2 + port2.dt, 1e8).put(last_time, 1e8) # noqa
    # expected_phases["frame2"].put(last_time_frame2 + port2.dt, 0).put(last_time, 0)

    parser = _ApproximationParser(program=pulse_seq._program, frames=to_dict([frame1, frame2]))

    verify_results(parser, expected_amplitudes, expected_frequencies, expected_phases)


@pytest.mark.parametrize(
    "literal_type, lhs, operator, rhs, expected_result",
    [
        (ast.FloatLiteral, 3, "+", 2, 5),
        (ast.FloatLiteral, 3, "-", 2, 1),
        (ast.FloatLiteral, 3, "*", 2, 6),
        (ast.FloatLiteral, 3, "/", 2, 1.5),
        (ast.FloatLiteral, 3, "%", 2, 1),
        (ast.FloatLiteral, 3, "**", 2, 9),
        (ast.FloatLiteral, 3, "<", 2, False),
        (ast.FloatLiteral, 3, ">", 2, True),
        (ast.FloatLiteral, 3, ">=", 2, True),
        (ast.FloatLiteral, 3, "<=", 2, False),
        (ast.FloatLiteral, 3, "==", 2, False),
        (ast.FloatLiteral, 3, "!=", 2, True),
        (ast.BooleanLiteral, True, "&&", False, False),
        (ast.BooleanLiteral, True, "||", False, True),
        (ast.BooleanLiteral, True, "|", False, True),
        (ast.BooleanLiteral, True, "^", False, True),
        (ast.BooleanLiteral, True, "&", False, False),
        (ast.IntegerLiteral, 3, "<<", 2, 12),
        (ast.IntegerLiteral, 3, ">>", 2, 0),
    ],
)
def test_binary_operations(literal_type, lhs, operator, rhs, expected_result):
    expression = ast.BinaryExpression(
        lhs=literal_type(lhs),
        op=ast.BinaryOperator[operator],
        rhs=literal_type(rhs),
    )
    pulse_seq = PulseSequence()
    parser = _ApproximationParser(program=pulse_seq._program, frames={})
    result = parser.visit_BinaryExpression(expression, Mock())
    assert result == expected_result


@pytest.mark.parametrize(
    "literal_type, operator, literal, expected_result",
    [
        (ast.FloatLiteral, "-", 3, -3),
        (ast.BooleanLiteral, "!", True, False),
        (ast.IntegerLiteral, "~", 3, ~3),
    ],
)
def test_unary_operations(literal_type, operator, literal, expected_result):
    expression = ast.UnaryExpression(
        op=ast.UnaryOperator[operator], expression=literal_type(literal)
    )
    pulse_seq = PulseSequence()
    parser = _ApproximationParser(program=pulse_seq._program, frames={})
    result = parser.visit_UnaryExpression(expression, Mock())
    assert result == expected_result


@pytest.mark.xfail(raises=ValueError)
def test_duration_literal():
    literal = Mock()
    pulse_seq = PulseSequence()
    parser = _ApproximationParser(program=pulse_seq._program, frames={})
    parser.visit_DurationLiteral(literal, Mock())


def verify_results(results, expected_amplitudes, expected_frequencies, expected_phases):
    for frame_id in expected_amplitudes.keys():
        assert _all_close(results.amplitudes[frame_id], expected_amplitudes[frame_id])
        assert _all_close(results.frequencies[frame_id], expected_frequencies[frame_id])
        assert _all_close(results.phases[frame_id], expected_phases[frame_id])


def to_dict(frames: Union[Frame, List]):
    if not isinstance(frames, List):
        frames = [frames]
    frame_dict = dict()
    for frame in frames:
        frame_dict[frame.id] = frame
    return frame_dict
