| Imports | `from braket.circuits import Noise, Gate` |
| Depolarizing noise | `circuit.depolarizing(0, 0.1)` |
| Apply a Kraus operator | `circuit.kraus([0,2], [E0, E1])` |
| Phase damping channel | `noise = Noise.PhaseDamping(0.1)` |
| Apply a noise channel | `circuit.apply_gate_noise(noise, Gate.X)` |