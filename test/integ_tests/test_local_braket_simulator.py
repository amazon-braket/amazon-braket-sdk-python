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
from gate_model_device_testing_utils import (
    multithreaded_bell_pair_testing,
    no_result_types_bell_pair_testing,
    qubit_ordering_testing,
    result_types_all_selected_testing,
    result_types_bell_pair_full_probability_testing,
    result_types_bell_pair_marginal_probability_testing,
    result_types_hermitian_testing,
    result_types_noncommuting_all,
    result_types_noncommuting_flipped_targets_testing,
    result_types_noncommuting_testing,
    result_types_nonzero_shots_bell_pair_testing,
    result_types_observable_not_in_instructions,
    result_types_tensor_hermitian_hermitian_testing,
    result_types_tensor_x_y_testing,
    result_types_tensor_y_hermitian_testing,
    result_types_tensor_z_h_y_testing,
    result_types_tensor_z_hermitian_testing,
    result_types_tensor_z_z_testing,
    result_types_zero_shots_bell_pair_testing,
)

from braket.devices import LocalSimulator

DEVICE = LocalSimulator()
SHOTS = 8000


def test_multithreaded_bell_pair(caplog):
    multithreaded_bell_pair_testing(DEVICE, {"shots": SHOTS})
    assert not caplog.text


def test_no_result_types_bell_pair(caplog):
    no_result_types_bell_pair_testing(DEVICE, {"shots": SHOTS})
    assert not caplog.text


def test_qubit_ordering(caplog):
    qubit_ordering_testing(DEVICE, {"shots": SHOTS})
    assert not caplog.text


def test_result_types_no_shots(caplog):
    result_types_zero_shots_bell_pair_testing(DEVICE, True, {"shots": 0})
    assert not caplog.text


def test_result_types_nonzero_shots_bell_pair(caplog):
    result_types_nonzero_shots_bell_pair_testing(DEVICE, {"shots": SHOTS})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_bell_pair_full_probability(shots, caplog):
    result_types_bell_pair_full_probability_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_bell_pair_marginal_probability(shots, caplog):
    result_types_bell_pair_marginal_probability_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_hermitian(shots, caplog):
    result_types_hermitian_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_tensor_x_y(shots, caplog):
    result_types_tensor_x_y_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_tensor_z_z(shots, caplog):
    result_types_tensor_z_z_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_tensor_z_h_y(shots, caplog):
    result_types_tensor_z_h_y_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_tensor_z_hermitian(shots, caplog):
    result_types_tensor_z_hermitian_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_tensor_hermitian_hermitian(shots, caplog):
    result_types_tensor_hermitian_hermitian_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_tensor_y_hermitian(shots, caplog):
    result_types_tensor_y_hermitian_testing(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_all_selected(shots, caplog):
    result_types_all_selected_testing(DEVICE, {"shots": shots})
    assert not caplog.text


def test_result_types_noncommuting(caplog):
    result_types_noncommuting_testing(DEVICE, {})
    assert not caplog.text


def test_result_types_noncommuting_flipped_targets(caplog):
    result_types_noncommuting_flipped_targets_testing(DEVICE, {})
    assert not caplog.text


def test_result_types_noncommuting_all(caplog):
    result_types_noncommuting_all(DEVICE, {})
    assert not caplog.text


@pytest.mark.parametrize("shots", [0, SHOTS])
def test_result_types_observable_not_in_instructions(shots, caplog):
    result_types_observable_not_in_instructions(DEVICE, {"shots": shots})
    assert not caplog.text


@pytest.mark.parametrize(
    "backend, device_name",
    [
        ("default", "StateVectorSimulator"),
        ("braket_sv", "StateVectorSimulator"),
        ("braket_dm", "DensityMatrixSimulator"),
        ("braket_ahs", "RydbergAtomSimulator"),
    ],
)
def test_local_simulator_device_names(backend, device_name, caplog):
    local_simulator_device = LocalSimulator(backend)
    assert local_simulator_device.name == device_name
    assert not caplog.text
