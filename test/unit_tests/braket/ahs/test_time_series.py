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

from braket.ahs.time_series import TimeSeries


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


def test_iteration():
    values = [(300, 25.1327), (2700, 25.1327), (Decimal(0.3), Decimal(0.4))]
    time_series = TimeSeries()
    for value in values:
        time_series.put(value[0], value[1])
    returned_values = []
    for item in time_series:
        returned_values.append((item.time, item.value))
    assert values == returned_values


def test_get():
    expected_values = [(300, 25.1327), (2700, 25.1327), (Decimal(0.3), Decimal(0.4))]
    time_series = TimeSeries()
    for value in expected_values:
        time_series.put(value[0], value[1])
    times = time_series.times()
    values = time_series.values()
    assert times == [item[0] for item in expected_values]
    assert values == [item[1] for item in expected_values]
