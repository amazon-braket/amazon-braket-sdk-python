| Task | Snippet |
|---|---|
| Imports | `from braket.pulse import Frame, PulseSequence`<br>`from braket.pulse.waveforms import ConstantWaveform, DragGaussianWaveform, GaussianWaveform` |
| Create a pulse sequence | `pulse_sequence = PulseSequence()` |
| Use predefined ports | `ports = device.ports` |
| Use predefined frames | `frames = device.frames` |
| Create a frame | `frame = Frame(port, frequency, phase=0)` |
| Constant waveform | `waveform = ConstantWaveform(length, iq)` |
| Gaussian waveform | `waveform = GaussianWaveform(length, width, amplitude, zero_at_edges=True)` |
| DRAG Gaussian waveform | `waveform = DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges=True)` |
| Play a waveform | `pulse_sequence.play(frame, waveform)` |
| Delay a frame | `pulse_sequence.delay(frame, delay)` |
| Shift frequency or phase | `pulse_sequence.shift_frequency(frame, detuning)`<br>`pulse_sequence.shift_phase(frame, phi)` |
| View time traces | `pulse_sequence.to_time_traces()` |
