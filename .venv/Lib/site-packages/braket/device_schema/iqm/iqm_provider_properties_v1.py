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
# language governing permissions and limitations under the License

from typing import TypeVar, Union

from pydantic.v1 import Field

from braket.schema_common.schema_base import BraketSchemaBase
from braket.schema_common.schema_header import BraketSchemaHeader

GateFidelityType = TypeVar("GateFidelityType", bound=dict[str, Union[str, float]])
OneQubitType = TypeVar("OneQubitType", bound=Union[float, list[GateFidelityType]])
TwoQubitType = TypeVar("TwoQubitType", bound=dict[str, Union[float, dict[str, int]]])

QubitType = TypeVar("QubitType", bound=dict[str, Union[OneQubitType, TwoQubitType]])


class IqmProviderProperties(BraketSchemaBase):
    """
    This defines the properties common to all the IQM devices.

    Attributes:
        properties (dict[str, dict[str, QubitType]]): Basic specifications for
            the device, such as gate fidelities and coherence times.
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.iqm.iqm_provider_properties", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    properties: dict[str, dict[str, QubitType]]
