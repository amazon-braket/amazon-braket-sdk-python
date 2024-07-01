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



import numpy as np
import pytest
from braket.ahs.atom_arrangement import AtomArrangement

@pytest.fixture
def canvas_boundary_points():
    return [(0, 0), (7.5e-5, 0), (7.5e-5, 7.5e-5), (0, 7.5e-5)]


def test_from_square_lattice(canvas_boundary_points):
    lattice_constant = 4e-6
    square_lattice = AtomArrangement.from_square_lattice(lattice_constant, canvas_boundary_points)
    expected_sites = [
        (x, y)
        for x in np.arange(0, 7.5e-5, lattice_constant)
        for y in np.arange(0, 7.5e-5, lattice_constant)
    ]
    assert len(square_lattice) == len(expected_sites)
    for site in square_lattice:
        assert site.coordinate in expected_sites


def test_from_rectangular_lattice(canvas_boundary_points):
    dx = 4e-6
    dy = 6e-6
    rectangular_lattice = AtomArrangement.from_rectangular_lattice(dx, dy, canvas_boundary_points)
    expected_sites = [
        (x, y)
        for x in np.arange(0, 7.5e-5, dx)
        for y in np.arange(0, 7.5e-5, dy)
    ]
    assert len(rectangular_lattice) == len(expected_sites)
    for site in rectangular_lattice:
        assert site.coordinate in expected_sites


def test_from_honeycomb_lattice(canvas_boundary_points):
    lattice_constant = 6e-6
    honeycomb_lattice = AtomArrangement.from_honeycomb_lattice(lattice_constant, canvas_boundary_points)
    a1 = (lattice_constant, 0)
    a2 = (lattice_constant / 2, lattice_constant * np.sqrt(3) / 2)
    decoration_points = [(0, 0), (lattice_constant / 2, lattice_constant * np.sqrt(3) / 6)]
    expected_sites = []
    vec_a, vec_b = np.array(a1), np.array(a2)
    x_min, y_min = 0, 0
    x_max, y_max = 7.5e-5, 7.5e-5
    i = 0
    while (origin := i * vec_a)[0] < x_max:
        j = 0
        while (point := origin + j * vec_b)[1] < y_max:
            if x_min <= point[0] <= x_max and y_min <= point[1] <= y_max:
                for dp in decoration_points:
                    decorated_point = point + np.array(dp)
                    if x_min <= decorated_point[0] <= x_max and y_min <= decorated_point[1] <= y_max:
                        expected_sites.append(tuple(decorated_point))
            j += 1
        i += 1
    assert len(honeycomb_lattice) == len(expected_sites)
    for site in honeycomb_lattice:
        assert site.coordinate in expected_sites


def test_from_bravais_lattice(canvas_boundary_points):
    a1 = (0, 5e-6)
    a2 = (3e-6, 4e-6)
    bravais_lattice = AtomArrangement.from_bravais_lattice([a1, a2], canvas_boundary_points)
    expected_sites = []
    vec_a, vec_b = np.array(a1), np.array(a2)
    x_min, y_min = 0, 0
    x_max, y_max = 7.5e-5, 7.5e-5
    i = 0
    while (origin := i * vec_a)[0] < x_max:
        j = 0
        while (point := origin + j * vec_b)[1] < y_max:
            if x_min <= point[0] <= x_max and y_min <= point[1] <= y_max:
                expected_sites.append(tuple(point))
            j += 1
        i += 1
    assert len(bravais_lattice) == len(expected_sites)
    for site in bravais_lattice:
        assert site.coordinate in expected_sites


def test_from_decorated_bravais_lattice(canvas_boundary_points):
    a1 = (0, 10e-6)
    a2 = (6e-6, 8e-6)
    basis = [(0, 0), (0, 5e-6), (4e-6, 2e-6)]
    decorated_bravais_lattice = AtomArrangement.from_decorated_bravais_lattice([a1, a2], basis, canvas_boundary_points)
    expected_sites = []
    vec_a, vec_b = np.array(a1), np.array(a2)
    x_min, y_min = 0, 0
    x_max, y_max = 7.5e-5, 7.5e-5
    i = 0
    while (origin := i * vec_a)[0] < x_max:
        j = 0
        while (point := origin + j * vec_b)[1] < y_max:
            if x_min <= point[0] <= x_max and y_min <= point[1] <= y_max:
                for dp in basis:
                    decorated_point = point + np.array(dp)
                    if x_min <= decorated_point[0] <= x_max and y_min <= decorated_point[1] <= y_max:
                        expected_sites.append(tuple(decorated_point))
            j += 1
        i += 1
    assert len(decorated_bravais_lattice) == len(expected_sites)
    for site in decorated_bravais_lattice:
        assert site.coordinate in expected_sites

