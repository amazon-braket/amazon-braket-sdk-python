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
#
# Notes 1: For a given input density matrix ρ, and error rate p, 
#          Depolarizing(p, ρ) = (1-4p/3)ρ + (4p/3)(I/2) where (I/2) is the one
#          qubit maximally mixed state. Then for a pure state ρ = |0><0|, or 
#          generally |ψ><ψ|, the input-output state fidelity reads 1-2p/3. 
#          Hence, for a "target one qubit gate average gate fidelity" q, 
#          which is the spec in the device property, the corresponing 
#          "target one qubit gate average error rate" is (1-q) * 3/2, not (1-q).
#
# Notes 2: For a given input density matrix ρ, and error rate p, 
#          TwoQubitDepolarizing(p, ρ) = (1-16p/15)ρ + (16p/15)(I/4) where (I/2) is 
#          the two qubit maximally mixed state. Then for a pure state ρ = |00><00|, 
#          or generally |ψ><ψ|, the input-output state fidelity reads 1-4p/5. 
#          Hence, for a "target two qubit gate average gate fidelity" q, 
#          which is the spec in the device property, the corresponing 
#          "target two qubit gate average error rate" is (1-q) * 5/4, not (1-q).

TARGET_F1Q = 0.99
TARGET_F2Q = 0.99

@pytest.fixture
def customized_emulator():
    """
    Fixture emulator with target one qubit and two qubit average gate fidelity
    """


    f1q = {'T1': {'standardError': None, 'unit': 'S', 'value': 2e-05},
     'T2': {'standardError': None, 'unit': 'S', 'value': 8e-06},
     'oneQubitFidelity': [{'fidelity': TARGET_F1Q,
                         'fidelityType': {'description': None,
                                          'name': 'RANDOMIZED_BENCHMARKING'},
                         'standardError': None},
                        {'fidelity': 1.0,
                        'fidelityType': {'description': None, 'name': 'READOUT'},
                        'standardError': None}]}
    f2q = {'twoQubitGateFidelity': [{'direction': None,
                           'fidelity': TARGET_F2Q,
                           'fidelityType': {'description': None,
                                            'name': 'RANDOMIZED_BENCHMARKING'},
                           'gateName': 'CZ',
                           'standardError': 0.0009},
                          ]}

    device_emu_propertis = DeviceEmulatorProperties(
        qubitCount = 2, 
        nativeGateSet = ["prx", "cz"],
        connectivityGraph = {},
        oneQubitProperties = {"0": OneQubitProperties.parse_obj(f1q),"1": OneQubitProperties.parse_obj(f1q)},
        twoQubitProperties = {"0-1": TwoQubitProperties.parse_obj(f2q)},
        supportedResultTypes = [
            ResultType.parse_obj(
                {"maxShots": 20000, "minShots": 1, "name": "Probability", "observables": None}
            )
        ]
    )

    return LocalEmulator.from_device_properties(device_emu_propertis)

def test_one_qubit_depolarizing_rate(customized_emulator):
    circ = Circuit().prx(0,0,0)
    circ = Circuit().add_verbatim_box(circ)
    num_samples = 1_000_000
    result = customized_emulator.run(circ, shots=num_samples).result().measurement_probabilities
    prob_0 = result['0']
    assert abs(TARGET_F1Q - prob_0) < 1/np.sqrt(num_samples)

def test_two_qubit_depolarizing_rate(customized_emulator):
    circ = Circuit().cz(0,1)
    circ = Circuit().add_verbatim_box(circ)
    num_samples = 1_000_000
    result = customized_emulator.run(circ, shots=num_samples).result().measurement_probabilities
    prob_00 = result['00']
    assert abs(TARGET_F1Q - prob_00) < 1/np.sqrt(num_samples)

