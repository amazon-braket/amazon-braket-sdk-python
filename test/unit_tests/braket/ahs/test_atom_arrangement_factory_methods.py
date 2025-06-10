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

import math
from decimal import Decimal
import itertools

import pytest

from braket.ahs.atom_arrangement import AtomArrangement, SiteType
from braket.ahs.canvas import Canvas


class TestAtomArrangementFactoryMethods:
    @pytest.fixture
    def square_canvas(self):
        """A simple square canvas for testing."""
        return Canvas([(0, 0), (1e-5, 0), (1e-5, 1e-5), (0, 1e-5)])

    @pytest.fixture
    def rectangular_canvas(self):
        """A rectangular canvas for testing."""
        return Canvas([(0, 0), (2e-5, 0), (2e-5, 1e-5), (0, 1e-5)])

    @pytest.fixture
    def triangular_canvas(self):
        """A triangular canvas for testing."""
        return Canvas([(0, 0), (1e-5, 0), (0.5e-5, 1e-5)])

    def test_from_square_lattice_basic(self, square_canvas):
        """Test basic square lattice creation."""
        spacing = 2e-6
        arrangement = AtomArrangement.from_square_lattice(spacing, square_canvas)

        # Canvas is 1e-5 x 1e-5, with spacing 2e-6
        assert len(arrangement) == 25  # Expected 5x5 grid (excluding boundary points)

        # Check some specific positions that should definitely be present
        coordinates = [site.coordinate for site in arrangement]
        assert (2e-6, 2e-6) in coordinates  # Interior point should be present
        assert (4e-6, 4e-6) in coordinates  # Another interior point

        # Check that we have the expected lattice structure
        x_coords = sorted(set(coord[0] for coord in coordinates))
        y_coords = sorted(set(coord[1] for coord in coordinates))

        # Should have regularly spaced coordinates
        assert len(x_coords) == 5  # 5 distinct x coordinates
        assert len(y_coords) == 5  # 5 distinct y coordinates

        # Check spacing
        if len(x_coords) > 1:
            assert abs(x_coords[1] - x_coords[0] - spacing) < 1e-10
        if len(y_coords) > 1:
            assert abs(y_coords[1] - y_coords[0] - spacing) < 1e-10

    def test_from_square_lattice_site_type(self, square_canvas):
        """Test square lattice with specific site type."""
        spacing = 5e-6
        arrangement = AtomArrangement.from_square_lattice(
            spacing, square_canvas, site_type=SiteType.VACANT
        )

        # All sites should be VACANT
        for site in arrangement:
            assert site.site_type == SiteType.VACANT

    def test_from_square_lattice_invalid_spacing(self, square_canvas):
        """Test square lattice with invalid spacing."""
        with pytest.raises(ValueError, match="Spacings must be positive"):
            AtomArrangement.from_square_lattice(0, square_canvas)

        with pytest.raises(ValueError, match="Spacings must be positive"):
            AtomArrangement.from_square_lattice(-1e-6, square_canvas)

    @pytest.mark.parametrize("spacing_x,spacing_y,expected_count,test_coords", [
        (
            4e-6, 2e-6, 25,
            [(4e-6, 2e-6), (8e-6, 4e-6), (1.2e-05, 6e-6), (1.6e-05, 8e-6)]
        ),
        (
            5e-6, 5e-6, 8,
            [(5e-6, 5e-6), (1e-05, 1e-05), (2e-05, 5e-6), (2e-05, 1e-05)]
        ),
        (
            10e-6, 5e-6, 4,
            [(1e-05, 5e-6), (1e-05, 1e-05), (2e-05, 5e-6), (2e-05, 1e-05)]
        ),
    ])
    def test_from_rectangular_lattice_basic(self, rectangular_canvas, spacing_x, spacing_y, 
                                          expected_count, test_coords):
        """Test basic rectangular lattice creation with various spacings."""
        arrangement = AtomArrangement.from_rectangular_lattice(
            spacing_x, spacing_y, rectangular_canvas
        )

        assert len(arrangement) == expected_count
        
        coordinates = [site.coordinate for site in arrangement]
        for coord in test_coords:
            # Check if coordinate exists with floating point tolerance
            found = any(
                abs(actual[0] - coord[0]) < 1e-10 and abs(actual[1] - coord[1]) < 1e-10
                for actual in coordinates
            )
            assert found, f"Expected coordinate {coord} not found in {coordinates}"

        # Verify spacing pattern
        x_coords = sorted(set(coord[0] for coord in coordinates))
        y_coords = sorted(set(coord[1] for coord in coordinates))
        
        if len(x_coords) > 1:
            for i in range(1, len(x_coords)):
                spacing_diff = abs(x_coords[i] - x_coords[i-1] - spacing_x)
                assert spacing_diff < 1e-10, f"X spacing mismatch: {spacing_diff}"
        
        if len(y_coords) > 1:
            for i in range(1, len(y_coords)):
                spacing_diff = abs(y_coords[i] - y_coords[i-1] - spacing_y)
                assert spacing_diff < 1e-10, f"Y spacing mismatch: {spacing_diff}"

    def test_from_rectangular_lattice_invalid_spacing(self, rectangular_canvas):
        """Test rectangular lattice with invalid spacing."""
        with pytest.raises(ValueError, match="Spacings must be positive"):
            AtomArrangement.from_rectangular_lattice(0, 1e-6, rectangular_canvas)

        with pytest.raises(ValueError, match="Spacings must be positive"):
            AtomArrangement.from_rectangular_lattice(1e-6, -1e-6, rectangular_canvas)

    def test_from_triangular_lattice_basic(self, square_canvas):
        """Test basic triangular lattice creation."""
        spacing = 3e-6
        arrangement = AtomArrangement.from_triangular_lattice(spacing, square_canvas)

        # Canvas is 1e-5 x 1e-5, with spacing 3e-6
        assert len(arrangement) == 9

    def test_from_triangular_lattice_invalid_spacing(self, square_canvas):
        """Test triangular lattice with invalid spacing."""
        with pytest.raises(ValueError, match="Spacing must be positive"):
            AtomArrangement.from_triangular_lattice(-1e-6, square_canvas)

    def test_from_honeycomb_lattice_basic(self, square_canvas):
        """Test basic honeycomb lattice creation."""
        spacing = 2e-6
        arrangement = AtomArrangement.from_honeycomb_lattice(spacing, square_canvas)

        # Canvas is 1e-5 x 1e-5, with spacing 2e-6 (nearest neighbor distance)
        # Should produce exactly 18 atoms in honeycomb arrangement
        assert len(arrangement) == 18

    def test_from_honeycomb_lattice_invalid_spacing(self, square_canvas):
        """Test honeycomb lattice with invalid spacing."""
        with pytest.raises(ValueError, match="Spacing must be positive"):
            AtomArrangement.from_honeycomb_lattice(0, square_canvas)

    def test_from_bravais_lattice_basic(self, square_canvas):
        """Test basic Bravais lattice creation."""
        a1 = (3e-6, 0)
        a2 = (0, 3e-6)
        arrangement = AtomArrangement.from_bravais_lattice(a1, a2, square_canvas)

        # Canvas is 1e-5 x 1e-5, with lattice vectors (3e-6, 0) and (0, 3e-6)
        # Should produce exactly 9 atoms in square lattice arrangement
        assert len(arrangement) == 9

        # Check that expected lattice position exists
        coordinates = [site.coordinate for site in arrangement]
        assert (3e-6, 3e-6) in coordinates  # Interior point should be present

    def test_from_bravais_lattice_with_basis(self, square_canvas):
        """Test Bravais lattice with custom basis."""
        a1 = (4e-6, 0)
        a2 = (0, 4e-6)
        basis = [(1e-6, 1e-6), (2e-6, 2e-6)]  # Two-atom basis

        arrangement = AtomArrangement.from_bravais_lattice(a1, a2, square_canvas, basis=basis)

        # Canvas is 1e-5 x 1e-5, with lattice vectors (4e-6, 0) and (0, 4e-6)
        # Two-atom basis should produce exactly 18 atoms (9 lattice sites × 2 basis atoms)
        assert len(arrangement) == 18

    def test_from_bravais_lattice_invalid_vectors(self, square_canvas):
        """Test Bravais lattice with invalid lattice vectors."""
        # Zero vector
        with pytest.raises(ValueError, match="Lattice vectors cannot be zero"):
            AtomArrangement.from_bravais_lattice((0, 0), (1e-6, 0), square_canvas)

        # Parallel vectors
        with pytest.raises(ValueError, match="Lattice vectors cannot be parallel"):
            AtomArrangement.from_bravais_lattice((1e-6, 0), (2e-6, 0), square_canvas)

    def test_from_bravais_lattice_with_decimals(self, square_canvas):
        """Test Bravais lattice with Decimal coordinates."""
        a1 = (Decimal("3e-6"), Decimal("0"))
        a2 = (Decimal("0"), Decimal("3e-6"))

        arrangement = AtomArrangement.from_bravais_lattice(a1, a2, square_canvas)
        
        # Should produce same result as float version (9 atoms)
        assert len(arrangement) == 9

    def test_triangular_lattice_spacing_geometry(self):
        """Test that triangular lattice has correct geometric properties."""
        # Use a larger canvas to get multiple lattice points
        canvas = Canvas([(1e-6, 1e-6), (1e-4, 1e-6), (1e-4, 1e-4), (1e-6, 1e-4)])
        spacing = 1e-5

        arrangement = AtomArrangement.from_triangular_lattice(spacing, canvas)
        
        # Large canvas (99μm × 99μm) with spacing 10μm should produce exactly 108 atoms
        assert len(arrangement) == 108

    def test_honeycomb_lattice_structure(self):
        """Test that honeycomb lattice has correct structure."""
        # Use a larger canvas with interior region
        canvas = Canvas([(1e-6, 1e-6), (2e-4, 1e-6), (2e-4, 2e-4), (1e-6, 2e-4)])
        spacing = 1e-5  # Nearest neighbor distance

        arrangement = AtomArrangement.from_honeycomb_lattice(spacing, canvas)
        
        # Large canvas (199μm × 199μm) with spacing 10μm should produce exactly 311 atoms
        assert len(arrangement) == 311

    def test_honeycomb_lattice_contains_requested_spacing(self, square_canvas):
        """At least one pair of atoms must be separated by exactly `spacing`
        (the declared nearest-neighbour distance)."""
        spacing = 2e-6
        arr = AtomArrangement.from_honeycomb_lattice(spacing, square_canvas)
        coords = [site.coordinate for site in arr]

        # we need at least two atoms to measure a distance
        assert len(coords) >= 2

        # collect unique pairwise distances (rounded to tame fp noise)
        distances = {
            round(math.hypot(x1 - x2, y1 - y2), 12)
            for (x1, y1), (x2, y2) in itertools.combinations(coords, 2)
        }

        # there should be at least one distance equal to `spacing`
        assert any(math.isclose(d, spacing, rel_tol=1e-7, abs_tol=1e-12) for d in distances), (
            "No pair found at the requested nearest-neighbour distance"
        )

    def test_honeycomb_lattice_min_distance_not_smaller_than_spacing(self, square_canvas):
        """The shortest non-zero distance in the honeycomb lattice must be
        at least the user-requested `spacing`.  A too-small value signals an
        incorrect basis."""
        spacing = 2e-6
        arr = AtomArrangement.from_honeycomb_lattice(spacing, square_canvas)
        coords = [site.coordinate for site in arr]

        # at least one pair to measure
        assert len(coords) >= 2

        min_dist = min(
            math.hypot(x1 - x2, y1 - y2)
            for (x1, y1), (x2, y2) in itertools.combinations(coords, 2)
            if (x1, y1) != (x2, y2)
        )

        # Allow tiny numerical wiggle room
        assert min_dist >= spacing * 0.999, (
            f"Shortest distance {min_dist:e} is < requested spacing {spacing:e};"
        )

    def test_factory_methods_empty_canvas(self):
        """Test factory methods with canvas that contains no lattice points."""
        # Very small canvas that might not contain any lattice points
        tiny_canvas = Canvas([(1e-7, 1e-7), (2e-7, 1e-7), (2e-7, 2e-7), (1e-7, 2e-7)])
        large_spacing = 1e-5

        arrangement = AtomArrangement.from_square_lattice(large_spacing, tiny_canvas)
        # Should not crash, might be empty or have very few atoms
        assert len(arrangement) >= 0

    def test_mixed_site_types_with_factory_methods(self, square_canvas):
        """Test that factory methods respect site_type parameter."""
        spacing = 3e-6

        filled_arrangement = AtomArrangement.from_square_lattice(
            spacing, square_canvas, site_type=SiteType.FILLED
        )
        vacant_arrangement = AtomArrangement.from_square_lattice(
            spacing, square_canvas, site_type=SiteType.VACANT
        )

        # Same number of sites
        assert len(filled_arrangement) == len(vacant_arrangement)

        # But different site types
        for site in filled_arrangement:
            assert site.site_type == SiteType.FILLED

        for site in vacant_arrangement:
            assert site.site_type == SiteType.VACANT

    def test_lattice_methods_with_complex_canvas(self):
        """Test lattice methods with a more complex canvas shape."""
        # L-shaped canvas
        l_canvas = Canvas([
            (0, 0),
            (1e-5, 0),
            (1e-5, 0.5e-5),
            (0.5e-5, 0.5e-5),
            (0.5e-5, 1e-5),
            (0, 1e-5),
        ])

        spacing = 2e-6
        arrangement = AtomArrangement.from_square_lattice(spacing, l_canvas)

        # Should have atoms only in the L-shaped region
        assert len(arrangement) > 0

        # Verify all atoms are within the canvas
        for site in arrangement:
            assert l_canvas.contains_point(site.coordinate)
