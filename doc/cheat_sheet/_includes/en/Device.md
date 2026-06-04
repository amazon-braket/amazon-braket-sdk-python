| Imports | `from braket.aws import AwsDevice`<br>`from braket.devices import Devices` |
| Instantiate a device | `device = AwsDevice("<deviceARN>")` |
| Device alias, use in place of string ARN | `Devices.Amazon.SV1` |
| Queue depth | `device.queue_depth()` |
| Gate pulse implementation, if available | `device.gate_calibrations` |