| Task | Snippet |
|---|---|
| Imports | `from braket.program_sets import CircuitBinding, ProgramSet`<br>`from braket.circuits import Circuit, FreeParameter, observables` |
| Sweep one circuit | `theta = FreeParameter("theta")`<br>`circuit = Circuit().rx(0, theta)`<br>`binding = CircuitBinding(circuit, input_sets={"theta": [0.1, 0.2]})` |
| Create a program set | `program_set = ProgramSet(binding, shots_per_executable=100)` |
| Run a program set | `task = device.run(program_set)` |
| Mix circuits and bindings | `program_set = ProgramSet([Circuit().h(0), binding], shots_per_executable=100)` |
| Pair circuits, inputs, and observables | `ProgramSet.zip([circuit], input_sets=[{"theta": 0.1}], observables=[observables.Z(0)])` |
| Cartesian product with observables | `ProgramSet.product([circuit], observables=[observables.X(0), observables.Z(0)], shots_per_executable=100)` |
| Inspect size | `program_set.total_executables`<br>`program_set.total_shots` |
| Result lookup | `result = task.result()`<br>`first_entry = result[0][0]`<br>`first_entry.counts` |

Program sets run multiple executables in one quantum task. Do not attach regular circuit result types to circuits that are placed in a `ProgramSet`; use `CircuitBinding` observables when measuring observables.
