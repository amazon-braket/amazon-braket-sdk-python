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
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from numbers import Number


@dataclass
class TimeSeriesItem:
    time: Number
    value: Number


class StitchBoundaryCondition(str, Enum):
    MEAN = "mean"
    LEFT = "left"
    RIGHT = "right"


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

    def times(self) -> list[Number]:
        """Returns the times in the time series.

        Returns:
            list[Number]: The times in the time series.
        """
        self._ensure_sorted()
        return [item.time for item in self._series.values()]

    def values(self) -> list[Number]:
        """Returns the values in the time series.

        Returns:
            list[Number]: The values in the time series.
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

    @staticmethod
    def from_lists(times: list[float], values: list[float]) -> TimeSeries:
        """Create a time series from the list of time and value points

        Args:
            times (list[float]): list of time points
            values (list[float]): list of value points

        Returns:
            TimeSeries: time series constructed from lists

        Raises:
            ValueError: If the len of `times` does not equal len of `values`.
        """
        if len(times) != len(values):
            raise ValueError(
                f"The lengths of the times({len(times)})\
                      and values({len(values)}) lists are not equal."
            )

        ts = TimeSeries()
        for t, v in zip(times, values):
            ts.put(t, v)
        return ts

    @staticmethod
    def constant_like(times: list | float | TimeSeries, constant: float = 0.0) -> TimeSeries:
        """Obtain a constant time series given another time series or the list of time points,
        and the constant values.

        Args:
            times (list | float | TimeSeries): list of time points or a time series
            constant (float): constant value

        Returns:
            TimeSeries: A constant time series
        """
        if not isinstance(times, list):
            times = times.times()

        ts = TimeSeries()
        for t in times:
            ts.put(t, constant)
        return ts

    def concatenate(self, other: TimeSeries) -> TimeSeries:
        """Concatenates two time series ino to a single time series.
        The time points in the final time series are obtained by concatenating
        two lists of time points from the first and the second time series.
        Similarly, the values in the final time series is a concatenated list
        of the values in the first and the second time series.

        Args:
            other (TimeSeries): The second time series to be concatenated
                Notes:
                Keeps the time points in both time series unchanged.
                Assumes that the time points in the first TimeSeries
                are at earlier times then the time points in the second TimeSeries.

        Returns:
            TimeSeries: The concatenated time series.

        Raises:
            ValueError: If the timeseries is not empty and time points in the first
                TimeSeries are not strictly smaller than in the second.

        Example:
        ::
            time_series_1 = TimeSeries.from_lists(times=[0, 0.1], values=[1, 2])
            time_series_2 = TimeSeries.from_lists(times=[0.2, 0.3], values=[4, 5])

            concat_ts = time_series_1.concatenate(time_series_2)

            Result:
                concat_ts.times() = [0, 0.1, 0.2, 0.3]
                concat_ts.values() = [1, 2, 4, 5]
        """
        not_empty_ts = len(other.times()) * len(self.times()) != 0
        if not_empty_ts and min(other.times()) <= max(self.times()):
            raise ValueError(
                "The time points in the first TimeSeries must be strictly smaller \
                then the time points in the second TimeSeries."
            )

        new_time_series = TimeSeries()
        new_times = self.times() + other.times()
        new_values = self.values() + other.values()
        for t, v in zip(new_times, new_values):
            new_time_series.put(t, v)

        return new_time_series

    def stitch(
        self, other: TimeSeries, boundary: StitchBoundaryCondition = StitchBoundaryCondition.MEAN
    ) -> TimeSeries:
        """Stitch two time series to a single time series. The time points of the
        second time series are shifted such that the first time point of the second series
        coincides with the last time point of the first series.
        The boundary point value is handled according to StitchBoundaryCondition argument value.

        Args:
            other (TimeSeries): The second time series to be stitched with.
            boundary (StitchBoundaryCondition): {"mean", "left", "right"}. Boundary point handler.

                Possible options are
              - "mean" - take the average of the boundary value points of the first
                and the second time series.
              - "left" - use the last value from the left time series as the boundary point.
              - "right" - use the first value from the right time series as the boundary point.

        Returns:
            TimeSeries: The stitched time series.

        Raises:
            ValueError: If boundary is not one of {"mean", "left", "right"}.

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
        if len(self.times()) == 0:
            return TimeSeries.from_lists(times=other.times(), values=other.values())
        if len(other.times()) == 0:
            return TimeSeries.from_lists(times=self.times(), values=self.values())

        new_time_series = TimeSeries()
        left_t, right_t = self.times()[-1], other.times()[0]
        other_times = [t - right_t + left_t for t in other.times()]
        new_times = self.times() + other_times[1:]

        left, right = self.values()[-1], other.values()[0]
        if boundary == StitchBoundaryCondition.MEAN:
            bndry_val = 0.5 * sum([left, right])
        elif boundary == StitchBoundaryCondition.LEFT:
            bndry_val = left
        elif boundary == StitchBoundaryCondition.RIGHT:
            bndry_val = right
        else:
            raise ValueError(
                f"Boundary handler value {boundary} is not allowed. \
                Possible options are: 'mean', 'left', 'right'."
            )

        new_values = self.values()[:-1] + [bndry_val] + other.values()[1:]

        for t, v in zip(new_times, new_values):
            new_time_series.put(t, v)

        return new_time_series

    def discretize(
        self, time_resolution: Decimal | None, value_resolution: Decimal | None
    ) -> TimeSeries:
        """Creates a discretized version of the time series,
        rounding all times and values to the closest multiple of the
        corresponding resolution.

        Args:
            time_resolution (Decimal | None): Time resolution
            value_resolution (Decimal | None): Value resolution

        Returns:
            TimeSeries: A new discretized time series.
        """
        discretized_ts = TimeSeries()
        for item in self:
            if time_resolution is None:
                discretized_time = Decimal(item.time)
            else:
                discretized_time = round(Decimal(item.time) / time_resolution) * time_resolution

            if value_resolution is None:
                discretized_value = Decimal(item.value)
            else:
                discretized_value = round(Decimal(item.value) / value_resolution) * value_resolution

            discretized_ts.put(time=discretized_time, value=discretized_value)
        return discretized_ts

    @staticmethod
    def periodic_signal(times: list[float], values: list[float], num_repeat: int = 1) -> TimeSeries:
        """Create a periodic time series by repeating the same block multiple times.

        Args:
            times (list[float]): List of time points in a single block
            values (list[float]): Values for the time series in a single block
            num_repeat (int): Number of block repetitions

        Raises:
            ValueError: If the first and last values are not the same

        Returns:
            TimeSeries: A new periodic time series.
        """
        if values[0] != values[-1]:
            raise ValueError("The first and last values must coincide to guarantee periodicity")
        new_time_series = TimeSeries()

        repeating_block = TimeSeries.from_lists(times=times, values=values)
        for _index in range(num_repeat):
            new_time_series = new_time_series.stitch(repeating_block)

        return new_time_series

    @staticmethod
    def trapezoidal_signal(
        area: float, value_max: float, slew_rate_max: float, time_separation_min: float = 0.0
    ) -> TimeSeries:
        """Get a trapezoidal time series with specified area, maximum value, maximum slew rate
        and minimum separation of time points

        Args:
            area (float): Total area under the time series
            value_max (float): The maximum value of the time series
            slew_rate_max (float): The maximum slew rate
            time_separation_min (float): The minimum separation of time points

        Raises:
            ValueError: If the time separation is negative

        Returns:
            TimeSeries: A trapezoidal time series

            Notes:
            The area of a time series f(t) is defined as the time integral of
            f(t) from t=0 to t=T, where T is the duration.
            We also assume the trapezoidal time series starts and ends at zero.
        """
        if area <= 0.0:
            raise ValueError("The area of the trapezoidal time series has to be positive.")
        if value_max <= 0.0:
            raise ValueError("The maximum value of the trapezoidal time series has to be positive.")
        if slew_rate_max <= 0.0:
            raise ValueError(
                "The maximum slew rate of the trapezoidal time series has to be positive."
            )
        if time_separation_min < 0.0:
            raise ValueError(
                "The minimum separation of time points of the trapezoidal time series "
                "has to be non-negative."
            )

        # Determine the ramp time to reach the max allowed value
        t_ramp = max(time_separation_min, value_max / slew_rate_max)

        # The max achievable area if there are 3 time points: [0, t_ramp, 2 * t_ramp]
        area_threshold_1 = t_ramp * value_max

        # The max achievable area if there are 4 time points:
        # [0, t_ramp, t_ramp + time_separation_min, 2 * t_ramp + time_separation_min]
        area_threshold_2 = (t_ramp + time_separation_min) * value_max

        if area <= area_threshold_1:
            # Determine the max value if area <= area_threshold_1
            value = area / t_ramp
            times = [0, t_ramp, 2 * t_ramp]
            values = [0, value, 0]
        elif area <= area_threshold_2:
            # Determine the max value if area_threshold_1 < area <= area_threshold_2
            value = area / (t_ramp + time_separation_min)
            times = [0, t_ramp, t_ramp + time_separation_min, 2 * t_ramp + time_separation_min]
            values = [0, value, value, 0]
        else:
            # Determine the t_plateau if area > area_threshold_2
            t_plateau = (area - area_threshold_2) / value_max + time_separation_min
            times = [0, t_ramp, t_ramp + t_plateau, 2 * t_ramp + t_plateau]
            values = [0, value_max, value_max, 0]

        return TimeSeries.from_lists(times, values)


# TODO: Verify if this belongs here.
def _all_close(first: TimeSeries, second: TimeSeries, tolerance: Number = 1e-7) -> bool:
    """Returns True if the times and values in two time series are all within (less than)
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
