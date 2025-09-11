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

from braket.emulation.device_emulator_properties import (
    DeviceEmulatorProperties,
)

from braket.device_schema.iqm.iqm_device_capabilities_v1 import IqmDeviceCapabilities

from conftest import (
    valid_oneQubitProperties,
    valid_oneQubitProperties_v2,
    valid_twoQubitProperties,
    valid_supportedResultTypes,
    valid_nativeGateSet,
)


def test_basic_instantiation():
    result = DeviceEmulatorProperties(
        qubitCount=2,
        nativeGateSet=["cz", "prx"],
        connectivityGraph={"0": ["1"], "1": ["0"]},
        oneQubitProperties={"0": valid_oneQubitProperties, "1": valid_oneQubitProperties},
        twoQubitProperties={"0-1": valid_twoQubitProperties},
        supportedResultTypes=valid_supportedResultTypes,
    )
    assert result.qubit_count == 2
    assert result.native_gate_set == ["cz", "prx"]
    assert result.connectivity_graph == {"0": ["1"], "1": ["0"]}
    assert (
        result.one_qubit_properties["0"]
        == result.one_qubit_properties["1"]
        == valid_oneQubitProperties
    )
    assert result.two_qubit_properties["0-1"] == valid_twoQubitProperties
    assert result.supported_result_types == valid_supportedResultTypes
    assert result.qubit_labels == [0, 1]
    assert result.fully_connected == True
    assert result.directed == False


def test_from_json_3(reduced_standardized_json):
    result = DeviceEmulatorProperties.from_json(reduced_standardized_json)
    assert result.qubit_count == 2
    assert result.native_gate_set == valid_nativeGateSet
    assert result.connectivity_graph == {"0": ["1"]}
    assert (
        result.one_qubit_properties["0"] == valid_oneQubitProperties,
        result.one_qubit_properties["1"] == valid_oneQubitProperties_v2,
    )
    assert result.two_qubit_properties["0-1"] == valid_twoQubitProperties
    assert result.supported_result_types == valid_supportedResultTypes
    assert result.qubit_labels == [0, 1]
    assert result.fully_connected == True
    assert result.directed == True


def test_from_device_properties(reduced_standardized_json):
    device_properties = IqmDeviceCapabilities.parse_raw(reduced_standardized_json)
    result = DeviceEmulatorProperties.from_device_properties(device_properties)
    assert result.qubit_count == 2
    assert result.native_gate_set == valid_nativeGateSet
    assert result.connectivity_graph == {"0": ["1"]}
    assert (
        result.one_qubit_properties["0"] == valid_oneQubitProperties,
        result.one_qubit_properties["1"] == valid_oneQubitProperties_v2,
    )
    assert result.two_qubit_properties["0-1"] == valid_twoQubitProperties
    assert result.supported_result_types == valid_supportedResultTypes
    assert result.qubit_labels == [0, 1]


@pytest.mark.parametrize(
    "field, invalid_values",
    [
        ("paradigm.nativeGateSet", ["not_a_Braket_gate"]),
        ("paradigm.connectivity.connectivityGraph", {2: [0]}),
        ("paradigm.connectivity.connectivityGraph", {0: [2]}),
        ("standardized.oneQubitProperties", {"2": valid_oneQubitProperties}),
        ("standardized.oneQubitProperties", {"0": valid_oneQubitProperties}),
    ],
)
def test_invalid_device_emulator_properties(reduced_standardized_json, field, invalid_values):
    with pytest.raises(ValueError):
        minimal_invalid_json_dict = json.loads(reduced_standardized_json)

        # replace with invalid values
        field_split = field.split(".")
        pointer = minimal_invalid_json_dict
        for k in field_split[:-1]:
            pointer = pointer[k]
        pointer[field_split[-1]] = invalid_values

        minimal_invalid_json_dict[field] = invalid_values
        DeviceEmulatorProperties.from_json(json.dumps(minimal_invalid_json_dict))


@pytest.mark.parametrize(
    "invalid_device_properties",
    [
        (1),
        (valid_oneQubitProperties),
    ],
)
def test_invalid_instantiation_from_invalid_device_properties(invalid_device_properties):
    with pytest.raises(TypeError):
        DeviceEmulatorProperties.from_device_properties(invalid_device_properties)


@pytest.mark.parametrize(
    "missing_field",
    [
        ("standardized"),
        ("paradigm"),
        ("braket.ir.openqasm.program"),
    ],
)
def test_invalid_instantiation_due_to_missing_field(reduced_standardized_json, missing_field):
    minimal_valid_dict = json.loads(reduced_standardized_json)
    if missing_field == "braket.ir.openqasm.program":
        minimal_valid_dict["action"].pop(missing_field)
    else:
        minimal_valid_dict.pop(missing_field)
    with pytest.raises(ValueError):
        DeviceEmulatorProperties.from_json(json.dumps(minimal_valid_dict))


def test_from_json_non_fully_connected(reduced_standardized_json_2):
    result = DeviceEmulatorProperties.from_json(reduced_standardized_json_2)
    assert result.qubit_count == 3
    assert result.native_gate_set == ["rx", "rz", "iswap"]
    assert result.connectivity_graph == {"0": ["1"], "1": ["0", "2"], "2": ["1"]}
    assert (
        result.one_qubit_properties["2"]
        == result.one_qubit_properties["1"]
        == result.one_qubit_properties["0"]
        == valid_oneQubitProperties
    )
    assert (
        result.two_qubit_properties["0-1"]
        == result.two_qubit_properties["1-2"]
        == valid_twoQubitProperties
    )
    assert result.supported_result_types == valid_supportedResultTypes
    assert result.qubit_labels == [0, 1, 2]
    assert result.fully_connected == False
    assert result.directed == False


def test_from_json_non_fully_connected_but_directed(reduced_standardized_json_3):
    result = DeviceEmulatorProperties.from_json(reduced_standardized_json_3)
    assert result.qubit_count == 3
    assert result.native_gate_set == ["cz", "prx"]
    assert result.connectivity_graph == {"0": ["1"], "1": ["2"]}
    assert (
        result.one_qubit_properties["2"]
        == result.one_qubit_properties["1"]
        == result.one_qubit_properties["0"]
        == valid_oneQubitProperties
    )
    assert result.two_qubit_properties["0-1"] == valid_twoQubitProperties
    assert result.supported_result_types == valid_supportedResultTypes
    assert result.qubit_labels == [0, 1, 2]
    assert result.fully_connected == False
    assert result.directed == True
