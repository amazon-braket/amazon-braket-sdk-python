import numpy as np
from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.devices import Devices
from braket.emulation.emulation_context import EmulationContext

EmulationContext.start()

circ = Circuit().rx(0, 0.5).rz(1, 0.5).rz(2, 0.5).rx(0, np.pi).rx(1, np.pi).rx(2, np.pi).cz(0, 1)

device_arns = [Devices.Amazon.SV1, Devices.Rigetti.AspenM3, Devices.OQC.Lucy, Devices.IonQ.Aria1]

for device_arn in device_arns:
    device = AwsDevice(device_arn)

    is_emulating = "with" if EmulationContext.is_emulation_enabled() else "without"
    print(f"Running on {device_arn} {is_emulating} emulation.")
    task = device.run(circ, shots=100000)
    print(task.result().measurement_probabilities)
