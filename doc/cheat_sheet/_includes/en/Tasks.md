| Task | Snippet |
|---|---|
| Imports | `from braket.aws import AwsQuantumTask, AwsSession` |
| Create a quantum task | `task = device.run(circuit, shots=100)` |
| Run a batch | `batch = device.run_batch([circuit1, circuit2], shots=100)` |
| Disable qubit rewiring | `task = device.run(circuit, shots=100, disable_qubit_rewiring=True)` |
| Set task tags | `task = device.run(circuit, shots=100, tags={"project": "demo"})` |
| Poll with a custom timeout | `task = device.run(circuit, shots=100, poll_timeout_seconds=86400)` |
| Recreate a task from ARN | `task = AwsQuantumTask(arn, aws_session=AwsSession())` |
| Inspect queue position | `task.queue_position()` |
| Inspect state and metadata | `task.state()`<br>`task.metadata()` |
| Cancel a task | `task.cancel()` |
