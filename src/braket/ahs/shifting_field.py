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
from braket.ahs.pattern import Pattern
from braket.timings.time_series import TimeSeries


class ShiftingField(Hamiltonian):
    def __init__(self, magnitude: Field) -> None:
        r"""Creates a Hamiltonian term :math:`H_{shift}` representing the shifting field
        that changes the energy of the Rydberg level in an AnalogHamiltonianSimulation,
        defined by the formula

        .. math::
            H_{shift} (t) := -\Delta(t) \sum_k h_k | r_k \rangle \langle r_k |

        where

            :math:`\Delta(t)` is the magnitude of the frequency shift in rad/s,

            :math:`h_k` is the site coefficient of atom :math:`k`,
            a dimensionless real number between 0 and 1,

            :math:`|r_k \rangle` is the Rydberg state of atom :math:`k`.

        with the sum :math:`\sum_k` taken over all target atoms.

        Args:
            magnitude (Field): containing the global magnitude time series :math:`\Delta(t)`,
                where time is measured in seconds (s) and values are measured in rad/s, and the
                local pattern :math:`h_k` of dimensionless real numbers between 0 and 1.
        """
        super().__init__()
        self._magnitude = magnitude

    @property
    def terms(self) -> List[Hamiltonian]:
        return [self]

    @property
    def magnitude(self) -> Field:
        r"""Field: containing the global magnitude time series :math:`\Delta(t)`,
        where time is measured in seconds (s) and values measured in rad/s)
        and the local pattern :math:`h_k` of dimensionless real numbers between 0 and 1."""
        return self._magnitude

    def concatenate(self, other: ShiftingField) -> ShiftingField:
        """Concatenate two driving fields to a single driving field.
        Assumes that the spatial modulation pattern is the same for the both driving fields.
            Args:
                other (ShiftingField): The second shifting field to be concatenated
            Returns:
                ShiftingField: The concatenated shifting field
            Note: In case if self.magnitude.pattern is empty creates pattern from the second
            ShiftingField
            Raises:
                ValueError: if the patterns of the two shifting fields are not identical.
        """
        current_pattern = self.magnitude.pattern.series
        if current_pattern != other.magnitude.pattern.series and len(current_pattern) > 0:
            raise ValueError("The patterns in the first and second TimeSeries must be equal.")

        new_magnitude = self.magnitude.time_series.concatenate(other.magnitude.time_series)
        return ShiftingField(Field(new_magnitude, other.magnitude.pattern))

    @staticmethod
    def concatenate_list(shift_fields: List[ShiftingField]) -> ShiftingField:
        """Concatenate a list of shifting fields to a single driving field
        Args:
            shift_fields (List[ShiftingField]): The list of shifting fields to be concatenated
        Returns:
            ShiftingField: The concatenated shifting field.
            For the empty input list returns empty ShiftingField object.
        """
        if len(shift_fields) == 0:
            return ShiftingField(magnitude=TimeSeries())

        shift = ShiftingField(magnitude=shift_fields[0].magnitude)
        for sf in shift_fields[1:]:
            shift = shift.concatenate(sf)
        return shift

    @staticmethod
    def from_lists(times: List[float], values: List[float], pattern: List[float]) -> ShiftingField:
        """Get the shifting field from a set of time points, values and pattern
        Args:
            times (List[float]): The time points of the shifting field
            values (List[float]): The values of the shifting field
            pattern (List[float]): The pattern of the shifting field
        Returns:
            ShiftingField: The shifting field obtained
        """
        if len(times) != len(values):
            raise ValueError("The length of the times and values lists must be equal.")

        magnitude = TimeSeries()
        for t, v in zip(times, values):
            magnitude.put(t, v)
        shift = ShiftingField(Field(magnitude, Pattern(pattern)))

        return shift

    def discretize(self, properties: DiscretizationProperties) -> ShiftingField:
        """Creates a discretized version of the ShiftingField.

        Args:
            properties (DiscretizationProperties): Capabilities of a device that represent the
                resolution with which the device can implement the parameters.

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
