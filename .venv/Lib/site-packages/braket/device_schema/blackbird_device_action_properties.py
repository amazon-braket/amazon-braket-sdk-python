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


from pydantic.v1 import conlist, constr

from braket.device_schema.device_action_properties import DeviceActionProperties
from braket.device_schema.result_type import ResultType


class BlackbirdDeviceActionProperties(DeviceActionProperties):
    """
    Defines the schema for properties for the actions that can be
    supported by devices that accept Blackbird IR.

    Attributes:
        supportedOperations: Operations supported by the Blackbird action.
        supportedResultTypes: Result types that are supported by the Blackbird action.


    Examples:
        >>> import json
        >>> input_json = {
        ...    "actionType": "braket.ir.blackbird.program",
        ...    "version": ["1"],
        ...    "supportedOperations": [ BSGate, XGate, ZGate],
        ...    "supportedResultTypes": [],
        ... }
        >>> BlackbirdDeviceActionProperties.parse_raw(json.dumps(input_json))

    """

    actionType: constr(regex=r"^braket\.ir\.blackbird\.program$")
    supportedOperations: list[str]
    supportedResultTypes: conlist(ResultType, max_items=0)
