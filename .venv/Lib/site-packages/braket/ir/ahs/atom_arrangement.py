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

from pydantic.v1 import BaseModel


class AtomArrangement(BaseModel):
    """
    Specifies the atom array

    Attributes:
        sites: List of 2-d coordinates where the tweezers trap atoms
        filling: Marks atoms that occupy the trap sites with 1, and empty sites with 0


    Examples:
        >>> AtomArrangement(sites=[
        ...         [0.0, 0.0],
        ...         [0.0, 3.0e-6],
        ...         [0.0, 6.0e-6],
        ...         [3.0e-6, 0.0],
        ...         [3.0e-6, 3.0e-6],
        ...         [3.0e-6, 6.0e-6]
        ...                 ],
        ...          filling=[1,1,1,1,0,0])
    """

    sites: list[list[Decimal]]
    filling: list[int]
