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

from typing import Optional, Union

from pydantic.v1 import Field

from braket.device_schema.blackbird_device_action_properties import BlackbirdDeviceActionProperties
from braket.device_schema.continuous_variable_qpu_paradigm_properties_v1 import (
    ContinuousVariableQpuParadigmProperties,
)
from braket.device_schema.device_action_properties import DeviceActionType
from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.xanadu.xanadu_provider_properties_v1 import XanaduProviderProperties
from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class XanaduDeviceCapabilities(BraketSchemaBase, DeviceCapabilities):
    """
    This defines the capabilities of a Xanadu device.

    Attributes:
        action(Dict[Union[DeviceActionType, str],
            Union[BlackbirdDeviceActionProperties]]): Actions that a
            Xanadu device can support
        paradigm(ContinuousVariableQpuParadigmProperties): Paradigm properties of a Xanadu device
        provider(Optional[XanaduProviderProperties]): Xanadu provider specific properties

    Examples:
        >>> import json
        >>> input_json = {
        ...    "braketSchemaHeader": {
        ...        "name": "braket.device_schema.xanadu.xanadu_device_capabilities",
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
        ...                "windowEndHour": "10:00",
        ...            }
        ...        ],
        ...        "shotsRange": [1, 1000000],
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
        ...        "braket.ir.blackbird.program": {
        ...            "actionType": "braket.ir.blackbird.program",
        ...            "version": ["1"],
        ...            "supportedOperations": ["BSGate", "XGate"],
        ...            "supportedResultTypes": [],
        ...        }
        ...    },
        ...    "paradigm": {
        ...        "braketSchemaHeader": {
        ...            "name": "braket.device_schema.continuous_variable_qpu_paradigm_properties",
        ...            "version": "1",
        ...        },
        ...        "nativeGateSet": ["XGate", "BSGate"],
        ...        "modes": {"spatial": 1},
        ...        "layout": "Some layout",
        ...        "compiler": ['borealis'],
        ...        "supportedLanguages": ["blackbird:1.0"],
        ...        "compilerDefault": "borealis",
        ...    },
        ...    "deviceParameters": {XanaduDeviceParameters.schema_json()},
        ... }
        >>> XanaduDeviceCapabilities.parse_raw_schema(json.dumps(input_json))

    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.xanadu.xanadu_device_capabilities", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    action: dict[
        Union[DeviceActionType, str],
        Union[BlackbirdDeviceActionProperties],
    ]
    paradigm: ContinuousVariableQpuParadigmProperties
    provider: Optional[XanaduProviderProperties]
