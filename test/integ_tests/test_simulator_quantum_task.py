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
from gate_model_device_testing_utils import (
    no_result_types_bell_pair_testing,
    qubit_ordering_testing,
    result_types_all_selected_testing,
    result_types_bell_pair_full_probability_testing,
    result_types_bell_pair_marginal_probability_testing,
    result_types_hermitian_testing,
    result_types_nonzero_shots_bell_pair_testing,
    result_types_tensor_hermitian_hermitian_testing,
    result_types_tensor_x_y_testing,
    result_types_tensor_y_hermitian_testing,
    result_types_tensor_z_h_y_testing,
    result_types_tensor_z_hermitian_testing,
    result_types_tensor_z_z_testing,
)

from braket.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns

SHOTS = 8000


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_no_result_types_bell_pair(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    no_result_types_bell_pair_testing(
        device, {"shots": SHOTS, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_qubit_ordering(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    qubit_ordering_testing(device, {"shots": SHOTS, "s3_destination_folder": s3_destination_folder})


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_result_types_nonzero_shots_bell_pair(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_nonzero_shots_bell_pair_testing(
        device, {"shots": SHOTS, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_result_types_bell_pair_full_probability(simulator_arn, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_bell_pair_full_probability_testing(
        device, {"shots": SHOTS, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn", [AwsQuantumSimulatorArns.QS1])
def test_result_types_bell_pair_marginal_probability(
    simulator_arn, aws_session, s3_destination_folder
):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_bell_pair_marginal_probability_testing(
        device, {"shots": SHOTS, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_tensor_x_y(simulator_arn, shots, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_tensor_x_y_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_tensor_z_h_y(simulator_arn, shots, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_tensor_z_h_y_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_hermitian(simulator_arn, shots, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_hermitian_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_tensor_z_z(simulator_arn, shots, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_tensor_z_z_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_tensor_hermitian_hermitian(
    simulator_arn, shots, aws_session, s3_destination_folder
):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_tensor_hermitian_hermitian_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_tensor_y_hermitian(simulator_arn, shots, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_tensor_y_hermitian_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_tensor_z_hermitian(simulator_arn, shots, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_tensor_z_hermitian_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )


@pytest.mark.parametrize("simulator_arn,shots", [(AwsQuantumSimulatorArns.QS1, SHOTS)])
def test_result_types_all_selected(simulator_arn, shots, aws_session, s3_destination_folder):
    device = AwsQuantumSimulator(simulator_arn, aws_session)
    result_types_all_selected_testing(
        device, {"shots": shots, "s3_destination_folder": s3_destination_folder}
    )
