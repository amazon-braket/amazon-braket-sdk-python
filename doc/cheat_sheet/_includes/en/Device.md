| Task | Snippet |
|---|---|
| Imports | `from braket.aws import AwsDevice, AwsDeviceType`<br>`from braket.devices import Devices` |
| Managed simulator | `device = AwsDevice(Devices.Amazon.SV1)` |
| QPU alias | `device = AwsDevice(Devices.IonQ.Forte1)` |
| ARN string | `device = AwsDevice("arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1")` |
| Search devices | `AwsDevice.get_devices(types=[AwsDeviceType.QPU], statuses=["ONLINE"])` |
| Queue depth | `device.queue_depth()` |
| Device status | `device.status` |
| Device ARN | `device.arn` |
| QPU emulator | `emulator = device.emulator()` |
| Pulse frames and ports | `device.frames`<br>`device.ports` |
