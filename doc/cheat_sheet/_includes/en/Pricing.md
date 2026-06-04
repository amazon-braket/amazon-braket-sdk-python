| Imports | `from braket.tracking import Tracker`<br>`from braket.tracking.pricing import Pricing` |
| Start the cost tracker | `tracker = Tracker().start()` |
| Get QPU task cost | `tracker.qpu_tasks_cost()` |
| Get simulator task cost | `tracker.simulator_tasks_cost()` |
| Get task statistics | `tracker.quantum_tasks_statistics()` |
| Search pricing data | `Pricing().price_search(**filters)` |