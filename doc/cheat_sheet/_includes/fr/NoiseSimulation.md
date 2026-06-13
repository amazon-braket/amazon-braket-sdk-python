| Imports | `from braket.circuits import Noise, Gate` |
| Bruit dépolarisant | `circuit.depolarizing(0, 0.1)` |
| Appliquer un opérateur de Kraus | `circuit.kraus([0,2], [E0, E1])` |
| Canal d'amortissement de phase | `noise = Noise.PhaseDamping(0.1)` |
| Appliquer un canal de bruit | `circuit.apply_gate_noise(noise, Gate.X)` |
