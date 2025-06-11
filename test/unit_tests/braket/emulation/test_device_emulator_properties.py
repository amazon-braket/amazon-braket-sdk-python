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

import pytest
from pydantic.v1 import ValidationError

from braket.emulation.test_device_emulator_properties import DeviceEmulatorProperties

from braket.device_schema.result_type import ResultType
from braket.device_schema.error_mitigation.debias import Debias
from braket.device_schema.error_mitigation.error_mitigation_properties import (
    ErrorMitigationProperties,
)


@pytest.fixture
def mitigation_config() -> ErrorMitigationProperties:
    return ErrorMitigationProperties(minimumShots=1234)


@pytest.fixture
def full_props(mitigation_config) -> DeviceEmulatorProperties:
    return DeviceEmulatorProperties(errorMitigation={Debias: mitigation_config})


def test_valid_input_with_class_key(full_props, mitigation_config):
    assert "Debias" in full_props.errorMitigation
    assert full_props.errorMitigation["Debias"].minimumShots == mitigation_config.minimumShots

    resolved = full_props.get_error_mitigation_resolved()
    assert Debias in resolved
    assert resolved[Debias].minimumShots == mitigation_config.minimumShots


def test_valid_input_with_str_key(mitigation_config):
    props = DeviceEmulatorProperties(errorMitigation={"Debias": mitigation_config})
    resolved = props.get_error_mitigation_resolved()
    assert Debias in resolved
    assert resolved[Debias].minimumShots == mitigation_config.minimumShots


def test_invalid_key_type():
    with pytest.raises(TypeError, match="errorMitigation must be a dictionary"):
        DeviceEmulatorProperties(errorMitigation=123)


def test_invalid_value_type():
    with pytest.raises(ValidationError):
        DeviceEmulatorProperties(errorMitigation={Debias: {"minimumShots": "not-an-int"}})


def test_unknown_class_name_resolution():
    with pytest.raises(ValueError, match="Unknown ErrorMitigationScheme subclass"):
        DeviceEmulatorProperties.get_error_mitigation_class("DoesNotExist")


# @pytest.fixture
# def multi_config() -> DeviceEmulatorProperties:
#     return DeviceEmulatorProperties(
#         errorMitigation={
#             Debias: ErrorMitigationProperties(minimumShots=2500),
#             MockMitigation: ErrorMitigationProperties(minimumShots=1500)
#         }
#     )

# def test_multiple_classes(multi_config):
#     resolved = multi_config.get_error_mitigation_resolved()
#     assert Debias in resolved
#     assert MockMitigation in resolved
#     assert resolved[Debias].minimumShots == 2500
#     assert resolved[MockMitigation].minimumShots == 1500

# @pytest.fixture(scope="module")
# def valid_input():
#     input = {
#         "qubitCount": 2,
#         "nativeGateSet": ["cz", "prx", "s"],
#         "connectivityGraph": {"0": ["1"], "1": ["0"]},
#         "oneQubitProperties": {
#             "0": {
#                 "T1": {"value": 28.9, "standardError": 0.01, "unit": "us"},
#                 "T2": {"value": 44.5, "standardError": 0.02, "unit": "us"},
#                 "oneQubitFidelity": [
#                     {
#                         "fidelityType": {
#                             "name": "RANDOMIZED_BENCHMARKING",
#                             "description": "uses a standard RB technique",
#                         },
#                         "fidelity": 0.9993,
#                     },
#                     {
#                         "fidelityType": {"name": "READOUT"},
#                         "fidelity": 0.903,
#                         "standardError": None,
#                     },
#                 ],
#             },
#             "1": {
#                 "T1": {"value": 28.9, "unit": "us"},
#                 "T2": {"value": 44.5, "standardError": 0.02, "unit": "us"},
#                 "oneQubitFidelity": [
#                     {
#                         "fidelityType": {"name": "RANDOMIZED_BENCHMARKING"},
#                         "fidelity": 0.9986,
#                         "standardError": None,
#                     },
#                     {
#                         "fidelityType": {"name": "READOUT"},
#                         "fidelity": 0.867,
#                         "standardError": None,
#                     },
#                 ],
#             },
#         },
#         "twoQubitProperties": {
#             "0-1": {
#                 "twoQubitGateFidelity": [
#                     {
#                         "direction": {"control": 0, "target": 1},
#                         "gateName": "CNOT",
#                         "fidelity": 0.877,
#                         "fidelityType": {"name": "INTERLEAVED_RANDOMIZED_BENCHMARKING"},
#                     }
#                 ]
#             }
#         },
#         "supportedResultTypes": [
#             ResultType(
#                 name="Sample", observables=["x", "y", "z", "h", "i"], minShots=1, maxShots=20000
#             ),
#         ],
#         "errorMitigation": {Debias: ErrorMitigationProperties(minimumShots=2500)},
#     }
#     return input


# def test_valid(valid_input):
#     result = DeviceEmulatorProperties.parse_obj(valid_input)
#     assert result.qubitCount == 2
#     assert result.connectivityGraph == {"0": ["1"], "1": ["0"]}


# @pytest.mark.parametrize("missing_field", ["connectivityGraph"])
# def test_missing_field(valid_input, missing_field):
#     with pytest.raises(ValidationError):
#         valid_input.pop(missing_field)
#         DeviceEmulatorProperties.parse_obj(valid_input)
