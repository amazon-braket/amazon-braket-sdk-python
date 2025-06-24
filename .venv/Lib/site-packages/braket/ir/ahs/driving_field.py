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


class DrivingField(BaseModel):
    r"""Specifies the driving field, defined by the formula

    .. math::
        H_{drive} (t) := \frac{\Omega(t)}{2} e^{i \phi(t)} \left(
            \sum_k |g_k \rangle \langle r_k| + |r_k \rangle \langle g_k|
        \right) - \Delta(t) \sum_k{| r_k \rangle \langle r_k |}

    where

        :math:`\Omega(t)` is the global Rabi frequency in rad/s,

        :math:`\phi(t)` is the global phase in rad/s,

        :math:`\Delta(t)` is the global detuning in rad/s,

        :math:`|g_k \rangle` is the ground state of atom k,

        :math:`|r_k \rangle` is the Rydberg state of atom k.

    with the sum :math:`\sum_k` taken over all target atoms.

    Attributes:
        amplitude: PhysicalField(pattern=“uniform”)
        phase: PhysicalField(pattern=“uniform”)
        detuning: PhysicalField(pattern=“uniform”)
    """

    amplitude: PhysicalField
    phase: PhysicalField
    detuning: PhysicalField
