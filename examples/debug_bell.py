# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

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
logger.info(
    device.run(
        bell,
        s3_folder,
        shots=100,
        poll_timeout_seconds=120,
        poll_interval_seconds=0.25,
        logger=logger,
    )
    .result()
    .measurement_counts
)
