| Task | Code |

|---|---|

| Import ProgramSet | `from braket.program\_sets import ProgramSet` |

| Import CircuitBinding | `from braket.program\_sets import CircuitBinding` |

| Import ParameterSets | `from braket.program\_sets import ParameterSets` |

| Create parameter sets | `params = ParameterSets({"theta": \[0.1, 0.2, 0.3]})` |

| Create circuit binding | `binding = CircuitBinding(circuit, input\_sets=params)` |

| Create program set | `program\_set = ProgramSet(\[circuit])` |

| Set shots per executable | `program\_set = ProgramSet(\[circuit], shots\_per\_executable=100)` |

| Zip circuits with matching observables | `program\_set = ProgramSet.zip(circuits=\[circuit], observables=\[observable])` |

| Create Cartesian product with observables | `program\_set = ProgramSet.product(circuits=\[circuit], observables=\[observable], shots\_per\_executable=100)` |

| Run locally | `result = LocalSimulator().run(program\_set, shots=100).result()` |

| Run on a device | `task = device.run(program\_set, shots=100)` |

| Emulate a program set | `task = emulator.run(program\_set, shots=100)` |

| Note | Circuits used in program sets cannot have result types attached. |

