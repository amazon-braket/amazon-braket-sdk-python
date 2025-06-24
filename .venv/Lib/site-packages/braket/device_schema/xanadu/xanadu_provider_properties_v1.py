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

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class XanaduProviderProperties(BraketSchemaBase):
    """
    This defines the parameters common to all Xanadu devices.

    Attributes:
        specs (Dict[str, Dict[str, Dict[str, float]]]): Basic specifications for the device,
            such as gate fidelities and coherence times.

    Examples:
        >>> import json
        >>> input_json = {
        ...    "braketSchemaHeader": {
        ...        "name": "braket.device_schema.xanadu.xanadu_provider_properties",
        ...        "version": "1",
        ...    },
        ...    "loop_phases": [
        ...        -1.5957742826142312
        ...    ],
        ...    "schmidt_number": 1.1240597475954237,
        ...    "common_efficiency": 0.42871142768980564,
        ...    "loop_efficiencies": [
        ...        0.8518902619448591
        ...    ],
        ...    "squeezing_parameters_mean": {
        ...        "low": 0.6130577606615072,
        ...        "high": 1.0635796125448667,
        ...        "medium": 0.893051739389763
        ...    },
        ...    "relative_channel_efficiencies": [
        ...        0.9648681625753431,
        ...        1.0,
        ...        0.973400900408643,
        ...    ]
        ...  }
        >>> XanaduProviderProperties.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.xanadu.xanadu_provider_properties", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    loopPhases: list[float]
    schmidtNumber: float
    commonEfficiency: float
    squeezingParametersMean: dict[str, float]
    relativeChannelEfficiencies: list[float]
    loopEfficiencies: list[float]
