from braket.aws import AwsDevice

device = AwsDevice("arn:aws:braket::us-west-1:device/qpu/rigetti/Ankaa-2")
print(device)
