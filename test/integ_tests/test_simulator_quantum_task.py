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
from braket.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns
from braket.circuits import Circuit

SHOTS = 750


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_bell_pair(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    bell = Circuit().h(0).cnot(0, 1)
    result = device.run(bell, s3_destination_folder, shots=SHOTS).result()

    assert 0.40 < result.measurement_probabilities["00"] < 0.60
    assert 0.40 < result.measurement_probabilities["11"] < 0.60
    assert len(result.measurements) == SHOTS


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_qubit_ordering(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)

    # |110> should get back value of "110"
    state_110 = Circuit().x(0).x(1).i(2)
    result = device.run(state_110, s3_destination_folder, shots=SHOTS).result()
    assert result.measurement_counts.most_common(1)[0][0] == "110"

    # |001> should get back value of "001"
    state_001 = Circuit().i(0).i(1).x(2)
    result = device.run(state_001, s3_destination_folder, shots=SHOTS).result()
    assert result.measurement_counts.most_common(1)[0][0] == "001"
