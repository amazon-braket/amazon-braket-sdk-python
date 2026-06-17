| Imports | `from braket.ahs import AtomArrangement, DrivingField, AnalogHamiltonianSimulation` |
| Arrangement d'atomes | `register = AtomArrangement()` |
| Ajouter un atome par coordonnées (en mètres) | `register.add((5.7e-6, 5.7e-6))` |
| Obtenir les coordonnées | `register.coordinate_list(axis)` |
| Créer un champ d'excitation | `DrivingField(amplitude, phase, detuning)` |
| Créer un programme AHS | `ahs_program = AnalogHamiltonianSimulation(register, drive)` |
| Exécuter un programme AHS | `device.run(ahs_program)` |
