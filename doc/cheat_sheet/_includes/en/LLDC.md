| Imports | `from braket.pulse import PulseSequence, Frame`<br>`from braket.pulse.waveforms import *` |
| Create a new pulse sequence | `pulse_sequence = PulseSequence()` |
| Predefined ports | `device.ports` |
| Predefined frames | `device.frames` |
| Create a frame | `Frame(port, frequency[, phase])` |
| Predefined waveforms | `ConstantWaveform(length, iq)`<br>`GaussianWaveform(length, width, amplitude, zero_at_edges)`<br>`DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges)` |
| Play a waveform | `pulse_sequence.play(frame, waveform)` |
| Add a delay | `pulse_sequence.delay(frame, delay)` |
| Set frequency | `pulse_sequence.set_frequency(frame, frequency)` |
| Shift frequency | `pulse_sequence.shift_frequency(frame, detuning)` |
| Set phase | `pulse_sequence.set_phase(frame, phase)` |
| Shift phase | `pulse_sequence.shift_phase(frame, phi)` |
| Get the time series | `pulse_sequence.to_time_traces()` |
