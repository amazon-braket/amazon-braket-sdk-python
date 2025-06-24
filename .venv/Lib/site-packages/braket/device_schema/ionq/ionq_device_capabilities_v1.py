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

import json
from typing import Optional, Union

from pydantic.v1 import Field

from braket.device_schema.device_action_properties import DeviceActionType
from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.gate_model_qpu_paradigm_properties_v1 import (
    GateModelQpuParadigmProperties,
)
from braket.device_schema.ionq.ionq_provider_properties_v1 import IonqProviderProperties
from braket.device_schema.jaqcd_device_action_properties import JaqcdDeviceActionProperties
from braket.device_schema.openqasm_device_action_properties import OpenQASMDeviceActionProperties
from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


def _loads_with_provider(serialized: str) -> dict:
    deserialized = json.loads(serialized)
    provider = deserialized.get("provider")
    deserialized["provider"] = (
        IonqProviderProperties.parse_raw(json.dumps(provider)).dict() if provider else None
    )
    return deserialized


def _dumps_with_provider(payload: dict, **kwargs):
    provider = payload.get("provider")
    payload["provider"] = (
        json.loads(IonqProviderProperties.parse_obj(provider).json()) if provider else None
    )
    return json.dumps(payload, **kwargs)


class IonqDeviceCapabilities(BraketSchemaBase, DeviceCapabilities):
    """
    This defines the capabilities of an IonQ device.

    Attributes:
        action(dict[Union[DeviceActionType, str],
            Union[OpenQASMDeviceActionProperties, JaqcdDeviceActionProperties]]): Actions that an
            IonQ device can support
        paradigm(GateModelQpuParadigmProperties): Paradigm properties
        provider(Optional[IonqProviderProperties]): IonQ provider specific properties

    Examples:
        >>> import json
        >>> input_json = {
        ...    "braketSchemaHeader": {
        ...        "name": "braket.device_schema.ionq.ionq_device_capabilities",
        ...        "version": "1",
        ...    },
        ...    "service": {
        ...        "braketSchemaHeader": {
        ...            "name": "braket.device_schema.device_service_properties",
        ...            "version": "1",
        ...        },
        ...        "executionWindows": [
        ...            {
        ...                "executionDay": "Everyday",
        ...                "windowStartHour": "09:00",
        ...                "windowEndHour": "09:05",
        ...            }
        ...        ],
        ...        "shotsRange": [1, 10],
        ...        "deviceCost": {
        ...             "price": 0.25,
        ...             "unit": "minute"
        ...         },
        ...         "deviceDocumentation": {
        ...             "imageUrl": "image_url",
        ...             "summary": "Summary on the device",
        ...             "externalDocumentationUrl": "external doc link",
        ...         },
        ...         "deviceLocation": "us-east-1",
        ...         "updatedAt": "2020-06-16T19:28:02.869136"
        ...    },
        ...    "action": {
        ...        "braket.ir.jaqcd.program": {
        ...            "actionType": "braket.ir.jaqcd.program",
        ...            "version": ["1"],
        ...            "supportedOperations": ["x", "y"],
        ...            "supportedResultTypes": [{
        ...                 "name": "resultType1",
        ...                 "observables": ["observable1"],
        ...                 "minShots": 0,
        ...                 "maxShots": 4,
        ...             }],
        ...        }
        ...    },
        ...    "paradigm": {
        ...        "braketSchemaHeader": {
        ...            "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
        ...            "version": "1",
        ...        },
        ...        "qubitCount": 11,
        ...        "nativeGateSet": ["ccnot", "cy"],
        ...        "connectivity": {
        ...            "fullyConnected": False,
        ...            "connectivityGraph": {"1": ["2", "3"]},
        ...        },
        ...    },
        ...    "deviceParameters": {IonqDeviceParameters.schema_json()},
        ... }
        >>> IonqDeviceCapabilities.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.ionq.ionq_device_capabilities", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    action: dict[
        Union[DeviceActionType, str],
        Union[OpenQASMDeviceActionProperties, JaqcdDeviceActionProperties],
    ]
    paradigm: GateModelQpuParadigmProperties
    provider: Optional[IonqProviderProperties]

    class Config:
        # Pydantic does not use the custom encoders/decoders of nested models:
        # https://github.com/pydantic/pydantic/issues/2277#issuecomment-1236369282
        # This should be fixed in Pydantic v2:
        # https://github.com/pydantic/pydantic/discussions/4456
        json_loads = _loads_with_provider
        json_dumps = _dumps_with_provider
