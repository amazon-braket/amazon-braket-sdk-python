| Imports | `from braket.pulse import PulseSequence, Frame`<br>`from braket.pulse.waveforms import *` |
| Créer une nouvelle séquence d'impulsions | `pulse_sequence = PulseSequence()` |
| Ports prédéfinis | `device.ports` |
| Frames prédéfinis | `device.frames` |
| Créer un frame | `Frame(port, frequency[, phase])` |
| Formes d'onde prédéfinies | `ConstantWaveform(length, iq)`<br>`GaussianWaveform(length, width, amplitude, zero_at_edges)`<br>`DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges)` |
| Jouer une forme d'onde | `pulse_sequence.play(frame, waveform)` |
| Ajouter un délai | `pulse_sequence.delay(frame, delay)` |
| Définir la fréquence | `pulse_sequence.set_frequency(frame, frequency)` |
| Décaler la fréquence | `pulse_sequence.shift_frequency(frame, detuning)` |
| Définir la phase | `pulse_sequence.set_phase(frame, phase)` |
| Décaler la phase | `pulse_sequence.shift_phase(frame, phi)` |
| Obtenir la série temporelle | `pulse_sequence.to_time_traces()` |
