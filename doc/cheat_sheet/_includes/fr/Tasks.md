| Imports | `from braket.aws import AwsSession, AwsQuantumTask` |
| Créer une tâche quantique en exécutant un circuit | `task = device.run(circuit)` |
| Désactiver le recâblage des qubits | `device.run(circuit, disable_qubit_rewiring=True)` |
| Instancier une AwsSession | `session = AwsSession(...)` |
| Recréer une tâche quantique | `task = AwsQuantumTask(arn[, aws_session])` |
| Position dans la file | `task.queue_position()` |
