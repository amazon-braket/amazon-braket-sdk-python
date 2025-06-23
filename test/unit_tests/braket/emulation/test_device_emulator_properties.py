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
from pydantic.v1 import ValidationError

from braket.emulation.device_emulator_properties import (
    DeviceEmulatorProperties,
)
from braket.device_schema.result_type import ResultType
from braket.device_schema.error_mitigation.debias import Debias
from braket.device_schema.error_mitigation.error_mitigation_properties import (
    ErrorMitigationProperties,
)
from braket.device_schema.iqm.iqm_device_capabilities_v1 import IqmDeviceCapabilities

from braket.emulation.device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES

from conftest import (
    valid_oneQubitProperties,
    valid_oneQubitProperties_v2,
    valid_twoQubitProperties,
    valid_supportedResultTypes,
    valid_connectivityGraph,
    valid_nativeGateSet,
)


def test_basic_instantiation():
    result = DeviceEmulatorProperties(
        qubitCount=2,
        nativeGateSet=["cz", "prx"],
        connectivityGraph={"0": ["1"], "1": ["0"]},
        oneQubitProperties={"0": valid_oneQubitProperties, "1": valid_oneQubitProperties},
        twoQubitProperties={"0-1": valid_twoQubitProperties},
    )
    assert result.qubitCount == 2
    assert result.nativeGateSet == ["cz", "prx"]
    assert result.connectivityGraph == {"0": ["1"], "1": ["0"]}
    assert (
        result.oneQubitProperties["0"] == result.oneQubitProperties["1"] == valid_oneQubitProperties
    )
    assert result.twoQubitProperties["0-1"] == valid_twoQubitProperties
    assert result.supportedResultTypes == DEFAULT_SUPPORTED_RESULT_TYPES
    assert result.errorMitigation == {}
    assert result.qubit_labels == [0, 1]
    assert result.fully_connected == True
    assert result.directed == False


def test_basic_instantiation_with_errorMitigation():
    result = DeviceEmulatorProperties(
        qubitCount=2,
        nativeGateSet=["cz", "prx"],
        connectivityGraph={"0": ["1"], "1": ["0"]},
        oneQubitProperties={"0": valid_oneQubitProperties, "1": valid_oneQubitProperties},
        twoQubitProperties={"0-1": valid_twoQubitProperties},
        errorMitigation={Debias: ErrorMitigationProperties(minimumShots=2500)},
    )
    assert result.qubitCount == 2
    assert result.nativeGateSet == ["cz", "prx"]
    assert result.connectivityGraph == {"0": ["1"], "1": ["0"]}
    assert (
        result.oneQubitProperties["0"] == result.oneQubitProperties["1"] == valid_oneQubitProperties
    )
    assert result.twoQubitProperties["0-1"] == valid_twoQubitProperties
    assert result.supportedResultTypes == DEFAULT_SUPPORTED_RESULT_TYPES
    assert result.errorMitigation == {Debias: ErrorMitigationProperties(minimumShots=2500)}
    assert result.qubit_labels == [0, 1]
    assert result.fully_connected == True
    assert result.directed == False


def test_from_json_1(minimal_valid_json):
    result = DeviceEmulatorProperties._from_json(minimal_valid_json)
    assert result.qubitCount == 2
    assert result.nativeGateSet == valid_nativeGateSet
    assert result.connectivityGraph == {}
    assert result.oneQubitProperties["0"] == valid_oneQubitProperties
    assert result.oneQubitProperties["1"] == valid_oneQubitProperties_v2
    assert result.twoQubitProperties["0-1"] == valid_twoQubitProperties
    assert result.supportedResultTypes == valid_supportedResultTypes
    assert result.errorMitigation == {}
    assert result.qubit_labels == [0, 1]
    assert result.fully_connected == True
    assert result.directed == False


def test_from_json_2(minimal_valid_json_with_errorMitigation):
    result = DeviceEmulatorProperties._from_json(minimal_valid_json_with_errorMitigation)
    assert result.qubitCount == 2
    assert result.nativeGateSet == valid_nativeGateSet
    assert result.connectivityGraph == {}
    assert result.oneQubitProperties["0"] == valid_oneQubitProperties
    assert result.oneQubitProperties["1"] == valid_oneQubitProperties_v2
    assert result.twoQubitProperties["0-1"] == valid_twoQubitProperties
    assert result.supportedResultTypes == valid_supportedResultTypes
    assert result.errorMitigation == {Debias: ErrorMitigationProperties(minimumShots=2500)}
    assert result.qubit_labels == [0, 1]
    assert result.fully_connected == True
    assert result.directed == False


def test_from_json_3(reduced_standardized_json):
    result = DeviceEmulatorProperties._from_json(reduced_standardized_json)
    assert result.qubitCount == 2
    assert result.nativeGateSet == valid_nativeGateSet
    assert result.connectivityGraph == {"0": ["1"]}
    assert (
        result.oneQubitProperties["1"] == result.oneQubitProperties["0"] == valid_oneQubitProperties
    )
    assert result.twoQubitProperties["0-1"] == valid_twoQubitProperties
    assert result.supportedResultTypes == valid_supportedResultTypes
    assert result.errorMitigation == {}
    assert result.qubit_labels == [0, 1]
    assert result.fully_connected == True
    assert result.directed == True


def test_from_device_properties(reduced_standardized_json):
    device_properties = IqmDeviceCapabilities.parse_raw(reduced_standardized_json)
    result = DeviceEmulatorProperties.from_device_properties(device_properties)
    assert result.qubitCount == 2
    assert result.nativeGateSet == valid_nativeGateSet
    assert result.connectivityGraph == {"0": ["1"]}
    assert (
        result.oneQubitProperties["1"] == result.oneQubitProperties["0"] == valid_oneQubitProperties
    )
    assert result.twoQubitProperties["0-1"] == valid_twoQubitProperties
    assert result.supportedResultTypes == valid_supportedResultTypes
    assert result.errorMitigation == {}
    assert result.qubit_labels == [0, 1]


def test_yet_another_way_of_instantiation(valid_input):
    result = DeviceEmulatorProperties.parse_obj(valid_input)
    assert result.qubitCount == 2
    assert result.connectivityGraph == valid_connectivityGraph
    assert result.qubit_labels == [0, 1]


@pytest.mark.parametrize(
    "field, invalid_values",
    [
        ("nativeGateSet", ["not_a_Braket_gate"]),
        ("connectivityGraph", {2: [0]}),
        ("connectivityGraph", {0: [2]}),
        ("supportedResultTypes", ["not_a_ResultType"]),
        ("supportedResultTypes", [ResultType(name="not_a_valid_ResultType")]),
        ("oneQubitProperties", {"2": valid_oneQubitProperties}),
        ("oneQubitProperties", {"0": valid_oneQubitProperties}),
        (
            "errorMitigation",
            {"not_a_ErrorMitigationScheme_subclass": ErrorMitigationProperties(minimumShots=2500)},
        ),
        ("errorMitigation", {Debias: "not_a_ErrorMitigationProperties"}),
    ],
)
def test_invalid_device_emulator_properties(valid_input, field, invalid_values):
    with pytest.raises(ValidationError):
        valid_input[field] = invalid_values
        DeviceEmulatorProperties.parse_obj(valid_input)


@pytest.mark.parametrize(
    "invalid_device_properties",
    [
        (1),
        (valid_oneQubitProperties),
    ],
)
def test_invalid_instantiation_from_invalid_device_properties(invalid_device_properties):
    with pytest.raises(ValueError):
        DeviceEmulatorProperties.from_device_properties(invalid_device_properties)


@pytest.mark.parametrize(
    "missing_field",
    [
        ("standardized"),
        ("paradigm"),
        ("braket.ir.openqasm.program"),
    ],
)
def test_invalid_instantiation_due_to_missing_field(minimal_valid_json, missing_field):
    minimal_valid_dict = json.loads(minimal_valid_json)
    if missing_field == "braket.ir.openqasm.program":
        minimal_valid_dict["action"].pop(missing_field)
    else:
        minimal_valid_dict.pop(missing_field)
    with pytest.raises(ValueError):
        DeviceEmulatorProperties._from_json(json.dumps(minimal_valid_dict))


@pytest.mark.parametrize(
    "invalid_json",
    ["1", "[1,2]"],
)
def test_invalid_json(invalid_json):
    with pytest.raises(ValueError):
        DeviceEmulatorProperties._from_json(invalid_json)

def test_from_json_non_fully_connected(reduced_standardized_json_2):
    result = DeviceEmulatorProperties._from_json(reduced_standardized_json_2)
    assert result.qubitCount == 3
    assert result.nativeGateSet == ["rx", "rz", "iswap"]
    assert result.connectivityGraph == {"0": ["1"], "1": ["0", "2"], "2": ["1"]}
    assert (
        result.oneQubitProperties["2"] == result.oneQubitProperties["1"] == result.oneQubitProperties["0"] == valid_oneQubitProperties
    )
    assert result.twoQubitProperties["0-1"] == result.twoQubitProperties["1-2"] == valid_twoQubitProperties
    assert result.supportedResultTypes == valid_supportedResultTypes
    assert result.errorMitigation == {}
    assert result.qubit_labels == [0, 1, 2]
    assert result.fully_connected == False
    assert result.directed == False

def test_from_json_non_fully_connected_but_directed(reduced_standardized_json_3):
    result = DeviceEmulatorProperties._from_json(reduced_standardized_json_3)
    assert result.qubitCount == 3
    assert result.nativeGateSet == ['cz', 'prx']
    assert result.connectivityGraph == {"0": ["1"], "1": ["2"]}
    assert (
        result.oneQubitProperties["2"] == result.oneQubitProperties["1"] == result.oneQubitProperties["0"] == valid_oneQubitProperties
    )
    assert result.twoQubitProperties["0-1"] == valid_twoQubitProperties
    assert result.supportedResultTypes == valid_supportedResultTypes
    assert result.errorMitigation == {}
    assert result.qubit_labels == [0, 1, 2]
    assert result.fully_connected == False
    assert result.directed == True
