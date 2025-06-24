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

from pydantic.v1 import BaseModel, Field

from braket.ir.ahs.driving_field import DrivingField
from braket.ir.ahs.local_detuning import LocalDetuning


class Hamiltonian(BaseModel):
    """
    Specifies the Hamiltonian

    Attributes:
        drivingFields: An externally controlled force
            that drives coherent transitions between selected levels of certain atom types
        localDetuning: An externally controlled polarizing force
            the effect of which is accurately described by a frequency shift of certain levels.

    Examples:
        >>> Hamiltonian(drivingFields=[DrivingField],localDetuning=[LocalDetuning])
    """

    drivingFields: list[DrivingField]
    localDetuning: list[LocalDetuning] = Field(alias="shiftingFields")

    def __getattr__(self, name):
        return self.__dict__[name] if name != "shiftingFields" else self.__dict__["localDetuning"]

    def __setattr__(self, name, value):
        if name == "shiftingFields":
            name = "localDetuning"
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name == "shiftingFields":
            name = "localDetuning"
        del self.__dict__[name]

    class Config:
        allow_population_by_field_name = True
