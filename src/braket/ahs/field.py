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

from decimal import Decimal
from typing import Optional

from braket.ahs.pattern import Pattern
from braket.timings.time_series import TimeSeries


class Field:
    def __init__(self, time_series: TimeSeries, pattern: Optional[Pattern] = None) -> None:
        """A space and time dependent parameter of a program.

        Args:
            time_series (TimeSeries): The time series representing this field.
            pattern (Optional[Pattern]): The local pattern of real numbers.
        """
        self._time_series = time_series
        self._pattern = pattern

    @property
    def time_series(self) -> TimeSeries:
        """TimeSeries: The time series representing this field."""
        return self._time_series

    @property
    def pattern(self) -> Optional[Pattern]:
        """Optional[Pattern]: The local pattern of real numbers."""
        return self._pattern

    def discretize(
        self,
        time_resolution: Optional[Decimal] = None,
        value_resolution: Optional[Decimal] = None,
        pattern_resolution: Optional[Decimal] = None,
    ) -> Field:
        """Creates a discretized version of the field,
        where time, value and pattern are rounded to the
        closest multiple of their corresponding resolutions.

        Args:
            time_resolution (Optional[Decimal]): Time resolution
            value_resolution (Optional[Decimal]): Value resolution
            pattern_resolution (Optional[Decimal]): Pattern resolution

        Returns:
            Field: A new discretized field.
        """
        discretized_time_series = self.time_series.discretize(time_resolution, value_resolution)
        if self.pattern is None:
            discretized_pattern = None
        else:
            discretized_pattern = self.pattern.discretize(pattern_resolution)
        return Field(time_series=discretized_time_series, pattern=discretized_pattern)

    @staticmethod
    def from_lists(times: list[Decimal], values: list[Decimal], pattern: list[Decimal]) -> Field:
        """Builds Field from lists of time points, values and pattern.

        Args:
            times (list[Decimal]): The time points of the field
            values (list[Decimal]): The values of the field
            pattern (list[Decimal]): The pattern of the field

        Raises:
            ValueError: If the length of times and values differs.

        Returns:
            Field: Field.
        """
        if not (len(times) == len(values)):
            raise ValueError(
                f"The lengths of the lists for times({len(times)}) and values({len(values)})\
                are not equal"
            )

        time_series = TimeSeries.from_lists(times=times, values=values)

        return Field(time_series=time_series, pattern=Pattern(pattern))
