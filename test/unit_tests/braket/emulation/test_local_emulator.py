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
from braket.emulation.emulator import Emulator

valid_oneQubitProperties = OneQubitProperties(
    T1=CoherenceTime(value=2e-5, standardError=1e-6, unit="S"),
    T2=CoherenceTime(value=8e-6, standardError=5e-7, unit="S"),
    oneQubitFidelity=[
        Fidelity1Q(
            fidelityType=FidelityType(name="RANDOMIZED_BENCHMARKING", description=None),
            fidelity=0.99,
            standardError=1e-5,
        ),
        Fidelity1Q(
            fidelityType=FidelityType(name="READOUT", description=None),
            fidelity=0.9795,
            standardError=None,
        ),
    ],
)

valid_twoQubitProperties = TwoQubitProperties(
    twoQubitGateFidelity=[
        GateFidelity2Q(
            direction=None,
            gateName="CZ",
            fidelity=0.99,
            standardError=0.0009,
            fidelityType=FidelityType(name="RANDOMIZED_BENCHMARKING", description=None),
        )
    ]
)

valid_connectivityGraph = {"0": ["1"], "1": ["0"]}


@pytest.fixture
def valid_input_1():
    input = {
        "qubitCount": 2,
        "nativeGateSet": ["cz", "prx", "s"],
        "connectivityGraph": valid_connectivityGraph,
        "oneQubitProperties": {
            "0": valid_oneQubitProperties.dict(),
            "1": valid_oneQubitProperties.dict(),
        },
        "twoQubitProperties": {"0-1": valid_twoQubitProperties.dict()},
        "supportedResultTypes": [
            ResultType(
                name="Sample", observables=["x", "y", "z", "h", "i"], minShots=1, maxShots=20000
            ),
        ],
        "errorMitigation": {Debias: ErrorMitigationProperties(minimumShots=2500)},
    }
    return input

fakeproperties = IonqProviderProperties(
    braketSchemaHeader={
        "name": "braket.device_schema.ionq.ionq_provider_properties",
        "version": "1",
    },
    fidelity={"1Q": {"mean": 0.99}, "2Q": {"mean": 0.9}, "spam": {"mean": 0.9}},
    timing={
        "T1": 10000000000,
        "T2": 500000,
        "1Q": 1.1e-05,
        "2Q": 0.00021,
        "readout": 0.000175,
        "reset": 3.5e-05,
    },
    errorMitigation={Debias: {"minimumShots": 2500}},
)

# @pytest.fixture
# def valid_device_properties():
#     input = {
#         "service": {"executionWindows": [], "shotsRange": [1, 2]},
#         "action": {
#             "braket.ir.openqasm.program": OpenQASMDeviceActionProperties(
#                 actionType="braket.ir.openqasm.program",
#                 version=["1"],
#                 supportedOperations=["x"],
#                 supportedResultTypes=DEFAULT_SUPPORTED_RESULT_TYPES,
#             )
#         },
#         "deviceParameters": {},
#         "paradigm": {
#             "braketSchemaHeader": {
#                 "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
#                 "version": "1",
#             },
#             "connectivity": {"connectivityGraph": valid_connectivityGraph, "fullyConnected": False},
#             "nativeGateSet": ["cz", "prx"],
#             "qubitCount": 2,
#         },
#         "standardized": {
#             "braketSchemaHeader": {
#                 "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
#                 "version": "1",
#             },
#             "oneQubitProperties": {
#                 "0": valid_oneQubitProperties.dict(),
#                 "1": valid_oneQubitProperties.dict(),
#             },
#             "twoQubitProperties": {"0-1": valid_twoQubitProperties.dict()},
#         },
#     }
#     device_properties = IqmDeviceCapabilities.parse_obj(input)
#     device_properties.provider = fakeproperties
#     return device_properties



@pytest.fixture
def valid_input_2():
    input = {
        "service": {"executionWindows": [], "shotsRange": [1, 2]},
        "action": {
            "braket.ir.openqasm.program": OpenQASMDeviceActionProperties(
                actionType="braket.ir.openqasm.program",
                version=["1"],
                supportedOperations=["x"],
                supportedResultTypes=DEFAULT_SUPPORTED_RESULT_TYPES,
            )
        },
        "deviceParameters": {},
        "paradigm": {
            "braketSchemaHeader": {
                "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
                "version": "1",
            },
            "connectivity": {"connectivityGraph": valid_connectivityGraph, "fullyConnected": False},
            "nativeGateSet": ["cz", "prx"],
            "qubitCount": 2,
        },
        "standardized": {
            "braketSchemaHeader": {
                "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
                "version": "1",
            },
            "oneQubitProperties": {
                "0": valid_oneQubitProperties.dict(),
                "1": valid_oneQubitProperties.dict(),
            },
            "twoQubitProperties": {"0-1": valid_twoQubitProperties.dict()},
        },
    }
    return input


def test_instantiation_with_device_properties(valid_input_1):
    valid_device_emulator_properties = DeviceEmulatorProperties.parse_obj(valid_input_1)
    emulator = LocalEmulator.from_device_properties(valid_device_emulator_properties)
    assert isinstance(emulator, Emulator)

def test_instantiation_with_device_properties2(valid_input_2):
    valid_device_properties = IqmDeviceCapabilities.parse_obj(valid_input_2)
    valid_device_properties.provider = fakeproperties
    emulator = LocalEmulator.from_device_properties(valid_device_properties)
    assert isinstance(emulator, Emulator)

# def test_insttest_instantiation_with_json1(valid_input_1):
#     valid_input_1.pop("errorMitigation")
#     valid_device_emulator_properties = DeviceEmulatorProperties.parse_obj(valid_input_1)
#     emulator = LocalEmulator.from_json(valid_device_emulator_properties.json())
#     assert isinstance(emulator, Emulator)


def test_insttest_instantiation_with_json2(valid_input_2):
    valid_device_properties = IqmDeviceCapabilities.parse_obj(valid_input_2)
    emulator = LocalEmulator.from_json(valid_device_properties.json())
    assert isinstance(emulator, Emulator)

# @pytest.mark.parametrize(
#     "backend",
#     ["braket_sv1", "braket_ahs"],
# )
# def test_invalid_backend(valid_input_1, backend):
#     valid_device_emulator_properties = DeviceEmulatorProperties.parse_obj(valid_input_1)
#     with pytest.raises(ValueError):
#         LocalEmulator.from_device_properties(valid_device_emulator_properties, backend=backend)