import logging
import sys

import boto3
from braket.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns
from braket.circuits import Circuit

logger = logging.getLogger("newLogger")  # create new logger
logger.addHandler(logging.StreamHandler(stream=sys.stdout))  # configure to print to sys.stdout
logger.setLevel(logging.DEBUG)  # print to sys.stdout all log messages with level DEBUG or above

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]

device = AwsQuantumSimulator(AwsQuantumSimulatorArns.QS1)
s3_folder = (f"braket-output-{aws_account_id}", "folder-name")

bell = Circuit().h(0).cnot(0, 1)
# pass in logger to device.run, enabling debugging logs to print to console
print(
    device.run(bell, s3_folder, poll_timeout_seconds=120, poll_interval_seconds=0.25, logger=logger)
    .result()
    .measurement_counts
)
