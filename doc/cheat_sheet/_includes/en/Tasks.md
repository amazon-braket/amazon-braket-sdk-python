| Imports | `from braket.aws import AwsSession, AwsQuantumTask` |
| Create a quantum task by executing a circuit | `task = device.run(circuit)` |
| disable qubit rewiring|  `device.run(circuit, disable_qubit_rewiring=True)` |
| Instantiate an AwsSession|  `session = AwsSession(...)` |
| Recreate a quantum task|  `task = AwsQuantumTask(arn[, aws_session])` |
| Queue position|  `task.queue_position()` |
