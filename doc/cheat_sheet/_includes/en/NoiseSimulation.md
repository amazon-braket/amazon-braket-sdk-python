| Task | Snippet |
|---|---|
| Imports | `from braket.circuits import Circuit, Gate, Noise`<br>`from braket.circuits.noise_model import GateCriteria, NoiseModel` |
| Add inline bit-flip noise | `circuit.bit_flip(0, probability=0.1)` |
| Add inline depolarizing noise | `circuit.depolarizing(0, probability=0.1)` |
| Add Kraus noise | `circuit.kraus([0, 2], [E0, E1])` |
| Create a noise channel | `noise = Noise.PhaseDamping(gamma=0.1)` |
| Apply noise after gates | `circuit.apply_gate_noise(noise, Gate.X)` |
| Build a noise model | `noise_model = NoiseModel().add_noise(Noise.BitFlip(0.05), GateCriteria(Gate.H))` |
| Run with local density-matrix simulator | `device = LocalSimulator("braket_dm", noise_model=noise_model)` |
