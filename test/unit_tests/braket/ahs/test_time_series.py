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

from braket.ahs.time_series import TimeSeries


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
