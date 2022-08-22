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

from typing import Optional
from decimal import Decimal

from braket.ahs.pattern import Pattern
from braket.ahs.time_series import TimeSeries


class Field:
    def __init__(self, time_series: TimeSeries, pattern: Optional[Pattern] = None) -> None:
        self._time_series = time_series
        self._pattern = pattern

    @property
    def time_series(self) -> TimeSeries:
        return self._time_series

    @property
    def pattern(self) -> Optional[Pattern]:
        return self._pattern

    def discretize(
        self,
        time_res: Decimal,
        value_res: Decimal,
        pattern_res: Optional[Decimal] = None
    ) -> Field:
        """Creates a discretized version of the field,
        where time, value and pattern are rounded to the
        closes multiple of their corresponding resolutions.

        Args:
            time_res (Decimal): Time resolution
            value_res (Decimal): Value resolution
            pattern_res (Decimal or None): Pattern resolution

        Returns:
            Field: A new discretized field.

        Raises:
            ValueError: if pattern_res is None, but there is a Pattern
        """
        discretized_time_series = self.time_series.discretize(time_res, value_res)
        if self.pattern is None:
            discretized_pattern = None
        else:
            if pattern_res is None:
                raise ValueError('since pattern is defined, pattern_res must be Decimal')
            discretized_pattern = self.pattern.discretize(pattern_res)

        discretized_field = Field(
            time_series=discretized_time_series,
            pattern=discretized_pattern
        )
        return discretized_field
