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
