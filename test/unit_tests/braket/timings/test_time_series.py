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

from braket.timings.time_series import TimeSeries, _all_close


@pytest.fixture
def default_values():
    return [(2700, 25.1327), (300, 25.1327), (600, 15.1327), (Decimal(0.3), Decimal(0.4))]


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
    values = [0.5, 1, 1, 0]
    new_ts = TimeSeries.periodic_signal(values=values, dt=1, num_repeat=3)
    expected_times = list(range(12))
    expected_values = values * 3

    assert new_ts.times() == expected_times
    assert new_ts.values() == expected_values


@pytest.mark.parametrize(
    "time_res, expected_times",
    [
        # default_time_series: [(Decimal(0.3), Decimal(0.4), (300, 25.1327), (600, 15.1327), (2700, 25.1327))] # noqa
        (Decimal(0.5), [Decimal("0.5"), Decimal("300"), Decimal("600"), Decimal("2700")]),
        (Decimal(1), [Decimal("0"), Decimal("300"), Decimal("600"), Decimal("2700")]),
        (Decimal(200), [Decimal("0"), Decimal("400"), Decimal("600"), Decimal("2800")]),
        (Decimal(1000), [Decimal("0"), Decimal("1000"), Decimal("3000")]),
    ],
)
def test_discretize_times(default_time_series, time_res, expected_times):
    value_res = Decimal("1")
    assert expected_times == default_time_series.discretize(time_res, value_res).times()


@pytest.mark.parametrize(
    "value_res, expected_values",
    [
        # default_time_series: [(Decimal(0.3), Decimal(0.4), (300, 25.1327), (600, 15.1327), (2700, 25.1327))] # noqa
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
        (TimeSeries().put(float(0.1), float(0.2)), TimeSeries().put(float(0.1), float(0.2)), True),
        (TimeSeries().put(float(1), float(0.2)), TimeSeries().put(int(1), float(0.2)), True),
        (TimeSeries().put(float(0.1), float(0.2)), TimeSeries().put(float(0.2), float(0.2)), False),
        (TimeSeries().put(float(0.1), float(0.3)), TimeSeries().put(float(0.1), float(0.2)), False),
    ],
)
def test_all_close(first_series, second_series, expected_result):
    result = _all_close(first_series, second_series)
    assert result == expected_result
