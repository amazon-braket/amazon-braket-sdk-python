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

# from braket.emulation.device_emulator_properties import (
#     DeviceEmulatorProperties,
# )
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

# from braket.emulation.device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES

from braket.device_schema.ionq.ionq_provider_properties_v1 import IonqProviderProperties


valid_oneQubitProperties = OneQubitProperties(
    T1=CoherenceTime(value=2e-5, standardError=None, unit="S"),
    T2=CoherenceTime(value=8e-6, standardError=None, unit="S"),
    oneQubitFidelity=[
        Fidelity1Q(
            fidelityType=FidelityType(name="RANDOMIZED_BENCHMARKING", description=None),
            fidelity=0.99,
            standardError=None,
        ),
        Fidelity1Q(
            fidelityType=FidelityType(name="READOUT", description=None),
            fidelity=0.9795,
            standardError=None,
        ),
    ],
).dict()

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
).dict()

valid_connectivityGraph = {"1": ["2"], "2": ["1"]}
valid_nativeGateSet = ["cz", "prx"]
valid_supportedResultTypes = [
    {"maxShots": 20000, "minShots": 1, "name": "Probability", "observables": None}
]

dict_errorMitigation = {
    "provider": {
        "errorMitigation": {
            "braket.device_schema.error_mitigation.debias.Debias": {"minimumShots": 2500}
        }
    }
}

minimal_valid_device_properties_dict = {
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1.0"],
        }
    },
    "paradigm": {
        "connectivity": {"connectivityGraph": valid_connectivityGraph, "fullyConnected": False},
        "nativeGateSet": valid_nativeGateSet,
        "qubitCount": 2,
    },
    "standardized": {
        "oneQubitProperties": {
            "1": valid_oneQubitProperties,
            "2": valid_oneQubitProperties,
        },
        "twoQubitProperties": {
            "1-2": valid_twoQubitProperties,
        },
    },
}

minimal_valid_device_properties_dict_with_errorMitigation = {
    **minimal_valid_device_properties_dict,
    **dict_errorMitigation,
}

reduced_standardized_gate_model_qpu_device_properties_dict = {
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1"],
        }
    },
    "braketSchemaHeader": {
        "name": "braket.device_schema.iqm.iqm_device_capabilities",
        "version": "1",
    },
    "deviceParameters": {},
    "paradigm": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
            "version": "1",
        },
        "connectivity": {"connectivityGraph": {"1": ["2"]}, "fullyConnected": False},
        "nativeGateSet": ["cz", "prx"],
        "qubitCount": 2,
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 20000],
        "updatedAt": "2024-04-04T01:10:02.869136",
    },
    "standardized": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
            "version": "1",
        },
        "oneQubitProperties": {
            "1": valid_oneQubitProperties,
            "2": valid_oneQubitProperties,
        },
        "twoQubitProperties": {"1-2": valid_twoQubitProperties},
    },
}
