| Imports | `from braket.aws import AwsDevice`<br>`from braket.devices import Devices` |
|  Instantiate a device | `AwsDevice("<deviceARN>")` |
|  Device alias (use in place of string ARN) | `Devices.Rigetti.AspenM3` |
|  Queue depth | `device.queue_depth()` |
|  Gate pulse implementation | `device.gate_calibrations` |
