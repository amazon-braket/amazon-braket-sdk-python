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

from typing import Optional

from pydantic.v1 import BaseModel


class PulseFunctionArgument(BaseModel):
    """
    Defines a pulse function argument

    Attributes:
        name: The argument name
        type: The string name of the argument type
        description: Optional description for the argument

    """

    name: str
    type: str
    optional: bool = False
    description: Optional[str]


class PulseFunction(BaseModel):
    """
    Describes a pulse function

    Attributes:
        functionName: The name of the function
        arguments: List of function arguments
        returnType: Return type of the function. If null function has no return value.

    """

    functionName: str
    arguments: list[PulseFunctionArgument]
    returnType: Optional[str]
