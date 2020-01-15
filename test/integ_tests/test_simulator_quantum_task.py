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
import math

import pytest
from braket.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns
from braket.circuits import Circuit


@pytest.mark.parametrize(
    "simulator_arn", [AwsQuantumSimulatorArns.QS1, AwsQuantumSimulatorArns.QS3]
)
def test_bell_pair(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    bell = Circuit().h(0).cnot(0, 1)
    result = device.run(bell, s3_destination_folder, shots=750).result()

    assert 0.40 < result.measurement_probabilities["00"] < 0.60
    assert 0.40 < result.measurement_probabilities["11"] < 0.60
    assert len(result.measurements) == 750


@pytest.mark.parametrize(
    "simulator_arn",
    [  # TODO Uncomment out below once proper ordering fix has been applied to QS1
        AwsQuantumSimulatorArns.QS1,
        AwsQuantumSimulatorArns.QS3,
    ],
)
def test_qubit_ordering(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)

    # |110> should get back value of "110"
    state_110 = Circuit().x(0).x(1).i(2)
    result = device.run(state_110, s3_destination_folder).result()
    assert result.measurement_counts.most_common(1)[0][0] == "110"

    # |001> should get back value of "001"
    state_001 = Circuit().i(0).i(1).x(2)
    result = device.run(state_001, s3_destination_folder).result()
    assert result.measurement_counts.most_common(1)[0][0] == "001"


def test_state_vector(aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(AwsQuantumSimulatorArns.QS3, aws_session)
    bell = Circuit().h(0).cnot(0, 1)
    state_vector = device.run(bell, s3_destination_folder, shots=1).result().state_vector
    assert state_vector["00"] == complex(1 / math.sqrt(2), 0)
    assert state_vector["01"] == 0
    assert state_vector["10"] == 0
    assert state_vector["11"] == complex(1 / math.sqrt(2), 0)


def test_qs2_quantum_task(aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(AwsQuantumSimulatorArns.QS2, aws_session)

    bell = Circuit().h(range(8))
    measurements = device.run(bell, s3_destination_folder, shots=1).result().measurements

    # 1 shot
    assert len(measurements) == 1

    # 8 qubits
    assert len(measurements[0]) == 8
