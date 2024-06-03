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
from numbers import Number
from typing import Optional


class Pattern:
    def __init__(self, series: list[Number]):
        """Represents the spatial dependence of a Field.

        Args:
            series (list[Number]): A series of numbers representing the the local
                pattern of real numbers.
        """
        self._series = series

    @property
    def series(self) -> list[Number]:
        """list[Number]: A series of numbers representing the local
        pattern of real numbers.
        """
        return self._series

    def discretize(self, resolution: Optional[Decimal]) -> Pattern:
        """Creates a discretized version of the pattern,
        where each value is rounded to the closest multiple
        of the resolution.

        Args:
            resolution (Optional[Decimal]): Resolution of the discretization

        Returns:
            Pattern: The new discretized pattern
        """
        if resolution is None:
            discretized_series = [Decimal(num) for num in self.series]
        else:
            discretized_series = [
                round(Decimal(num) / resolution) * resolution for num in self.series
            ]
        return Pattern(series=discretized_series)
