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

import pytest
from braket.aws import AwsQpu, AwsQpuArns, AwsQuantumSimulator, AwsQuantumSimulatorArns


@pytest.mark.parametrize(
    "qpu_arn,qpu_name", [(AwsQpuArns.RIGETTI, "Rigetti"), (AwsQpuArns.IONQ, "IonQ")]
)
def test_qpu_creation(qpu_arn, qpu_name, aws_session):
    qpu = AwsQpu(qpu_arn, aws_session=aws_session)
    assert qpu.arn == qpu_arn
    assert qpu.name == qpu_name


def test_device_across_regions(aws_session):
    # assert QPUs across different regions can be created using the same aws_session
    AwsQpu(AwsQpuArns.RIGETTI, aws_session)
    AwsQpu(AwsQpuArns.IONQ, aws_session)


@pytest.mark.parametrize(
    "simulator_arn,simulator_name", [(AwsQuantumSimulatorArns.QS1, "quantum-simulator-1")],
)
def test_simulator_creation(simulator_arn, simulator_name, aws_session):
    simulator = AwsQuantumSimulator(simulator_arn, aws_session=aws_session)
    assert simulator.arn == simulator_arn
    assert simulator.name == simulator_name
