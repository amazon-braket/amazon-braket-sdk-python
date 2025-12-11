# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import json

from braket.device_schema.iqm.iqm_device_capabilities_v1 import IqmDeviceCapabilities
from braket.device_schema.ionq.ionq_device_capabilities_v1 import IonqDeviceCapabilities
from braket.device_schema.rigetti.rigetti_device_capabilities_v1 import RigettiDeviceCapabilities

from braket.emulation.local_emulator import LocalEmulator

from braket.program_sets import ProgramSet
from braket.circuits import Circuit

from conftest import invalid_device_properties_dict_1, invalid_device_properties_dict_2

from braket.emulation.device_emulator_properties import DeviceEmulatorProperties

from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    OneQubitProperties,
    TwoQubitProperties,
)

from braket.device_schema.result_type import ResultType

import numpy as np


def test_from_json_3(reduced_standardized_json):
    emulator = LocalEmulator.from_json(reduced_standardized_json)
    assert isinstance(emulator, LocalEmulator)


def test_from_device_properties(reduced_standardized_json):
    device_properties = IqmDeviceCapabilities.parse_raw(reduced_standardized_json)
    emulator = LocalEmulator.from_device_properties(device_properties)
    assert isinstance(emulator, LocalEmulator)


def test_from_device_properties_non_fully_connected(reduced_standardized_json_2):
    device_properties = RigettiDeviceCapabilities.parse_raw(reduced_standardized_json_2)
    emulator = LocalEmulator.from_device_properties(device_properties)
    assert isinstance(emulator, LocalEmulator)


def test_from_device_properties_non_fully_connected_but_directed(reduced_standardized_json_3):
    device_properties = IqmDeviceCapabilities.parse_raw(reduced_standardized_json_3)
    emulator = LocalEmulator.from_device_properties(device_properties)
    assert isinstance(emulator, LocalEmulator)


def test_invalid_instantiation_2(reduced_standardized_json):
    with pytest.raises(TypeError):
        LocalEmulator.from_device_properties(reduced_standardized_json)


@pytest.mark.parametrize(
    "invalid_device_properties_dict",
    [
        (invalid_device_properties_dict_1),
        (invalid_device_properties_dict_2),
    ],
)
def test_noise_model_with_invalid_data(invalid_device_properties_dict):
    with pytest.raises(ValueError):
        LocalEmulator.from_json(json.dumps(invalid_device_properties_dict))


def test_validate_valid_verbatim_circ_garnet(
    reduced_standardized_json_3, valid_verbatim_circ_garnet
):
    emulator = LocalEmulator.from_json(reduced_standardized_json_3)
    emulator.validate(valid_verbatim_circ_garnet)


def test_validate_valid_verbatim_circ_ankaa3(
    reduced_standardized_json_2, valid_verbatim_circ_ankaa3
):
    emulator = LocalEmulator.from_json(reduced_standardized_json_2)
    emulator.validate(valid_verbatim_circ_ankaa3)


def test_validate_valid_verbatim_circ_aria_1(
    reduced_ionq_device_capabilities_json, valid_verbatim_circ_aria1
):
    emulator = LocalEmulator.from_json(reduced_ionq_device_capabilities_json)
    emulator.validate(valid_verbatim_circ_aria1)


def test_validate_valid_verbatim_circ_aria_1_v2(
    reduced_ionq_device_capabilities_json, valid_verbatim_circ_aria1
):
    emulator = LocalEmulator.from_device_properties(
        IonqDeviceCapabilities.parse_raw(reduced_ionq_device_capabilities_json)
    )
    emulator.validate(valid_verbatim_circ_aria1)


def test_program_set(reduced_standardized_json):
    emulator = LocalEmulator.from_json(reduced_standardized_json)
    ps = ProgramSet([Circuit()], shots_per_executable=50)
    with pytest.raises(TypeError):
        emulator.run(ps)


# Below we test the one qubit and two qubit depolarizing rates are set correctly.

NUM_SHOTS = 1_000_000
NUM_SIGMA = 3
TARGET_F1Q = 1 - 2 * NUM_SIGMA * 3 / np.sqrt(NUM_SHOTS)
TARGET_F2Q = 1 - 2 * NUM_SIGMA * 5 / np.sqrt(NUM_SHOTS)

# Notes for the chosen TARGET_F1Q:
# For a "target one qubit gate average gate fidelity" q, suppose, suppose
# we mistakenly set the "target one qubit gate average gate error" as (1-q),
# then we obtain the input-output state fidelity as 1-2/3 * (1-q) = 2q/3+1/3,
# which is different from the target fidelity q. In order to distinguish these
# two values, while making sure that the estimated fidelity is close to the
# target fidelity 99.73% of the time [3 sigma], we want |q - (2q+3+1/3)| = |1-q|/3
# to be large enough, or |1-q|/3 = 2 * (3 * 1/np.sqrt(NUM_SHOTS)). In other words,
# we set the difference between the errant and correct estimate to be at least 6 sigma,
# 3 sigma centered around each estimated value.
#
# Notes for the chosen TARGET_F2Q:
# For a "target two qubit gate average gate fidelity" q, suppose, suppose
# we mistakenly set the "target two qubit gate average gate error" as (1-q),
# then we obtain the input-output state fidelity as 1-4/5 * (1-q) = 4q/5+1/5,
# which is different from the target fidelity q. Using the same argument as above, we
# set |q - (4q/5+1/5)| = |1-q|/5 = 2 * (3 * 1/np.sqrt(NUM_SHOTS)).


@pytest.fixture
def customized_emulator():
    """
    Fixture emulator with target one qubit and two qubit average gate fidelity
    """

    f1q = {
        "T1": {"standardError": None, "unit": "S", "value": 2e-05},
        "T2": {"standardError": None, "unit": "S", "value": 8e-06},
        "oneQubitFidelity": [
            {
                "fidelity": TARGET_F1Q,
                "fidelityType": {"description": None, "name": "RANDOMIZED_BENCHMARKING"},
                "standardError": None,
            },
            {
                "fidelity": 1.0,
                "fidelityType": {"description": None, "name": "READOUT"},
                "standardError": None,
            },
        ],
    }
    f2q = {
        "twoQubitGateFidelity": [
            {
                "direction": None,
                "fidelity": TARGET_F2Q,
                "fidelityType": {"description": None, "name": "RANDOMIZED_BENCHMARKING"},
                "gateName": "CZ",
                "standardError": 0.0009,
            },
        ]
    }

    device_emu_propertis = DeviceEmulatorProperties(
        qubitCount=2,
        nativeGateSet=["prx", "cz"],
        connectivityGraph={},
        oneQubitProperties={
            "0": OneQubitProperties.parse_obj(f1q),
            "1": OneQubitProperties.parse_obj(f1q),
        },
        twoQubitProperties={"0-1": TwoQubitProperties.parse_obj(f2q)},
        supportedResultTypes=[
            ResultType.parse_obj({
                "maxShots": 20000,
                "minShots": 1,
                "name": "Probability",
                "observables": None,
            })
        ],
    )

    return LocalEmulator.from_device_properties(device_emu_propertis)


def test_one_qubit_depolarizing_rate(customized_emulator):
    circ = Circuit().prx(0, 0, 0)
    circ = Circuit().add_verbatim_box(circ)
    num_samples = NUM_SHOTS
    result = customized_emulator.run(circ, shots=num_samples).result().measurement_probabilities
    prob_0 = result["0"]
    assert abs(TARGET_F1Q - prob_0) < NUM_SIGMA / np.sqrt(num_samples)
    # If this unit test failed, it could be statistical fluctuation [with 1/370 probability],
    # please retry again.


def test_two_qubit_depolarizing_rate(customized_emulator):
    circ = Circuit().cz(0, 1)
    circ = Circuit().add_verbatim_box(circ)
    num_samples = NUM_SHOTS
    result = customized_emulator.run(circ, shots=num_samples).result().measurement_probabilities
    prob_00 = result["00"]
    assert abs(TARGET_F2Q - prob_00) < NUM_SIGMA / np.sqrt(num_samples)
    # If this unit test failed, it could be statistical fluctuation [with 1/370 probability],
    # please retry again.
