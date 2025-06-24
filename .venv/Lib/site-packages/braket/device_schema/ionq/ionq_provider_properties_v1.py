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
from importlib import import_module
from typing import Optional

from pydantic.v1 import Field

from braket.device_schema.error_mitigation.error_mitigation_properties import (
    ErrorMitigationProperties,
)
from braket.device_schema.error_mitigation.error_mitigation_scheme import ErrorMitigationScheme
from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


def _loads_with_error_mitigation(serialized: str) -> dict:
    deserialized = json.loads(serialized)
    em = deserialized.get("errorMitigation") or {}
    em_with_types = {}
    for k, v in em.items():
        split = k.rsplit(".", 1)
        em_with_types[getattr(import_module(split[0]), split[1])] = v
    deserialized["errorMitigation"] = em_with_types or None
    return deserialized


def _dumps_with_error_mitigation(payload: dict, **kwargs):
    em = payload.get("errorMitigation") or {}
    em_serialized = {f"{k.__module__}.{k.__name__}": v for k, v in em.items()}
    payload["errorMitigation"] = em_serialized or None
    return json.dumps(payload, **kwargs)


class IonqProviderProperties(BraketSchemaBase):
    """
    This defines the properties common to all the IonQ devices.

    Attributes:
        fidelity(dict[str, dict[str, float]]): Average fidelity, the measured success
            to perform operations of the given type.
        timing(dict[str, float]): The timing characteristics of the device. 1Q, 2Q, readout,
            and reset are the operation times. T1 and T2 are decoherence times
        errorMitigation (Optional[dict[Type[ErrorMitigationScheme], ErrorMitigationProperties]]):
            The error mitigation schemes supported by the device, where the key is the Python type
            of the error mitigation scheme and the value contains the properties of the scheme.
            Default: None.

    Examples:
        >>> import json
        >>> input_json = {
        ...     "braketSchemaHeader": {
        ...         "name": "braket.device_schema.ionq.ionq_provider_properties",
        ...         "version": "1",
        ...     },
        ...     "fidelity": {
        ...         "1Q": {
        ...           "mean": 0.99717
        ...         },
        ...         "2Q": {
        ...           "mean": 0.9696
        ...         },
        ...         "spam": {
        ...           "mean": 0.9961
        ...         }
        ...       },
        ...       "timing": {
        ...         "T1": 10000000000,
        ...         "T2": 500000,
        ...         "1Q": 1.1e-05,
        ...         "2Q": 0.00021,
        ...         "readout": 0.000175,
        ...         "reset": 3.5e-05
        ...       },
        ...     errorMitigation: {
        ...         "braket.device_schema.error_mitigation.debias.Debias": {
        ...             "minimumShots": 2500
        ...         }
        ...     }
        ... }
        >>> IonqProviderProperties.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.ionq.ionq_provider_properties", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    fidelity: dict[str, dict[str, float]]
    timing: dict[str, float]
    errorMitigation: Optional[dict[type[ErrorMitigationScheme], ErrorMitigationProperties]] = None

    class Config:
        json_loads = _loads_with_error_mitigation
        json_dumps = _dumps_with_error_mitigation
