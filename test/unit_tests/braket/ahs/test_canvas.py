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

from braket.ahs.canvas import Canvas


class TestCanvas:
    def test_init_valid_square(self):
        """Test Canvas initialization with a valid square."""
        boundary_points = [(0, 0), (1, 0), (1, 1), (0, 1)]
        canvas = Canvas(boundary_points)
        assert canvas.boundary_points == boundary_points

    def test_init_valid_triangle(self):
        """Test Canvas initialization with a valid triangle."""
        boundary_points = [(0, 0), (1, 0), (0.5, 1)]
        canvas = Canvas(boundary_points)
        assert canvas.boundary_points == boundary_points

    def test_init_invalid_too_few_points(self):
        """Test Canvas initialization with too few points."""
        with pytest.raises(ValueError, match="Canvas must have at least 3 boundary points"):
            Canvas([(0, 0), (1, 0)])

    def test_init_invalid_point_format(self):
        """Test Canvas initialization with invalid point format."""
        with pytest.raises(TypeError, match="Boundary point 1 must be a tuple/list of length 2"):
            Canvas([(0, 0), (1,), (0.5, 1)])

    def test_init_invalid_coordinate_type(self):
        """Test Canvas initialization with invalid coordinate type."""
        with pytest.raises(TypeError, match="Coordinate 0 of boundary point 1 must be a number"):
            Canvas([(0, 0), ("invalid", 0), (0.5, 1)])

    def test_init_with_decimals(self):
        """Test Canvas initialization with Decimal coordinates."""
        boundary_points = [
            (Decimal("0"), Decimal("0")),
            (Decimal("1"), Decimal("0")),
            (Decimal("0.5"), Decimal("1")),
        ]
        canvas = Canvas(boundary_points)
        assert canvas.boundary_points == boundary_points

    def test_contains_point_square_inside(self):
        """Test point containment for points inside a square."""
        canvas = Canvas([(0, 0), (2, 0), (2, 2), (0, 2)])

        # Points clearly inside
        assert canvas.contains_point((1, 1))
        assert canvas.contains_point((0.5, 0.5))
        assert canvas.contains_point((1.5, 1.5))

    def test_contains_point_square_outside(self):
        """Test point containment for points outside a square."""
        canvas = Canvas([(0, 0), (2, 0), (2, 2), (0, 2)])

        # Points clearly outside
        assert not canvas.contains_point((-1, 1))
        assert not canvas.contains_point((3, 1))
        assert not canvas.contains_point((1, -1))
        assert not canvas.contains_point((1, 3))

    def test_contains_point_square_on_boundary(self):
        """Test point containment for points on boundary of a square."""
        canvas = Canvas([(0, 0), (2, 0), (2, 2), (0, 2)])

        # Points on boundary (ray casting may vary for boundary points)
        # The exact behavior on boundary is implementation-dependent
        # but should be consistent
        boundary_result = canvas.contains_point((0, 1))
        assert isinstance(boundary_result, bool)

    def test_contains_point_triangle(self):
        """Test point containment for a triangle."""
        canvas = Canvas([(0, 0), (2, 0), (1, 2)])

        # Point inside triangle
        assert canvas.contains_point((1, 0.5))

        # Points outside triangle
        assert not canvas.contains_point((-1, 0))
        assert not canvas.contains_point((3, 0))
        assert not canvas.contains_point((1, 3))

    def test_contains_point_complex_polygon(self):
        """Test point containment for a more complex polygon."""
        # L-shaped polygon
        canvas = Canvas([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)])

        # Points inside L-shape
        assert canvas.contains_point((0.5, 0.5))
        assert canvas.contains_point((1.5, 0.5))
        assert canvas.contains_point((0.5, 1.5))

        # Point in the "missing" part of the L
        assert not canvas.contains_point((1.5, 1.5))

    def test_get_bounding_box_square(self):
        """Test bounding box calculation for a square."""
        canvas = Canvas([(1, 1), (3, 1), (3, 3), (1, 3)])
        (min_x, min_y), (max_x, max_y) = canvas.get_bounding_box()

        assert min_x == 1
        assert min_y == 1
        assert max_x == 3
        assert max_y == 3

    def test_get_bounding_box_triangle(self):
        """Test bounding box calculation for a triangle."""
        canvas = Canvas([(-1, 0), (2, 0), (0.5, 3)])
        (min_x, min_y), (max_x, max_y) = canvas.get_bounding_box()

        assert min_x == -1
        assert min_y == 0
        assert max_x == 2
        assert max_y == 3

    def test_get_bounding_box_with_decimals(self):
        """Test bounding box calculation with Decimal coordinates."""
        canvas = Canvas([
            (Decimal("-1.5"), Decimal("0.5")),
            (Decimal("2.5"), Decimal("0.5")),
            (Decimal("0.5"), Decimal("3.5")),
        ])
        (min_x, min_y), (max_x, max_y) = canvas.get_bounding_box()

        assert min_x == Decimal("-1.5")
        assert min_y == Decimal("0.5")
        assert max_x == Decimal("2.5")
        assert max_y == Decimal("3.5")

    def test_edge_cases_degenerate_triangle(self):
        """Test edge case with degenerate triangle (collinear points)."""
        # Points are collinear (degenerate triangle)
        canvas = Canvas([(0, 0), (1, 0), (2, 0)])

        # Point "inside" the degenerate triangle
        result = canvas.contains_point((1, 0))
        assert isinstance(result, bool)  # Should not crash

    def test_edge_cases_duplicate_points(self):
        """Test edge case with duplicate boundary points."""
        canvas = Canvas([(0, 0), (1, 0), (1, 0), (0, 1)])

        # Should not crash and should work reasonably
        result = canvas.contains_point((0.3, 0.3))
        assert isinstance(result, bool)

    def test_vertical_edge_ray_casting(self):
        """Test vertical edge case to ensure complete coverage."""
        canvas = Canvas([(0, 0), (1, 0), (1, 1), (0, 1)])

        # Test point that will cause ray casting to interact with vertical edge
        assert canvas.contains_point((0.5, 0.5))

        # Test point outside that interacts with vertical edge
        assert not canvas.contains_point((-0.5, 0.5))
