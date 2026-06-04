| Task | Code |

|---|---|

| Import LocalEmulator | `from braket.emulation.local\_emulator import LocalEmulator` |

| Import LocalSimulator | `from braket.devices import LocalSimulator` |

| Get emulator from AWS device | `emulator = device.emulator` |

| Create emulator from device properties | `emulator = LocalEmulator.from\_device\_properties(device.properties)` |

| Create emulator from device properties JSON | `emulator = LocalEmulator.from\_json(device\_properties\_json)` |

| Run a circuit on an emulator | `task = emulator.run(circuit, shots=100)` |

| Validate a circuit before running | `emulator.validate(circuit)` |

| Transform a circuit before running | `compiled\_circuit = emulator.transform(circuit)` |

| Generic local simulation | `task = LocalSimulator().run(circuit, shots=100)` |

| Note | Creating an emulator from an AWS device may require AWS credentials and a configured AWS region because device properties must be loaded. |

