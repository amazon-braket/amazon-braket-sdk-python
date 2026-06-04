|                      |                                                       |
| -------------------- | ----------------------------------------------------- |
| Create a quantum task by executing a circuit|  `task = device.run(circuit)` |
| disable qubit rewiring|  `device.run(circuit, disable_qubit_rewiring=true)` |
| Instantiate an AwsSession|  `session = AwsSession...` |
| Recreate a quantum task|  `task = AwsQuantumTask(“arn:....”[, awssession=session])` |
| Queue position|  `task.queue_position()` |
