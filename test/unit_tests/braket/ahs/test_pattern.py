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

from braket.ahs.pattern import Pattern


@pytest.fixture
def default_values():
    return [
        Decimal(0),
        Decimal("0.1"),
        Decimal(1),
        Decimal("0.5"),
        Decimal("0.2"),
        Decimal("0.001"),
        Decimal("1e-10"),
    ]


@pytest.fixture
def default_pattern(default_values):
    return Pattern(series=default_values)


def test_create():
    expected_series = [1, 2, Decimal(3.1)]
    pattern = Pattern(expected_series)
    assert expected_series == pattern.series


@pytest.mark.parametrize(
    "res, expected_series",
    [
        # default pattern: [0, 0.1, 1, 0.5, 0.2, 0.001, 1e-10]
        (
            None,
            [
                Decimal("0"),
                Decimal("0.1"),
                Decimal("1"),
                Decimal("0.5"),
                Decimal("0.2"),
                Decimal("0.001"),
                Decimal("1e-10"),
            ],
        ),
        (
            Decimal("0.001"),
            [
                Decimal("0"),
                Decimal("0.1"),
                Decimal("1"),
                Decimal("0.5"),
                Decimal("0.2"),
                Decimal("0.001"),
                Decimal("0"),
            ],
        ),
        (
            Decimal("0.1"),
            [
                Decimal("0"),
                Decimal("0.1"),
                Decimal("1"),
                Decimal("0.5"),
                Decimal("0.2"),
                Decimal("0"),
                Decimal("0"),
            ],
        ),
        (
            Decimal("0.5"),
            [
                Decimal("0"),
                Decimal("0"),
                Decimal("1"),
                Decimal("0.5"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            ],
        ),
        (
            Decimal("0.9"),
            [
                Decimal("0"),
                Decimal("0"),
                Decimal("0.9"),
                Decimal("0.9"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            ],
        ),
    ],
)
def test_discretize(default_pattern, res, expected_series):
    print(default_pattern.series)
    print(res, default_pattern.discretize(res).series)
    assert expected_series == default_pattern.discretize(res).series
