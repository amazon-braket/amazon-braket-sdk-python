| Imports | `from braket.circuits import Circuit, Gate, Instruction`<br>`from braket.circuits.observables import X` |
| Créer un circuit | `circuit = Circuit()`|
| Ajouter des portes | `circuit.x(0).rx(1, 1.23).cnot(0, 1)` |
| Lister les portes disponibles | `[attr for attr in dir(Gate) if attr[0].isupper()]` |
| Appliquer une matrice unitaire | `circuit.unitary([0], matrix)` |
| Obtenir l'unitaire du circuit | `circuit.to_unitary()` |
| Ajouter un type de résultat | `circuit.probability(0)`<br>`circuit.expectation(0.5 * X() @ X(), target=[0, 1])` |
| Types de résultats disponibles | adjoint_gradient, amplitude, density_matrix, expectation, probability, sample, state_vector, variance |
| Ajouter une boîte verbatim | `circuit.add_verbatim_box(circuit2)` |
| Modificateurs de portes | `circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)` |
| Dessiner un circuit | `print(circuit)` |
| Importer depuis OpenQASM3 | `Circuit.from_ir(source=qasm_str)` |
| Exporter vers OpenQASM3 | `Circuit.to_ir("OPENQASM")` |
| Créer une instruction | `inst = Instruction(Gate.CPhaseShift(1.23), target=[0, 1])` |
| Ajouter une instruction | `circuit.add(inst)` |
