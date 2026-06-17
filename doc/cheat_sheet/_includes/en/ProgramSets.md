| Imports | `from braket.program_sets import ProgramSet, CircuitBinding`<br>`from braket.circuits.observables import X, Z` |
| Bundle several circuits in one task<!-- LLM: . Circuits inside a program set cannot have result types attached--> | `program_set = ProgramSet([circuit1, circuit2], shots_per_executable=100)` |
| Sweep one circuit over parameter sets | `binding = CircuitBinding(circuit, input_sets=[{"theta": 0.1}, {"theta": 0.2}])` |
| Sweep over a Hamiltonian (observables) | `binding = CircuitBinding(circuit, {"theta": [0.1, 0.2]}, 2.1 * X(0) @ Z(1) - 4.5 * Z(0) @ Z(1))` |
| Build a program set from bindings | `program_set = ProgramSet(binding)` |
| Pair circuits with inputs/observables | `ProgramSet.zip([circuit1, circuit2], observables=[X(0), Z(0)])` |
| Cartesian product of circuits × observables | `ProgramSet.product([circuit1], [X(0), Z(0)])` |
| Total number of executables | `program_set.total_executables` |
| Run a program set | `task = device.run(program_set, shots=1000)` |
| Expectation value of the i-th executable | `task.result().expectation(0)` |
