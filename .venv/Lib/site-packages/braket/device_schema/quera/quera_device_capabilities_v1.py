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


from pydantic.v1 import Field

from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.quera.quera_ahs_paradigm_properties_v1 import QueraAhsParadigmProperties
from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class QueraDeviceCapabilities(BraketSchemaBase, DeviceCapabilities):
    """
    This defines the capabilities of a Quera device.

    Attributes:
        provider: Properties specific to Quera provider

    Examples:
        >>> import json
        >>> input_json = {
        ...    "braketSchemaHeader": {
        ...        "name": "braket.device_schema.quera.quera_device_capabilities",
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
        ...        "shotsRange": [1, 100000],
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
        ...         "updatedAt": "2022-05-15T19:28:02.869136"
        ...    },
        ...    "action": {
        ...        "braket.ir.ahs.program": {
        ...            "actionType": "braket.ir.ahs.program",
        ...            "version": ["1"],
        ...        }
        ...    },
        ...    "paradigm": {QueraAhsParadigmProperties.schema_json()},
        ...    "deviceParameters": ""
        ... }
        >>> QueraDeviceCapabilities.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.quera.quera_device_capabilities", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    paradigm: QueraAhsParadigmProperties
