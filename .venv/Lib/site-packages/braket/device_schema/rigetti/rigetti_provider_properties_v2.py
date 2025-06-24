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

from typing import Union

from pydantic.v1 import Field

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class RigettiProviderProperties(BraketSchemaBase):
    """
    This defines the parameters common to all Rigetti devices.

    Attributes:
        specs (dict[str, Union[str, list, dict[str, Union[str,list]]]): Basic specifications for the device,
            such as gate fidelities and coherence times. More details at
            https://docs.api.qcs.rigetti.com/#operation/GetInstructionSetArchitecture

    Examples:
        >>> import json
        >>> input_json = {
        ...    "braketSchemaHeader": {
        ...        "name": "braket.device_schema.rigetti.rigetti_provider_properties",
        ...        "version": "2",
        ...    },
        ...    "specs": {
        ...        "instructionSetArchitectures": [
        ...            {
        ...      "architecture": {
        ...        "edges": [
        ...          {
        ...            "node_ids": [
        ...              0,
        ...              0
        ...            ]
        ...          }
        ...        ],
        ...        "family": "None",
        ...        "nodes": [
        ...          {
        ...            "node_id": 0
        ...          }
        ...        ]
        ...      },
        ...      "benchmarks": [
        ...        {
        ...          "characteristics": [
        ...            {
        ...              "error": 0,
        ...              "name": "string",
        ...              "node_ids": [
        ...                0
        ...              ],
        ...              "parameter_values": [
        ...                0
        ...              ],
        ...              "timestamp": "2025-01-03T00:13:25Z",
        ...              "value": 0
        ...            }
        ...          ],
        ...          "name": "string",
        ...          "node_count": 0,
        ...          "parameters": [
        ...            {
        ...              "name": "string"
        ...            }
        ...          ],
        ...          "sites": [
        ...            {
        ...              "characteristics": [
        ...                {
        ...                  "error": 0,
        ...                  "name": "string",
        ...                  "node_ids": [
        ...                    0
        ...                  ],
        ...                  "parameter_values": [
        ...                    0
        ...                  ],
        ...                  "timestamp": "2025-01-03T00:13:25Z",
        ...                  "value": 0
        ...                }
        ...              ],
        ...              "node_ids": [
        ...                0
        ...              ]
        ...            }
        ...          ]
        ...        }
        ...      ],
        ...      "instructions": [
        ...        {
        ...          "characteristics": [
        ...            {
        ...              "error": 0,
        ...              "name": "string",
        ...              "node_ids": [
        ...                0
        ...              ],
        ...              "parameter_values": [
        ...                0
        ...              ],
        ...              "timestamp": "2025-01-03T00:13:25Z",
        ...              "value": 0
        ...            }
        ...          ],
        ...          "name": "string",
        ...          "node_count": 0,
        ...          "parameters": [
        ...            {
        ...              "name": "string"
        ...            }
        ...          ],
        ...          "sites": [
        ...            {
        ...              "characteristics": [
        ...                {
        ...                  "error": 0,
        ...                  "name": "string",
        ...                  "node_ids": [
        ...                    0
        ...                  ],
        ...                  "parameter_values": [
        ...                    0
        ...                  ],
        ...                  "timestamp": "2025-01-03T00:13:25Z",
        ...                  "value": 0
        ...                }
        ...              ],
        ...              "node_ids": [
        ...                0
        ...              ]
        ...            }
        ...          ]
        ...        }
        ...      ],
        ...      "name": "string"
        ...    }
        ...  ],
        ...  }
        >>> RigettiProviderProperties.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.rigetti.rigetti_provider_properties", version="2"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    specs: dict[str, Union[str, list, dict[str, Union[str, list]]]]
