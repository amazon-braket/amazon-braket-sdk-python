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

from importlib import import_module
from typing import Optional

from pydantic.v1 import Field, validator

from braket.device_schema.error_mitigation.error_mitigation_scheme import ErrorMitigationScheme
from braket.device_schema.gate_model_parameters_v1 import GateModelParameters
from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class IonqDeviceParameters(BraketSchemaBase):
    """
    This defines the parameters common to all the IonQ devices.

    Attributes:
        paradigmParameters: Parameters that are common to gatemodel paradigm
        errorMitigation: The error mitigation schemes to apply to the circuit

    Examples:
        >>> import json
        >>> input_json = {
        ...    "braketSchemaHeader": {
        ...        "name": "braket.device_schema.ionq.ionq_device_parameters",
        ...        "version": "1",
        ...    },
        ...    "paradigmParameters": {"braketSchemaHeader": {
        ...        "name": "braket.device_schema.gate_model_parameters",
        ...        "version": "1",
        ...    },"qubitCount": 1},
        ...    "errorMitigation": [
        ...        {
        ...            "type": "braket.device_schema.error_mitigation.debias.Debias"
        ...        }
        ...    ]
        ... }
        >>> IonqDeviceParameters.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.ionq.ionq_device_parameters", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    paradigmParameters: GateModelParameters
    errorMitigation: Optional[list[ErrorMitigationScheme]] = None

    @validator("errorMitigation", each_item=True, pre=True)
    def validate_em(cls, value, field):
        """
        Pydantic uses the validation subsystem to create objects.
        This custom validator ensures O(1) deserialization
        """
        if isinstance(value, ErrorMitigationScheme):
            return value
        if value is not None and "type" in value:
            split = value["type"].rsplit(".", 1)
            return getattr(import_module(split[0]), split[1])(**value)
        raise ValueError(f"Invalid type or value specified: {value} for field: {field}")
