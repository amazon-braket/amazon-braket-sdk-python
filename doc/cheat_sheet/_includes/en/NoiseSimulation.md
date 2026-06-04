| Imports | `from braket.circuits import Gate, Noise` |
| Depolarizing noise | `circuit.depolarizing(0, probability=0.1)` |
| Apply a Kraus operator | `circuit.kraus([0, 2], matrices=[E0, E1])` |
| Phase damping channel | `noise = Noise.PhaseDamping(0.1)` |
| Apply a noise channel | `circuit.apply_gate_noise(noise, target_gates=Gate.X)` |