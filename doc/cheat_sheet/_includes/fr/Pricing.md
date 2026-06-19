| Imports | `from braket.tracking import Tracker` |
| Démarrer le suivi des coûts | `tracker=Tracker().start()` |
| Afficher les coûts | `tracker.qpu_tasks_cost()`<br>`tracker.simulator_tasks_cost()` |
| Résumé des coûts | `tracker.quantum_tasks_statistics()` |
