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


from decimal import Decimal

from pydantic.v1 import BaseModel, Field

from braket.ir.ahs.atom_arrangement import AtomArrangement
from braket.ir.ahs.hamiltonian import Hamiltonian
from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class Setup(BaseModel):
    """
    The initial setup of the quantum register
    Attributes:
        ahs_register: The spatial setup of the neutral atom program
    """

    ahs_register: AtomArrangement


class Program(BraketSchemaBase):
    """Specifies an AHS program

    Attributes:
        braketSchemaHeader (BraketSchemaHeader): Schema header. Users do not need
            to set this value. Only default is allowed
        setup: Neutral atom lattice set up
        hamiltonian: rydberg hamiltonian

    Examples:
        >>> Program(
        ...     setup={"ahs_register":AtomArrangement},
        ...     hamiltonian={"drivingFields":DrivingField,"localDetuning":LocalDetuning}
        ...    )
    """

    _PROGRAM_HEADER = BraketSchemaHeader(name="braket.ir.ahs.program", version="1")
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    setup: Setup
    hamiltonian: Hamiltonian

    class Config:
        json_encoders = {Decimal: str}
