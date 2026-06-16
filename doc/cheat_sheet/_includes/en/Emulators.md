| Imports | `from braket.emulation import LocalEmulator` |
| Create from device properties | `emulator = LocalEmulator.from_device_properties(device.properties)` |
| With a noise model | `emulator = LocalEmulator.from_device_properties(device.properties, noise_model=noise_model)` |
| Backend simulator | `backend = LocalSimulator("braket_dm")`<br>`emulator = LocalEmulator.from_device_properties(device_properties, backend=backend)` |
| Run a circuit on the emulator | `task = emulator.run(circuit, shots=100)` |
