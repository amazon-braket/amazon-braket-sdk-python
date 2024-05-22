| Imports | `from braket.tracking import Tracker` |
| Start the cost tracker | `tracker=Tracker().start()` |
| Print costs | `tracker.qpu_tasks_cost()`<br>`tracker.simulator_tasks_cost()` |
| Cost summary | `tracker.quantum_tasks_statistics()` |