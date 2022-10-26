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
from decimal import Decimal
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

    def _ensure_sorted(self) -> None:
        if not self._sorted:
            self._series = OrderedDict(sorted(self._series.items()))
            self._sorted = True

    def discretize(self, time_resolution: Decimal, value_resolution: Decimal) -> TimeSeries:
        """Creates a discretized version of the time series,
        rounding all times and values to the closest multiple of the
        corresponding resolution.

        Args:
            time_resolution (Decimal): Time resolution
            value_resolution (Decimal): Value resolution

        Returns:
            TimeSeries: A new discretized time series.
        """
        discretized_ts = TimeSeries()
        for item in self:
            discretized_ts.put(
                time=round(Decimal(item.time) / time_resolution) * time_resolution,
                value=round(Decimal(item.value) / value_resolution) * value_resolution,
            )
        return discretized_ts


# TODO: Verify if this belongs here.
def _all_close(first: TimeSeries, second: TimeSeries, tolerance: Number = 1e-7) -> bool:
    """
    Returns True if the times and values in two time series are all within (less than)
    a given tolerance range. The values in the TimeSeries must be numbers that can be
    subtracted from each-other, support getting the absolute value, and can be compared
    against the tolerance.


    Args:
        first (TimeSeries): A time series.
        second (TimeSeries): A time series.
        tolerance (Number): The tolerance value.

    Returns:
        bool: True if the times and values in two time series are all within (less than)
        a given tolerance range. If the time series are not the same size, this function
        will return False.
    """
    if len(first) != len(second):
        return False
    if len(first) == 0:
        return True
    first_times = first.times()
    second_times = second.times()
    first_values = first.values()
    second_values = second.values()
    for index in range(len(first)):
        if abs(first_times[index] - second_times[index]) >= tolerance:
            return False
        if abs(first_values[index] - second_values[index]) >= tolerance:
            return False
    return True
