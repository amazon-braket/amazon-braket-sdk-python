| Task | Snippet |
|---|---|
| Imports | `from braket.circuits import Circuit, Gate, Instruction, observables` |
| Create a circuit | `circuit = Circuit()` |
| Add gates | `circuit.h(0).rx(1, 1.23).cnot(0, 1)` |
| Build an instruction | `inst = Instruction(Gate.CPhaseShift(1.23), target=[0, 1])`<br>`circuit.add(inst)` |
| Apply a unitary matrix | `circuit.unitary(matrix, targets=[0])` |
| Gate modifiers | `circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)` |
| Add result types | `circuit.probability(target=[0])`<br>`circuit.expectation(observable=observables.X(0) @ observables.X(1))` |
| Exact-state result types | `amplitude`, `density_matrix`, `probability`, `state_vector` |
| Sampled result types | `expectation`, `probability`, `sample`, `variance` |
| Draw a circuit | `print(circuit)` |
| Export to OpenQASM 3 | `circuit.to_ir("OPENQASM")` |
| Import from OpenQASM 3 | `Circuit.from_ir(source=qasm_source)` |
| Add a verbatim box | `circuit.add_verbatim_box(native_circuit)` |
