import boto3
from braket.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns
from braket.circuits import Circuit

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]

device = AwsQuantumSimulator(AwsQuantumSimulatorArns.QS1)
s3_folder = (f"braket-output-{aws_account_id}", "folder-name")

# https://wikipedia.org/wiki/Bell_state
bell = Circuit().h(0).cnot(0, 1)
print(device.run(bell, s3_folder, shots=100).result().measurement_counts)
