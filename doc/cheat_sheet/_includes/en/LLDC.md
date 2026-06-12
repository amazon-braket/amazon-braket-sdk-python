| Imports | `from braket.pulse import PulseSequence, Frame`<br>`from braket.pulse.waveforms import ConstantWaveform, GaussianWaveform, DragGaussianWaveform` |
| Create a new pulse sequence | `pulse_sequence = PulseSequence()` |
| Predefined ports | `device.ports` |
| Predefined frames | `device.frames` |
| Create a frame | `frame = Frame(port, frequency, phase)` |
| Predefined waveforms | `ConstantWaveform(length, iq)`<br>`GaussianWaveform(length, width, amplitude, zero_at_edges)`<br>`DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges)` |
| Play a waveform | `pulse_sequence.play(frame, waveform)` |
| Add a delay | `pulse_sequence.delay(frame, delay)` |
| Set frequency | `pulse_sequence.set_frequency(frame, frequency)` |
| Shift frequency | `pulse_sequence.shift_frequency(frame, frequency_shift)` |
| Set phase | `pulse_sequence.set_phase(frame, phase)` |
| Shift phase | `pulse_sequence.shift_phase(frame, phase_shift)` |
| Swap phases | `pulse_sequence.swap_phases(frame_1, frame_2)` |
| Set scale | `pulse_sequence.set_scale(frame, scale)` |
| Add a barrier | `pulse_sequence.barrier([frame_1, frame_2])` |
| Capture from a frame | `pulse_sequence.capture_v0(frame)` |
| Bind pulse parameters | `pulse_sequence.make_bound_pulse_sequence({"theta": 0.1})` |
| Export to OpenPulse IR | `pulse_sequence.to_ir()` |
| Get the time trace | `pulse_sequence.to_time_trace()` |