|                      |                                                       |
| -------------------- | ----------------------------------------------------- |
| Create a pulse sequence | pulse_sequence = PulseSequence() |
| Dictionary of predefined ports | device.ports |
| Dictionary of predefined frames | device.frames |
| Create a frame | Frame(port, frequency[, phase]) |
| Predefined waveforms | ConstantWaveform(length, iq) | GaussianWaveform(length, width, amplitude, zero_at_edges) | DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges) |
| Play a waveform | pulse_sequence.play(frame, waveform) |
| Add a delay | pulse_sequence.delay(frame, delay) |
| Set and Shift frequency | pulse_sequence.set_frequency(frame, frequency).shift_frequency(frame, detuning) |
| Set and Shift phase | pulse_sequence.set_phase(frame, phase).shift_phase(frame, phi) |
| Get the time series | pulse_sequence.to_time_traces() |