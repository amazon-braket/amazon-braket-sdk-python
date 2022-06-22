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
