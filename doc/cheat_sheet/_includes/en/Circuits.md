| Imports | `from braket.circuits import Circuit, Gate, Instruction`<br>`from braket.circuits.observables import X` |
| Create a circuit                  | `circuit = Circuit()`                       |
| Add gates                         | `circuit.x(0).rx(1, 1.23).cnot(0, 1)` |
| Get the list of available gates | `[attr for attr in dir(Gate) if attr[0].isupper()]` |
| Apply a unitary matrix | `circuit.unitary(matrix, [0])` |
| Get the circuit unitary | `circuit.to_unitary()` |
| Add a result type | `circuit.probability(0)`<br>`circuit.expectation(0.5 * X() @ X(), target=[0, 1])` |
| List of the available result types | adjoint_gradient, amplitude, density_matrix, expectation, probability, sample, state_vector, variance |
| Add a verbatim box | `circuit.add_verbatim_box(circuit2)` |
| Gate modifiers | `circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)` |
| Draw a circuit | `print(circuit)` |
| Import from OpenQASM3 | `Circuit.from_ir(source=qasm_str)` |
| Export to OpenQASM3 | `Circuit.to_ir("OPENQASM")` |
| Create an instruction | `inst = Instruction(Gate.CPhaseShift(1.23), target=[0, 1])` |
| Add an instruction | `circuit.add(inst)` |