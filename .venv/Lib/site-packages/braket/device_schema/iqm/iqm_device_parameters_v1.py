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

from pydantic.v1 import Field

from braket.device_schema.gate_model_parameters_v1 import GateModelParameters
from braket.schema_common.schema_base import BraketSchemaBase
from braket.schema_common.schema_header import BraketSchemaHeader


class IqmDeviceParameters(BraketSchemaBase):
    """
    This defines the parameters common to all the IQM devices.

    Attributes:
        paradigmParameters: Parameters that are common to gatemodel paradigm
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.iqm.iqm_device_parameters", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    paradigmParameters: GateModelParameters
