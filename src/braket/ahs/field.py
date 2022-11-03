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

from braket.ahs.discretization_types import DiscretizationError
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
        time_resolution: Decimal,
        value_resolution: Decimal,
        pattern_resolution: Optional[Decimal] = None,
    ) -> Field:
        """Creates a discretized version of the field,
        where time, value and pattern are rounded to the
        closest multiple of their corresponding resolutions.

        Args:
            time_resolution (Decimal): Time resolution
            value_resolution (Decimal): Value resolution
            pattern_resolution (Optional[Decimal]): Pattern resolution

        Returns:
            Field: A new discretized field.

        Raises:
            ValueError: if pattern_resolution is None, but there is a Pattern
        """
        discretized_time_series = self.time_series.discretize(time_resolution, value_resolution)
        if self.pattern is None:
            discretized_pattern = None
        else:
            if pattern_resolution is None:
                raise DiscretizationError(
                    f"{self.pattern} is defined but has no pattern_resolution defined"
                )
            discretized_pattern = self.pattern.discretize(pattern_resolution)
        discretized_field = Field(time_series=discretized_time_series, pattern=discretized_pattern)
        return discretized_field
