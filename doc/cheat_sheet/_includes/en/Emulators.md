| Imports | `from braket.aws import AwsDevice`<br>`from braket.devices import Devices, LocalSimulator`<br>`from braket.emulation import Emulator`<br>`from braket.emulation.local_emulator import LocalEmulator` |
| Get an emulator for a QPU<!-- LLM: . Emulators are only available for QPUs; requesting one from a managed simulator raises an error--> | `emulator = AwsDevice(Devices.IQM.Garnet).emulator` |
| Validate a circuit against device constraints | `emulator.validate(circuit)` |
| Compile a circuit to the device's native gates and connectivity | `compiled = emulator.transform(circuit)` |
| Run on the emulated backend (applies device noise) | `result = emulator.run(circuit, shots=100).result()` |
| Inspect the device noise model | `emulator.noise_model` |
| Build a custom emulator | `emulator = Emulator(backend=LocalSimulator("braket_dm"))` |
| Emulator from a device-properties JSON | `emulator = LocalEmulator.from_json(properties_json)` |
