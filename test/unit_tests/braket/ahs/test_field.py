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
from unittest.mock import Mock

import pytest

from braket.ahs.field import Field
from braket.ahs.pattern import Pattern
from braket.timings.time_series import TimeSeries


@pytest.fixture
def default_time_series():
    default_values = [(2700, 25.1327), (300, 25.1327), (600, 15.1327), (Decimal(0.3), Decimal(0.4))]
    time_series = TimeSeries()
    for value in default_values:
        time_series.put(value[0], value[1])
    return time_series


@pytest.fixture
def default_pattern():
    return Pattern(series=[0, 0.1, 1, 0.5, 0.2, 0.001, 1e-10])


@pytest.fixture
def default_field(default_time_series, default_pattern):
    return Field(time_series=default_time_series, pattern=default_pattern)


@pytest.fixture
def default_uniform_field(default_time_series):
    return Field(time_series=default_time_series)


def test_create():
    mock0 = Mock()
    mock1 = Mock()
    field = Field(time_series=mock0, pattern=mock1)
    assert mock0 == field.time_series
    assert mock1 == field.pattern


@pytest.mark.parametrize(
    "time_res, value_res, pattern_res",
    [
        (Decimal("0.1"), Decimal("10"), Decimal("0.5")),
        (Decimal("10"), Decimal("20"), Decimal("0.1")),
        (Decimal("100"), Decimal("0.1"), Decimal("1")),
    ],
)
def test_discretize(
    default_time_series, default_pattern, default_field, time_res, value_res, pattern_res
):
    expected = Field(
        time_series=default_time_series.discretize(time_res, value_res),
        pattern=default_pattern.discretize(pattern_res),
    )
    actual = default_field.discretize(time_res, value_res, pattern_res)
    assert expected.pattern.series == actual.pattern.series
    assert expected.time_series.times() == actual.time_series.times()
    assert expected.time_series.values() == actual.time_series.values()


@pytest.mark.parametrize(
    "time_res, value_res, pattern_res",
    [
        (Decimal("0.1"), Decimal("10"), Decimal("0.5")),
        (Decimal("10"), Decimal("20"), None),
        (Decimal("0.1"), None, Decimal("0.5")),
        (None, Decimal("10"), Decimal("0.5")),
        (None, None, Decimal("0.5")),
        (None, Decimal("10"), None),
        (Decimal("0.1"), None, None),
        (None, None, None),
        (Decimal("100"), Decimal("0.1"), Decimal("1")),
    ],
)
def test_uniform_field(
    default_time_series, default_uniform_field, time_res, value_res, pattern_res
):
    expected = Field(time_series=default_time_series.discretize(time_res, value_res))
    actual = default_uniform_field.discretize(time_res, value_res, pattern_res)
    assert (
        (expected.pattern is None) and (actual.pattern is None)
    ) or expected.pattern.series == actual.pattern.series
    assert expected.time_series.times() == actual.time_series.times()
    assert expected.time_series.values() == actual.time_series.values()


def test_from_lists():
    times = [0, 0.1, 0.2, 0.3]
    values = [0.5, 0.8, 0.9, 1.0]
    pattern = [0.3, 0.7, 0.6, -0.5, 0, 1.6]

    sh_field = Field.from_lists(times, values, pattern)
    assert sh_field.time_series.times() == times
    assert sh_field.time_series.values() == values
    assert sh_field.pattern.series == pattern


@pytest.mark.xfail(raises=ValueError)
def test_from_lists_not_eq_length():
    times = [0, 0.1, 0.2]
    values = [0.5, 0.8, 0.9, 1.0]
    pattern = [0.3, 0.7, 0.6, -0.5, 0, 1.6]

    Field.from_lists(times, values, pattern)
