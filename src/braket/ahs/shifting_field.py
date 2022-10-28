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

from __future__ import annotations

from typing import List

from braket.ahs.discretization_types import DiscretizationProperties
from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian


class ShiftingField(Hamiltonian):
    def __init__(self, magnitude: Field) -> None:
        r"""Creates a Hamiltonian term :math:`H_{shift}` representing the shifting field
        that changes the energy of the Rydberg level in an AnalogHamiltonianSimulation,
        defined by the formula

        .. math::
            H_{shift} (t) := -\Delta(t) \sum_k h_k | r_k \rangle \langle r_k |

        States:
          :math:`|r_k \rangle`: Rydberg state of atom k.

        Other symbols:
          :math:`\sum_k`: Sum over all target atoms.

        Args:
            magnitude (Field): containing the global magnitude time series (Delta(t)),
                where time measured in seconds (s) and values measured in rad/s) and the
                local pattern of unitless real numbers between 0 and 1 (h_k).
        """
        super().__init__()
        self._magnitude = magnitude

    @property
    def terms(self) -> List[Hamiltonian]:
        return [self]

    @property
    def magnitude(self) -> Field:
        """Field: containing the global magnitude time series (Delta(t)), where time measured in
        seconds (s) and values measured in rad/s) and the local pattern of unitless real numbers
        between 0 and 1 (h_k)."""
        return self._magnitude

    def discretize(self, properties: DiscretizationProperties) -> ShiftingField:
        """Creates a discretized version of the ShiftingField.

        Args:
            properties (DiscretizationProperties): Discretization properties of a device.

        Returns:
            ShiftingField: A new discretized ShiftingField.
        """
        shifting_parameters = properties.rydberg.rydbergLocal
        discretized_magnitude = self.magnitude.discretize(
            time_resolution=shifting_parameters.timeResolution,
            value_resolution=shifting_parameters.commonDetuningResolution,
            pattern_resolution=shifting_parameters.localDetuningResolution,
        )
        return ShiftingField(discretized_magnitude)
