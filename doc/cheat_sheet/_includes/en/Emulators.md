| Task | Snippet |
|---|---|
| Imports | `from braket.emulation.local_emulator import LocalEmulator` |
| Create from an AWS QPU | `emulator = device.emulator()` |
| Create from device properties | `emulator = LocalEmulator.from_device_properties(device.properties)` |
| Create from JSON properties | `emulator = LocalEmulator.from_json(device_properties_json)` |
| Validate without running | `emulator.validate(circuit)` |
| Transform before running | `compiled = emulator.transform(circuit)` |
| Run through emulator backend | `result = emulator.run(circuit, shots=100).result()` |
| Add custom validation passes | `from braket.emulation import PassManager` |

Emulators mimic QPU restrictions and noise on a local simulator backend. They are useful for checking device compatibility before submitting to hardware.
