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
from simulator_assert_utils import (
    assert_measurement_counts_most_common,
    assert_measurement_probabilities,
)

SHOTS = 750


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_bell_pair(simulator_arn, aws_session, s3_destination_folder, bell_state_and_tolerances):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result = device.run(bell_state_and_tolerances[0], s3_destination_folder, shots=SHOTS).result()
    assert_measurement_probabilities(result.measurement_probabilities, bell_state_and_tolerances[1])
    assert len(result.measurements) == SHOTS


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_qubit_ordering(
    simulator_arn,
    aws_session,
    s3_destination_folder,
    state_110_and_most_common,
    state_001_and_most_common,
):
    device = AwsQuantumSimulator(simulator_arn, aws_session)

    # |110> should get back value of "110"
    result = device.run(state_110_and_most_common[0], s3_destination_folder, shots=SHOTS).result()
    assert_measurement_counts_most_common(result.measurement_counts, state_110_and_most_common[1])

    # |001> should get back value of "001"
    result = device.run(state_001_and_most_common[0], s3_destination_folder, shots=SHOTS).result()
    assert_measurement_counts_most_common(result.measurement_counts, state_001_and_most_common[1])
