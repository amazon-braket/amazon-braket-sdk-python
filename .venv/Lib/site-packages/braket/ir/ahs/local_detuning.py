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

from pydantic.v1 import BaseModel

from braket.ir.ahs.physical_field import PhysicalField


class LocalDetuning(BaseModel):
    r"""Specifies the local detuning, defined by the formula

    .. math::
        H_{shift} (t) := -\Delta(t) \sum_k h_k | r_k \rangle \langle r_k |

    where

        :math:`\Delta(t)` is the magnitude of the frequency shift in rad/s,

        :math:`h_k` is the site coefficient,

        :math:`|r_k \rangle` is the Rydberg state of atom k.

    with the sum :math:`\sum_k` taken over all target atoms.

    Attributes:
        magnitude: PhysicalField

    Examples:
        >>> LocalDetuning(magnitude=PhysicalField)
    """

    magnitude: PhysicalField
