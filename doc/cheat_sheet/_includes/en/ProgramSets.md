| Imports | `from braket.program_sets import ProgramSet, CircuitBinding` |
| Create a CircuitBinding | `binding = CircuitBinding(circuit)` |
| With parameter sets | `binding = CircuitBinding(circuit, input_sets=[{"theta": 0.1}, {"theta": 0.2}])` |
| With observables | `binding = CircuitBinding(circuit, observables=X() @ X())` |
| Combine into a ProgramSet | `program_set = ProgramSet([binding], shots_per_executable=100)` |
| Run a ProgramSet | `result = device.run(program_set)` |
