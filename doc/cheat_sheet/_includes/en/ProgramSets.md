| Task | Code |
|---|---|
| Import ProgramSet | `from braket.program_sets import ProgramSet` |
| Import CircuitBinding | `from braket.program_sets import CircuitBinding` |
| Import ParameterSets | `from braket.program_sets import ParameterSets` |
| Create parameter sets | `params = ParameterSets({"theta": [0.1, 0.2, 0.3]})` |
| Create circuit binding | `binding = CircuitBinding(circuit, input_sets=params)` |
| Create program set | `program_set = ProgramSet([circuit])` |
| Set shots per executable | `program_set = ProgramSet([circuit], shots_per_executable=100)` |
| Zip circuits with matching observables | `program_set = ProgramSet.zip(circuits=[circuit], observables=[observable])` |
| Create Cartesian product with observables | `program_set = ProgramSet.product(circuits=[circuit], observables=[observable], shots_per_executable=100)` |
| Run locally | `result = LocalSimulator().run(program_set, shots=100).result()` |
| Run on a device | `task = device.run(program_set, shots=100)` |
| Emulate a program set | `task = emulator.run(program_set, shots=100)` |
| Note | Circuits used in program sets cannot have result types attached. |
