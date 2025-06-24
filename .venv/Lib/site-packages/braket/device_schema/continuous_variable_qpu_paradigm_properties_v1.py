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


class ContinuousVariableQpuParadigmProperties(BraketSchemaBase):
    """
    This class defines the properties that are specific to continuous variable (CV) devices

    Attributes:
        nativeGateSet: list of native gates

    Examples:
        >>> import json
        >>> input_json = {
        ...    "braketSchemaHeader": {
        ...        "name": "braket.device_schema.continuous_variable_qpu_paradigm_properties",
        ...        "version": "1",
        ...    },
        ...    "nativeGateSet": ["XGate", "BSGate"],
        ...     "modes": {
        ...         "spatial": 1
        ...     }
        ...     "layout": "some layout",
        ...     "compiler": ["borealis"],
        ...     "supportedLanguages": ["blackbird:1.0"],
        ...     "compilerDefault": "borealis",
        ...     "nativeGateSet": ["XGate"]
        ...     "gateParameters": {
        ...         "s": [
        ...                 [
        ...                     0.0,
        ...                     2.0
        ...                 ]
        ...         ],
        ...         "r0": [
        ...                 [
        ...                     -1.5707963267948966,
        ...                     1.5707963267948966
        ...                 ]
        ...         ]
        ...     }
        ... }
        >>> ContinuousVariableQpuParadigmProperties.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.continuous_variable_qpu_paradigm_properties", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    modes: dict[str, float]
    layout: str
    compiler: list[str]
    supportedLanguages: list[str]
    compilerDefault: str
    nativeGateSet: list[str]
    gateParameters: dict[str, list[list[float]]]
    target: str
