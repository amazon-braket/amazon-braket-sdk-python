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

from __future__ import annotations

from numbers import Number


class Canvas:
    """Defines a region where atoms can be placed using boundary points.

    A Canvas represents a polygonal region in 2D space defined by boundary points.
    It is used by factory methods to determine which lattice sites should contain atoms.
    """

    def __init__(self, boundary_points: list[tuple[Number, Number]]):
        """Initialize a Canvas with boundary points.

        Args:
            boundary_points (list[tuple[Number, Number]]): List of (x, y) coordinates
                defining the polygon boundary. Must have at least 3 points.

        Raises:
            ValueError: If fewer than 3 boundary points are provided.
            TypeError: If boundary points are not properly formatted.
        """
        self._validate_boundary_points(boundary_points)
        self.boundary_points = boundary_points

    def _validate_boundary_points(self, boundary_points: list[tuple[Number, Number]]) -> None:
        """Validate the boundary points."""
        if len(boundary_points) < 3:
            raise ValueError("Canvas must have at least 3 boundary points")

        for i, point in enumerate(boundary_points):
            if not isinstance(point, tuple | list) or len(point) != 2:
                raise TypeError(f"Boundary point {i} must be a tuple/list of length 2")

            for j, coord in enumerate(point):
                if not isinstance(coord, Number):
                    raise TypeError(
                        f"Coordinate {j} of boundary point {i} must be a number, got {type(coord)}"
                    )

    def contains_point(self, point: tuple[Number, Number]) -> bool:
        """Check if a point is inside the canvas using ray casting algorithm.

        Args:
            point (tuple[Number, Number]): The (x, y) coordinate to test.

        Returns:
            bool: True if the point is inside the canvas, False otherwise.
        """
        x, y = point
        n = len(self.boundary_points)
        inside = False

        p1x, p1y = self.boundary_points[0]
        for i in range(1, n + 1):
            p2x, p2y = self.boundary_points[i % n]

            # Skip horizontal edges
            if p1y == p2y:
                p1x, p1y = p2x, p2y
                continue

            if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def get_bounding_box(self) -> tuple[tuple[Number, Number], tuple[Number, Number]]:
        """Get the bounding box of the canvas.

        Returns:
            tuple[tuple[Number, Number], tuple[Number, Number]]:
                ((min_x, min_y), (max_x, max_y)) coordinates of the bounding box.
        """
        x_coords = [point[0] for point in self.boundary_points]
        y_coords = [point[1] for point in self.boundary_points]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        return ((min_x, min_y), (max_x, max_y))
