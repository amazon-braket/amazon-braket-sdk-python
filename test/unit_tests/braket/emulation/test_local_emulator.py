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
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    CoherenceTime,
    Fidelity1Q,
    FidelityType,
    OneQubitProperties,
    TwoQubitProperties,
    GateFidelity2Q,
)
from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.device_action_properties import DeviceActionType
from braket.device_schema.gate_model_qpu_paradigm_properties_v1 import (
    GateModelQpuParadigmProperties,
)
from braket.device_schema.device_service_properties_v1 import DeviceServiceProperties
from braket.device_schema.openqasm_device_action_properties import OpenQASMDeviceActionProperties
from braket.device_schema.iqm.iqm_device_capabilities_v1 import IqmDeviceCapabilities

from braket.emulation.device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES

from braket.device_schema.ionq.ionq_provider_properties_v1 import IonqProviderProperties

from braket.emulation.local_emulator import LocalEmulator

from test_fixtures import (
    valid_connectivityGraph,
    valid_oneQubitProperties,
    valid_twoQubitProperties,
    minimal_valid_device_properties_dict,
    minimal_valid_device_properties_dict_with_errorMitigation,
    reduced_standardized_gate_model_qpu_device_properties_dict,
    valid_supportedResultTypes,
)


@pytest.fixture
def minimal_valid_json():
    return json.dumps(minimal_valid_device_properties_dict)


@pytest.fixture
def minimal_valid_json_with_errorMitigation():
    return json.dumps(minimal_valid_device_properties_dict_with_errorMitigation)


@pytest.fixture
def reduced_standardized_json():
    return json.dumps(reduced_standardized_gate_model_qpu_device_properties_dict)


def test_from_json_1(minimal_valid_json):
    emulator = LocalEmulator.from_json(minimal_valid_json)
    assert isinstance(emulator, LocalEmulator)
    


def test_from_json_1(minimal_valid_json_with_errorMitigation):
    emulator = LocalEmulator.from_json(minimal_valid_json_with_errorMitigation)
    assert isinstance(emulator, LocalEmulator)


def test_from_json_3(reduced_standardized_json):
    emulator = LocalEmulator.from_json(reduced_standardized_json)
    assert isinstance(emulator, LocalEmulator)


def test_from_device_properties(reduced_standardized_json):
    device_properties = IqmDeviceCapabilities.parse_raw(reduced_standardized_json)
    emulator = LocalEmulator.from_device_properties(device_properties)
    assert isinstance(emulator, LocalEmulator)


# @pytest.fixture
# def valid_input():
#     input = {
#         "qubitCount": 2,
#         "nativeGateSet": ["cz", "prx", "s"],
#         "connectivityGraph": {"0": ["1"], "1": ["0"]},
#         "oneQubitProperties": {
#             "0": valid_oneQubitProperties,
#             "1": valid_oneQubitProperties,
#         },
#         "twoQubitProperties": {"0-1": valid_twoQubitProperties},
#         "supportedResultTypes": valid_supportedResultTypes,
#         "errorMitigation": {Debias: ErrorMitigationProperties(minimumShots=2500)},
#     }
#     return input


# def test_yet_another_way_of_instantiation(valid_input):
#     result = DeviceEmulatorProperties.parse_obj(valid_input)
#     assert result.qubitCount == 2
#     assert result.connectivityGraph == {"0": ["1"], "1": ["0"]}
#     assert result.qubit_indices == [0, 1]


# @pytest.mark.parametrize(
#     "field, invalid_values",
#     [
#         ("nativeGateSet", ["not_a_Braket_gate"]),
#         ("connectivityGraph", {2: [0]}),
#         ("connectivityGraph", {0: [2]}),
#         ("supportedResultTypes", ["not_a_ResultType"]),
#         ("supportedResultTypes", [ResultType(name="not_a_valid_ResultType")]),
#         ("oneQubitProperties", {"2": valid_oneQubitProperties}),
#         ("oneQubitProperties", {"0": valid_oneQubitProperties}),
#         (
#             "errorMitigation",
#             {"not_a_ErrorMitigationScheme_subclass": ErrorMitigationProperties(minimumShots=2500)},
#         ),
#         ("errorMitigation", {Debias: "not_a_ErrorMitigationProperties"}),
#     ],
# )
# def test_invalid_device_emulator_properties(valid_input, field, invalid_values):
#     with pytest.raises(ValidationError):
#         valid_input[field] = invalid_values
#         DeviceEmulatorProperties.parse_obj(valid_input)


# @pytest.mark.parametrize(
#     "invalid_device_properties",
#     [
#         (1),
#         (valid_oneQubitProperties),
#     ],
# )
# def test_invalid_instantiation_from_invalid_device_properties(invalid_device_properties):
#     with pytest.raises(ValueError):
#         DeviceEmulatorProperties.from_device_properties(invalid_device_properties)


# @pytest.mark.parametrize(
#     "missing_field",
#     [
#         ("standardized"),
#         ("paradigm"),
#         ("braket.ir.openqasm.program"),
#     ],
# )
# def test_invalid_instantiation_due_to_missing_field(minimal_valid_json, missing_field):
#     minimal_valid_dict = json.loads(minimal_valid_json)
#     if missing_field == "braket.ir.openqasm.program":
#         minimal_valid_dict["action"].pop(missing_field)
#     else:
#         minimal_valid_dict.pop(missing_field)
#     with pytest.raises(ValueError):
#         DeviceEmulatorProperties.from_json(json.dumps(minimal_valid_dict))


# @pytest.mark.parametrize(
#     "invalid_json",
#     ["1", "[1,2]"],
# )
# def test_invalid_json(invalid_json):
#     with pytest.raises(ValueError):
#         DeviceEmulatorProperties.from_json(invalid_json)

