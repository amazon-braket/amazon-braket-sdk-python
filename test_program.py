from braket.aws import AwsDevice, AwsSession
from braket.circuits import Circuit
from braket.devices import Devices

circ = Circuit().h(0)
dev = AwsDevice(Devices.IQM.Garnet)
print(dev)

session = AwsSession()
print(session.search_devices())

task = dev.run(circ, shots=5)
print(task.result)
