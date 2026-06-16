| Imports | `from braket.program_sets import ProgramSet, CircuitBinding`<br>`from braket.circuits.observables import X, Z` |
| Regrouper plusieurs circuits dans une tâche | `program_set = ProgramSet([circuit1, circuit2], shots_per_executable=100)` |
| Balayer un circuit sur des jeux de paramètres | `binding = CircuitBinding(circuit, input_sets=[{"theta": 0.1}, {"theta": 0.2}])` |
| Balayer sur un hamiltonien (observables) | `binding = CircuitBinding(circuit, {"theta": [0.1, 0.2]}, 2.1 * X(0) @ Z(1) - 4.5 * Z(0) @ Z(1))` |
| Construire un ensemble de programmes à partir de liaisons | `program_set = ProgramSet(binding)` |
| Associer circuits et entrées/observables | `ProgramSet.zip([circuit1, circuit2], observables=[X(0), Z(0)])` |
| Produit cartésien circuits × observables | `ProgramSet.product([circuit1], [X(0), Z(0)])` |
| Nombre total d'exécutables | `program_set.total_executables` |
| Exécuter un ensemble de programmes | `task = device.run(program_set, shots=1000)` |
| Espérance du i-ème exécutable | `task.result().expectation(0)` |
