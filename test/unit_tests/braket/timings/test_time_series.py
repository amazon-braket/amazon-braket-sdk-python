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

from decimal import Decimal

import pytest

from braket.timings.time_series import StitchBoundaryCondition, TimeSeries, _all_close


@pytest.fixture
def default_values():
    return [
        (2700, Decimal("25.1327")),
        (300, Decimal("25.1327")),
        (600, Decimal("15.1327")),
        (Decimal("0.3"), Decimal("0.4")),
    ]


@pytest.fixture
def default_time_series(default_values):
    time_series = TimeSeries()
    for value in default_values:
        time_series.put(value[0], value[1])
    return time_series


def test_add_chaining():
    time_series = (
        TimeSeries()
        .put(time=0, value=0)
        .put(300, 25.1327)
        .put(2700, 25.1327)
        .put(3000, 0)
        .put(2700, 25.1327)
    )
    assert len(time_series) == 4


def test_iteration_sorted(default_values, default_time_series):
    sorted_returned_values = [(item.time, item.value) for item in default_time_series]
    assert sorted_returned_values == sorted(default_values)


def test_get_sorted(default_values, default_time_series):
    sorted_values = sorted(default_values)
    assert default_time_series.times() == [item[0] for item in sorted_values]
    assert default_time_series.values() == [item[1] for item in sorted_values]


def test_constant_like():
    times = list(range(10))
    constant_ts = TimeSeries.constant_like(times, constant=3.14)
    assert times == constant_ts.times()
    assert constant_ts.values() == [3.14] * len(times)


def test_periodic_signal():
    times = list(range(4))
    values = [0, 1, 3, 0]
    new_ts = TimeSeries.periodic_signal(times=times, values=values, num_repeat=3)
    expected_times = list(range(10))
    expected_values = [0, 1, 3, 0, 1, 3, 0, 1, 3, 0]

    assert new_ts.times() == expected_times
    assert new_ts.values() == expected_values


def test_constant_like_with_time_series():
    time_series = TimeSeries().put(0.0, 0.0).put(1.2, 3.14)
    constant_ts = TimeSeries.constant_like(time_series, constant=3.14)
    times = time_series.times()
    assert times == constant_ts.times()
    assert constant_ts.values() == [3.14] * len(times)


@pytest.mark.parametrize(
    "area, value_max, slew_rate_max, time_separation_min",
    [
        (2.0, 2.0, 4.0, 1.0),
        (1.0, 2.0, 4.0, 1.0),
        (4.0, 2.0, 1.0, 1.0),
        (1.0, 2.0, 1.0, 1.0),
    ],
)
def test_trapezoidal_signal_as_triangular_signal(
    area, value_max, slew_rate_max, time_separation_min
):
    ts = TimeSeries.trapezoidal_signal(area, value_max, slew_rate_max, time_separation_min)
    t_ramp = max(time_separation_min, value_max / slew_rate_max)
    value = area / t_ramp
    assert ts.times() == [0, t_ramp, 2 * t_ramp]
    assert ts.values() == [0, value, 0]


@pytest.mark.parametrize(
    "area, value_max, slew_rate_max, time_separation_min",
    [
        (4.0, 2.0, 4.0, 1.0),
        (2.1, 2.0, 4.0, 1.0),
        (6.0, 2.0, 1.0, 1.0),
        (4.1, 2.0, 1.0, 1.0),
    ],
)
def test_trapezoidal_signal_as_min_trapezoidal_signal(
    area, value_max, slew_rate_max, time_separation_min
):
    ts = TimeSeries.trapezoidal_signal(area, value_max, slew_rate_max, time_separation_min)
    t_ramp = max(time_separation_min, value_max / slew_rate_max)
    value = area / (t_ramp + time_separation_min)
    assert ts.times() == [0, t_ramp, t_ramp + time_separation_min, 2 * t_ramp + time_separation_min]
    assert ts.values() == [0, value, value, 0]


@pytest.mark.parametrize(
    "area, value_max, slew_rate_max, time_separation_min",
    [
        (4.1, 2.0, 4.0, 1.0),
        (6.1, 2.0, 1.0, 1.0),
    ],
)
def test_trapezoidal_signal_with_large_area(area, value_max, slew_rate_max, time_separation_min):
    ts = TimeSeries.trapezoidal_signal(area, value_max, slew_rate_max, time_separation_min)
    t_ramp = max(time_separation_min, value_max / slew_rate_max)
    t_plateau = area / value_max - t_ramp
    assert ts.times() == [0, t_ramp, t_ramp + t_plateau, 2 * t_ramp + t_plateau]
    assert ts.values() == [0, value_max, value_max, 0]


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize(
    "area, value_max, slew_rate_max, time_separation_min",
    [
        (-4.1, 2.0, 4.0, 1.0),
        (4.1, -2.0, 4.0, 1.0),
        (4.1, 2.0, -4.0, 1.0),
        (4.1, 2.0, 4.0, -1.0),
    ],
)
def test_trapezoidal_signal_with_negative_para(area, value_max, slew_rate_max, time_separation_min):
    TimeSeries.trapezoidal_signal(area, value_max, slew_rate_max, time_separation_min)


@pytest.mark.xfail(raises=ValueError)
def test_periodic_signal_not_eq_length():
    times = list(range(5))
    values = [0.5, 1, 1, 0]
    TimeSeries.periodic_signal(times=times, values=values, num_repeat=3)


def test_concatenate():
    times_1 = list(range(4))
    values_1 = [0.5, 1, 1, 0]
    time_series_1 = TimeSeries.from_lists(times=times_1, values=values_1)

    times_2 = list(range(4, 8))
    values_2 = [-0.5, -1, -1, 0]
    time_series_2 = TimeSeries.from_lists(times=times_2, values=values_2)

    new_ts = time_series_1.concatenate(time_series_2)

    assert new_ts.times() == times_1 + times_2
    assert new_ts.values() == values_1 + values_2

    new_ts = time_series_1.concatenate(TimeSeries())
    assert new_ts.times() == times_1
    assert new_ts.values() == values_1

    new_ts = TimeSeries().concatenate(time_series_1)
    assert new_ts.times() == times_1
    assert new_ts.values() == values_1

    new_ts = TimeSeries().concatenate(TimeSeries())
    assert new_ts.times() == []
    assert new_ts.values() == []


@pytest.mark.xfail(raises=ValueError)
def test_concatenate_not_ordered():
    times_1 = list(range(4))
    values_1 = [0.5, 1, 1, 0]
    time_series_1 = TimeSeries.from_lists(times=times_1, values=values_1)

    times_2 = list(range(4))
    values_2 = [-0.5, -1, -1, 0]
    time_series_2 = TimeSeries.from_lists(times=times_2, values=values_2)

    time_series_1.concatenate(time_series_2)


def test_from_lists():
    times = list(range(4))
    values = [0.5, 1, 1, 0]
    ts = TimeSeries.from_lists(times=times, values=values)
    assert ts.times() == times
    assert ts.values() == values


@pytest.mark.xfail(raises=ValueError)
def test_from_lists_not_equal_size():
    times = list(range(4))
    values = [0.5, 1, 1]
    TimeSeries.from_lists(times=times, values=values)


def test_stitch():
    times_1 = list(range(4))
    values_1 = [0.5, 1, 1, 0]
    time_series_1 = TimeSeries.from_lists(times=times_1, values=values_1)

    times_2 = list(range(4))
    values_2 = [-0.5, -1, -1, 0]
    time_series_2 = TimeSeries.from_lists(times=times_2, values=values_2)

    new_ts_mean = time_series_1.stitch(time_series_2, boundary=StitchBoundaryCondition.MEAN)
    new_ts_left = time_series_1.stitch(time_series_2, boundary=StitchBoundaryCondition.LEFT)
    new_ts_right = time_series_1.stitch(time_series_2, boundary=StitchBoundaryCondition.RIGHT)

    excepted_times = list(range(7))
    assert new_ts_mean.times() == excepted_times
    assert new_ts_left.times() == excepted_times
    assert new_ts_right.times() == excepted_times

    assert new_ts_mean.values() == [0.5, 1, 1, -0.25, -1, -1, 0]
    assert new_ts_left.values() == [0.5, 1, 1, 0, -1, -1, 0]
    assert new_ts_right.values() == [0.5, 1, 1, -0.5, -1, -1, 0]


def test_stitch_empty_ts():
    times = list(range(4))
    values = [0.5, 1, 1, 0]
    time_series = TimeSeries.from_lists(times=times, values=values)
    new_ts = time_series.stitch(TimeSeries())
    assert new_ts.times() == times
    assert new_ts.values() == values

    new_ts = TimeSeries().stitch(TimeSeries())
    assert new_ts.times() == []
    assert new_ts.values() == []

    new_ts = TimeSeries().stitch(time_series)
    assert new_ts.times() == time_series.times()
    assert new_ts.values() == time_series.values()


@pytest.mark.xfail(raises=ValueError)
def test_stitch_wrong_bndry_value():
    times_1 = list(range(4))
    values_1 = [0.5, 1, 1, 0]
    time_series_1 = TimeSeries.from_lists(times=times_1, values=values_1)

    times_2 = list(range(4))
    values_2 = [-0.5, -1, -1, 0]
    time_series_2 = TimeSeries.from_lists(times=times_2, values=values_2)

    time_series_1.stitch(time_series_2, boundary="average")


@pytest.mark.parametrize(
    "time_res, expected_times",
    [
        # default_time_series: [(Decimal(0.3), Decimal(0.4)), (300, 25.1327), (600, 15.1327), (2700, 25.1327)] # noqa
        (None, [Decimal("0.3"), Decimal("300"), Decimal("600"), Decimal("2700")]),
        (Decimal("0.5"), [Decimal("0.5"), Decimal("300"), Decimal("600"), Decimal("2700")]),
        (Decimal("1"), [Decimal("0"), Decimal("300"), Decimal("600"), Decimal("2700")]),
        (Decimal("200"), [Decimal("0"), Decimal("400"), Decimal("600"), Decimal("2800")]),
        (Decimal("1000"), [Decimal("0"), Decimal("1000"), Decimal("3000")]),
    ],
)
def test_discretize_times(default_time_series, time_res, expected_times):
    value_res = Decimal("1")
    assert expected_times == default_time_series.discretize(time_res, value_res).times()


@pytest.mark.parametrize(
    "value_res, expected_values",
    [
        # default_time_series: [(Decimal(0.3), Decimal(0.4)), (300, 25.1327), (600, 15.1327), (2700, 25.1327)] # noqa
        (None, [Decimal("0.4"), Decimal("25.1327"), Decimal("15.1327"), Decimal("25.1327")]),
        (Decimal("0.1"), [Decimal("0.4"), Decimal("25.1"), Decimal("15.1"), Decimal("25.1")]),
        (Decimal(1), [Decimal("0"), Decimal("25"), Decimal("15"), Decimal("25")]),
        (Decimal(6), [Decimal("0"), Decimal("24"), Decimal("18"), Decimal("24")]),
        (Decimal(100), [Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")]),
    ],
)
def test_discretize_values(default_time_series, value_res, expected_values):
    time_res = Decimal("0.1")
    assert expected_values == default_time_series.discretize(time_res, value_res).values()


@pytest.mark.parametrize(
    "first_series, second_series, expected_result",
    [
        (TimeSeries(), TimeSeries(), True),
        (TimeSeries().put(0.1, 0.2), TimeSeries(), False),
        (TimeSeries().put(0.1, 0.2), TimeSeries().put(0.1, 0.2), True),
        (TimeSeries().put(float(1), 0.2), TimeSeries().put(1, 0.2), True),
        (TimeSeries().put(0.1, 0.2), TimeSeries().put(0.2, 0.2), False),
        (TimeSeries().put(0.1, 0.3), TimeSeries().put(0.1, 0.2), False),
    ],
)
def test_all_close(first_series, second_series, expected_result):
    result = _all_close(first_series, second_series)
    assert result == expected_result
