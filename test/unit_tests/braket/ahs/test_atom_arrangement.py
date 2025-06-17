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

from braket.ahs.analog_hamiltonian_simulation import DiscretizationError
from braket.ahs.atom_arrangement import AtomArrangement, SiteType


@pytest.fixture
def default_atom_arrangement():
    atom_arrangement = (
        AtomArrangement()
        .add((0, 3.1e-6), SiteType.FILLED)
        .add((0, 5.99e-6))
        .add((3.001e-6, 0))
        .add((3e-6, 3e-6))
        .add((-3.01e-6, 6.5e-6))
    )
    return atom_arrangement


def test_add_chaining():
    atom_arrangement = (
        AtomArrangement()
        .add(coordinate=(0, 0), site_type=SiteType.FILLED)
        .add((0, 3), SiteType.FILLED)
        .add((0, 6))
        .add((3, 0))
        .add((3, 3))
        .add((3, 6))
        .add((3, 0))
    )
    assert len(atom_arrangement) == 7


def test_iteration():
    values = [(0, 0), (0.1, 0.2), (Decimal(0.3), Decimal(0.4))]
    atom_arrangement = AtomArrangement()
    for value in values:
        atom_arrangement.add(value)
    returned_values = [site.coordinate for site in atom_arrangement]
    assert values == returned_values


def test_coordinate_list():
    values = [(0, 0), (0.1, 0.2), (Decimal(0.3), Decimal(0.4))]
    atom_arrangement = AtomArrangement()
    for value in values:
        atom_arrangement.add(value)
    for coord_index in range(2):
        coords = atom_arrangement.coordinate_list(coord_index)
        assert coords == [value[coord_index] for value in values]


@pytest.mark.parametrize(
    "position_res, expected_x, expected_y",
    [
        # default x: [0, 0, 3.001e-6, 3e-6, -3.01e-6]
        # default y: [3.1e-6, 5.99e-6, 0, 3e-6, 6.5e-6]
        (
            Decimal("1e-6"),
            [Decimal("0"), Decimal("0"), Decimal("3e-6"), Decimal("3e-6"), Decimal("-3e-6")],
            [Decimal("3e-6"), Decimal("6e-6"), Decimal("0"), Decimal("3e-6"), Decimal("6e-6")],
        ),
        (
            Decimal("1e-7"),
            [Decimal("0"), Decimal("0"), Decimal("3e-6"), Decimal("3e-6"), Decimal("-3e-6")],
            [Decimal("3.1e-6"), Decimal("6e-6"), Decimal("0"), Decimal("3e-6"), Decimal("6.5e-6")],
        ),
        (
            Decimal("2e-7"),
            [Decimal("0"), Decimal("0"), Decimal("3e-6"), Decimal("3e-6"), Decimal("-3e-6")],
            [Decimal("3e-6"), Decimal("6e-6"), Decimal("0"), Decimal("3e-6"), Decimal("6.4e-6")],
        ),
        (
            Decimal("1e-8"),
            [Decimal("0"), Decimal("0"), Decimal("3e-6"), Decimal("3e-6"), Decimal("-3.01e-6")],
            [
                Decimal("3.1e-6"),
                Decimal("5.99e-6"),
                Decimal("0"),
                Decimal("3e-6"),
                Decimal("6.5e-6"),
            ],
        ),
    ],
)
def test_discretize(default_atom_arrangement, position_res, expected_x, expected_y):
    properties = Mock()
    properties.lattice.geometry.positionResolution = position_res
    actual = default_atom_arrangement.discretize(properties)
    assert expected_x == actual.coordinate_list(0)
    assert expected_y == actual.coordinate_list(1)


@pytest.mark.xfail(raises=DiscretizationError)
def test_invalid_discretization_properties(default_atom_arrangement):
    properties = "not-a-valid-discretization-property"
    default_atom_arrangement.discretize(properties)
