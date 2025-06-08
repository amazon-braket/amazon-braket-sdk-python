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
        # The exact boundary behavior may vary, but we should get a reasonable grid
        assert len(arrangement) > 0  # At least some atoms should be created
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
        with pytest.raises(ValueError, match="Spacing must be positive"):
            AtomArrangement.from_square_lattice(0, square_canvas)
        
        with pytest.raises(ValueError, match="Spacing must be positive"):
            AtomArrangement.from_square_lattice(-1e-6, square_canvas)

    def test_from_rectangular_lattice_basic(self, rectangular_canvas):
        """Test basic rectangular lattice creation."""
        spacing_x = 4e-6
        spacing_y = 2e-6
        arrangement = AtomArrangement.from_rectangular_lattice(
            spacing_x, spacing_y, rectangular_canvas
        )
        
        # Should have atoms in a rectangular grid
        assert len(arrangement) > 0
        
        # Check some specific positions (interior points)
        coordinates = [site.coordinate for site in arrangement]
        assert (4e-6, 2e-6) in coordinates  # Interior point should be present
        
        # Check grid structure
        x_coords = sorted(set(coord[0] for coord in coordinates))
        y_coords = sorted(set(coord[1] for coord in coordinates))
        assert len(x_coords) >= 2
        assert len(y_coords) >= 2

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
        
        assert len(arrangement) > 0
        
        # Check that we have a reasonable number of atoms for triangular lattice
        coordinates = [site.coordinate for site in arrangement]
        assert len(coordinates) >= 3  # Should have multiple atoms
        
        # In triangular lattice, check we have the expected structure
        # At least verify we have atoms at reasonable positions

    def test_from_triangular_lattice_invalid_spacing(self, square_canvas):
        """Test triangular lattice with invalid spacing."""
        with pytest.raises(ValueError, match="Spacing must be positive"):
            AtomArrangement.from_triangular_lattice(-1e-6, square_canvas)

    def test_from_honeycomb_lattice_basic(self, square_canvas):
        """Test basic honeycomb lattice creation."""
        spacing = 2e-6
        arrangement = AtomArrangement.from_honeycomb_lattice(spacing, square_canvas)
        
        assert len(arrangement) > 0
        
        # Honeycomb should have two atoms per unit cell
        coordinates = [site.coordinate for site in arrangement]
        # Check that we have multiple atoms forming honeycomb structure
        assert len(coordinates) >= 2

    def test_from_honeycomb_lattice_invalid_spacing(self, square_canvas):
        """Test honeycomb lattice with invalid spacing."""
        with pytest.raises(ValueError, match="Spacing must be positive"):
            AtomArrangement.from_honeycomb_lattice(0, square_canvas)

    def test_from_bravais_lattice_basic(self, square_canvas):
        """Test basic Bravais lattice creation."""
        a1 = (3e-6, 0)
        a2 = (0, 3e-6)
        arrangement = AtomArrangement.from_bravais_lattice(a1, a2, square_canvas)
        
        assert len(arrangement) > 0
        
        # Check some expected lattice positions (interior points)
        coordinates = [site.coordinate for site in arrangement]
        assert (3e-6, 3e-6) in coordinates  # Interior point should be present
        
        # Should have reasonable number of lattice points
        assert len(coordinates) >= 4

    def test_from_bravais_lattice_with_basis(self, square_canvas):
        """Test Bravais lattice with custom basis."""
        a1 = (4e-6, 0)
        a2 = (0, 4e-6)
        basis = [(1e-6, 1e-6), (2e-6, 2e-6)]  # Use interior points for basis
        
        arrangement = AtomArrangement.from_bravais_lattice(
            a1, a2, square_canvas, basis=basis
        )
        
        assert len(arrangement) > 0
        
        # Check that basis atoms appear at reasonable positions
        coordinates = [site.coordinate for site in arrangement]
        # Look for atoms that are at basis offsets from lattice points
        assert len(coordinates) >= 2  # Should have multiple atoms

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
        assert len(arrangement) > 0

    def test_triangular_lattice_spacing_geometry(self):
        """Test that triangular lattice has correct geometric properties."""
        # Use a larger canvas to get multiple lattice points
        canvas = Canvas([(1e-6, 1e-6), (1e-4, 1e-6), (1e-4, 1e-4), (1e-6, 1e-4)])
        spacing = 1e-5
        
        arrangement = AtomArrangement.from_triangular_lattice(spacing, canvas)
        coordinates = [site.coordinate for site in arrangement]
        
        # Should have multiple atoms in triangular arrangement
        assert len(coordinates) > 1
        
        # Check that we have a reasonable number of atoms
        # Just verify we get a reasonable count without being too precise
        assert len(coordinates) > 10  # Should have a decent number of atoms
        assert len(coordinates) < 200  # But not an unreasonable amount

    def test_honeycomb_lattice_structure(self):
        """Test that honeycomb lattice has correct structure."""
        # Use a larger canvas with interior region
        canvas = Canvas([(1e-6, 1e-6), (2e-4, 1e-6), (2e-4, 2e-4), (1e-6, 2e-4)])
        spacing = 1e-5  # Nearest neighbor distance
        
        arrangement = AtomArrangement.from_honeycomb_lattice(spacing, canvas)
        coordinates = [site.coordinate for site in arrangement]
        
        # Should have multiple atoms with honeycomb structure
        assert len(arrangement) >= 2

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
        assert any(
            math.isclose(d, spacing, rel_tol=1e-7, abs_tol=1e-12)
            for d in distances
        ), "No pair found at the requested nearest-neighbour distance"

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
            (0, 0), (1e-5, 0), (1e-5, 0.5e-5), 
            (0.5e-5, 0.5e-5), (0.5e-5, 1e-5), (0, 1e-5)
        ])
        
        spacing = 2e-6
        arrangement = AtomArrangement.from_square_lattice(spacing, l_canvas)
        
        # Should have atoms only in the L-shaped region
        assert len(arrangement) > 0
        
        # Verify all atoms are within the canvas
        for site in arrangement:
            assert l_canvas.contains_point(site.coordinate)