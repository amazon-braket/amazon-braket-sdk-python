import os

from braket.aws import AwsDevice
from braket.circuits import Circuit


def start_here():

    print("Test job started!!!!!")

    # Use the device declared in the Orchestration Script
    device = AwsDevice(os.environ["AMZN_BRAKET_DEVICE_ARN"])

    bell = Circuit().h(0).cnot(0, 1)
    for count in range(5):
        task = device.run(bell, shots=100)
        print(task.result().measurement_counts)

    print("Test job completed!!!!!")
