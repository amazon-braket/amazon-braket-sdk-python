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

from collections import OrderedDict
from dataclasses import dataclass
from numbers import Number
from typing import Iterator, List


@dataclass
class TimeSeriesItem:
    time: Number
    value: Number


class TimeSeries:
    def __init__(self):
        self._series = OrderedDict()
        self._sorted = True
        self._largest_time = -1

    def put(
        self,
        time: Number,
        value: Number,
    ) -> TimeSeries:
        """Puts a value to the time series at the given time. A value passed to an existing
        time will overwrite the current value.

        Args:
            time (Number): The time of the value.
            value (Number): The value to add to the time series.

        Returns:
            TimeSeries: returns self (to allow for chaining).
        """
        if time in self._series:
            self._series[time] = TimeSeriesItem(time, value)
        elif time > self._largest_time:
            self._series[time] = TimeSeriesItem(time, value)
            self._largest_time = time
        else:
            self._series[time] = TimeSeriesItem(time, value)
            self._sorted = False
        return self

    def times(self) -> List[Number]:
        """Returns the times in the time series.

        Returns:
            List[Number]: The times in the time series.
        """
        self._ensure_sorted()
        return [item.time for item in self._series.values()]

    def values(self) -> List[Number]:
        """Returns the values in the time series.

        Returns:
            List[Number]: The values in the time series.
        """
        self._ensure_sorted()
        return [item.value for item in self._series.values()]

    def __iter__(self) -> Iterator:
        self._ensure_sorted()
        return self._series.values().__iter__()

    def __len__(self):
        return self._series.values().__len__()

    def _ensure_sorted(self):
        if not self._sorted:
            self._series = OrderedDict(sorted(self._series.items()))
            self._sorted = True
