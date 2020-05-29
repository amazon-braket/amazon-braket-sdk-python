import boto3
from braket.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns
from braket.aws import AwsQpu, AwsQpuArns
from braket.circuits import Circuit

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]

device = AwsQpu(AwsQpuArns.IONQ)
s3_folder = (f"braket-output-{aws_account_id}", "IONQ")

# https://wikipedia.org/wiki/Bell_state
bell = Circuit().h(0).cnot(0, 1)
task = device.run(bell, s3_folder, shots=1000, poll_timeout_seconds=86400)
print(task.result().measurement_counts)
