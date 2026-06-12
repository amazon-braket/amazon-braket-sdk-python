| Imports | `from braket.devices import LocalSimulator` |
| Instantiate the local simulator | `local_sim = LocalSimulator()` |
| Instantiate with backend | `local_sim = LocalSimulator("default")` |
| Instantiate with noise model | `local_sim = LocalSimulator(noise_model=noise_model)` |
| Run a local task | `task = local_sim.run(circuit, shots=100)` |
| Run a local batch | `batch = local_sim.run_batch([circuit1, circuit2], shots=100)` |
| Get available local backends | `LocalSimulator.registered_backends()` |
| Get simulator properties | `local_sim.properties` |