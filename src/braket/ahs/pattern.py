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

from numbers import Number
from typing import List
from decimal import Decimal


class Pattern:
    def __init__(self, series: List[Number]):
        self._series = series

    @property
    def series(self) -> List[Number]:
        return self._series

    def discretize(self, res: Decimal) -> Pattern:
        """Creates a discretized version of the pattern,
        where each value is rounded to the nearest multiple
        of the resolution.

        Args:
            res: Resolution

        Returns:
            Pattern: The new discretized pattern
        """
        discretized_series = [round(Decimal(num) / res) * res for num in self.series]
        return Pattern(discretized_series)
