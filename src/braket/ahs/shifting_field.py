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

from braket.ahs.discretization_types import DiscretizationProperties
from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.pattern import Pattern
from braket.timings.time_series import StitchBoundaryCondition, TimeSeries


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
    def terms(self) -> list[Hamiltonian]:
        return [self]

    @property
    def magnitude(self) -> Field:
        r"""Field: containing the global magnitude time series :math:`\Delta(t)`,
        where time is measured in seconds (s) and values measured in rad/s)
        and the local pattern :math:`h_k` of dimensionless real numbers between 0 and 1."""
        return self._magnitude

    @staticmethod
    def from_lists(times: list[float], values: list[float], pattern: list[float]) -> ShiftingField:
        """Get the shifting field from a set of time points, values and pattern

        Args:
            times (list[float]): The time points of the shifting field
            values (list[float]): The values of the shifting field
            pattern (list[float]): The pattern of the shifting field

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

    def stitch(
        self, other: ShiftingField, boundary: StitchBoundaryCondition = StitchBoundaryCondition.MEAN
    ) -> ShiftingField:
        """Stitches two shifting fields based on TimeSeries.stitch method.
        The time points of the second ShiftingField are shifted such that the first time point of
        the second ShiftingField coincides with the last time point of the first ShiftingField.
        The boundary point value is handled according to StitchBoundaryCondition argument value.

        Args:
            other (ShiftingField): The second shifting field to be stitched with.
            boundary (StitchBoundaryCondition): {"mean", "left", "right"}. Boundary point handler.

                Possible options are
              - "mean" - take the average of the boundary value points of the first
                and the second time series.
              - "left" - use the last value from the left time series as the boundary point.
              - "right" - use the first value from the right time series as the boundary point.

        Returns:
            ShiftingField: The stitched ShiftingField object.

        Example (StitchBoundaryCondition.MEAN):
        ::
            time_series_1 = TimeSeries.from_lists(times=[0, 0.1], values=[1, 2])
            time_series_2 = TimeSeries.from_lists(times=[0.2, 0.4], values=[4, 5])

            stitch_ts = time_series_1.stitch(time_series_2, boundary=StitchBoundaryCondition.MEAN)

            Result:
                stitch_ts.times() = [0, 0.1, 0.3]
                stitch_ts.values() = [1, 3, 5]

        Example (StitchBoundaryCondition.LEFT):
        ::
            stitch_ts = time_series_1.stitch(time_series_2, boundary=StitchBoundaryCondition.LEFT)

            Result:
                stitch_ts.times() = [0, 0.1, 0.3]
                stitch_ts.values() = [1, 2, 5]

        Example (StitchBoundaryCondition.RIGHT):
        ::
            stitch_ts = time_series_1.stitch(time_series_2, boundary=StitchBoundaryCondition.RIGHT)

            Result:
                stitch_ts.times() = [0, 0.1, 0.3]
                stitch_ts.values() = [1, 4, 5]
        """
        if not (self.magnitude.pattern.series == other.magnitude.pattern.series):
            raise ValueError("The ShiftingField pattern for both fields must be equal.")

        new_ts = self.magnitude.time_series.stitch(other.magnitude.time_series, boundary)
        return ShiftingField(Field(new_ts, self.magnitude.pattern))

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
