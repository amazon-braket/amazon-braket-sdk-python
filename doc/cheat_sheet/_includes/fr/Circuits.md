|                                   |                                             |
| --------------------------------- | ------------------------------------------- |
| Create a circuit                  | `circuit = Circuit()`                       |
| Add gates                         | `circuit.x(0).cnot(0, 1)`                   |
| Apply a unitary matrix | `circuit.unitary(matrix, [0])` |
| Add a result type | `circuit.probability(0)` |
| Add a verbatim box | `circuit.add_verbatim_box(circuit2)` |
| Gate modifiers | `circuit.x(0, control=1, neg_control=2)` |
| Plot a circuit | `print(circuit)` |
| Observables | |
| Import from OpenQASM3 | `Circuit.from_ir(source)` |