# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
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

import pytest
from botocore.exceptions import ClientError

from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.aws.aws_quantum_job import AwsQuantumJob


@pytest.fixture
def qpu_arn():
    return "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"


def test_create_task_via_invalid_reservation_arn_on_qpu(qpu_arn):
    circuit = Circuit().h(0)
    device = AwsDevice(qpu_arn)

    with pytest.raises(ClientError, match="Reservation arn is invalid"):
        device.run(
            circuit,
            shots=10,
            reservation_arn="arn:aws:braket:us-west-2:872076371963:reservation/a1b123cd-45e6-789f-gh01-i234567jk8l9",
        )


def test_create_task_via_reservation_arn_on_simulator():
    device_arn = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
    circuit = Circuit().h(0)
    device = AwsDevice(device_arn)

    with pytest.raises(ClientError, match="Braket Direct is not supported for"):
        device.run(
            circuit,
            shots=10,
            reservation_arn="arn:aws:braket:us-west-2:872076371963:reservation/a1b123cd-45e6-789f-gh01-i234567jk8l9",
        )


def test_create_job_via_invalid_reservation_arn_on_qpu(aws_session, qpu_arn, capsys):
    with pytest.raises(ClientError, match="Reservation arn is invalid"):
        AwsQuantumJob.create(
            device=qpu_arn,
            source_module="test/integ_tests/job_test_script.py",
            entry_point="job_test_script:start_here",
            wait_until_complete=True,
            aws_session=aws_session,
            hyperparameters={"test_case": "completed"},
        )
