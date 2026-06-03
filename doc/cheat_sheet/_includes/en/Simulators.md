| Task | Snippet |
|---|---|
| Imports | `from braket.devices import LocalSimulator`<br>`from braket.aws import AwsDevice`<br>`from braket.devices import Devices` |
| Local state-vector simulator | `device = LocalSimulator()` |
| Local density-matrix simulator | `device = LocalSimulator("braket_dm")` |
| Run locally | `result = device.run(circuit, shots=100).result()` |
| Exact local simulation | `result = device.run(circuit).result()` |
| Local batch | `batch = device.run_batch([circuit1, circuit2], shots=100)` |
| Installed local backends | `LocalSimulator.registered_backends()` |
| Managed state-vector simulator | `device = AwsDevice(Devices.Amazon.SV1)` |
| Managed density-matrix simulator | `device = AwsDevice(Devices.Amazon.DM1)` |
| Managed tensor-network simulator | `device = AwsDevice(Devices.Amazon.TN1)` |
