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

from enum import Enum
from typing import Optional, Union

from pydantic.v1 import BaseModel, constr


class Control(BaseModel):
    name: constr(regex=r"^ctrl$")
    max_qubits: Optional[int] = None  # None indicates no limit


class NegControl(BaseModel):
    name: constr(regex=r"^negctrl$")
    max_qubits: Optional[int] = None  # None indicates no limit


class ExponentType(str, Enum):
    INT = "int"
    FLOAT = "float"


class Power(BaseModel):
    name: constr(regex=r"^pow$")
    exponent_types: list[ExponentType]


class Inverse(BaseModel):
    name: constr(regex=r"^inv$")


Modifier = Union[Control, NegControl, Power, Inverse]
