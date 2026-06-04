| Imports | `from braket.aws import AwsSession, AwsQuantumTask` |
| Create a quantum task by executing a circuit | `task = device.run(circuit)` |
| Disable qubit rewiring|  `device.run(circuit, disable_qubit_rewiring=True)` |
| Instantiate an AwsSession|  `session = AwsSession(...)` |
| Recreate a quantum task | `task = AwsQuantumTask(arn, aws_session=session)` |
| Queue position|  `task.queue_position()` |
| Get task ID | `task.id` |
| Get task state | `task.state()` |
| Get task result | `result = task.result()` |
| Get task metadata | `task.metadata()` |
| Cancel a task | `task.cancel()` |
