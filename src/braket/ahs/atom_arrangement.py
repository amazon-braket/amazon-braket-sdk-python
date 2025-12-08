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

import math
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from numbers import Number

import numpy as np

from braket.ahs.canvas import Canvas
from braket.ahs.discretization_types import DiscretizationError, DiscretizationProperties


class SiteType(Enum):
    VACANT = "Vacant"
    FILLED = "Filled"


@dataclass
class AtomArrangementItem:
    """Represents an item (coordinate and metadata) in an atom arrangement."""

    coordinate: tuple[Number, Number]
    site_type: SiteType

    def _validate_coordinate(self) -> None:
        if len(self.coordinate) != 2:
            raise ValueError(f"{self.coordinate} must be of length 2")
        for idx, num in enumerate(self.coordinate):
            if not isinstance(num, Number):
                raise TypeError(f"{num} at position {idx} must be a number")

    def _validate_site_type(self) -> None:
        allowed_site_types = {SiteType.FILLED, SiteType.VACANT}
        if self.site_type not in allowed_site_types:
            raise ValueError(f"{self.site_type} must be one of {allowed_site_types}")

    def __post_init__(self) -> None:
        self._validate_coordinate()
        self._validate_site_type()


class AtomArrangement:
    def __init__(self):
        """Represents a set of coordinates that can be used as a register to an
        AnalogHamiltonianSimulation.
        """
        self._sites = []

    def add(
        self,
        coordinate: tuple[Number, Number] | np.ndarray,
        site_type: SiteType = SiteType.FILLED,
    ) -> AtomArrangement:
        """Add a coordinate to the atom arrangement.

        Args:
            coordinate (tuple[Number, Number] | np.ndarray): The coordinate of the
                atom (in meters). The coordinates can be a numpy array of shape (2,)
                or a tuple of int, float, Decimal
            site_type (SiteType): The type of site. Optional. Default is FILLED.

        Returns:
            AtomArrangement: returns self (to allow for chaining).
        """
        self._sites.append(AtomArrangementItem(tuple(coordinate), site_type))
        return self

    def coordinate_list(self, coordinate_index: Number) -> list[Number]:
        """Returns all the coordinates at the given index.

        Args:
            coordinate_index (Number): The index to get for each coordinate.

        Returns:
            list[Number]:The list of coordinates at the given index.

        Example:
            To get a list of all x-coordinates: coordinate_list(0)
            To get a list of all y-coordinates: coordinate_list(1)
        """
        return [site.coordinate[coordinate_index] for site in self._sites]

    def __iter__(self) -> Iterator:
        return self._sites.__iter__()

    def __len__(self):
        return self._sites.__len__()

    def discretize(self, properties: DiscretizationProperties) -> AtomArrangement:
        """Creates a discretized version of the atom arrangement,
        rounding all site coordinates to the closest multiple of the
        resolution. The types of the sites are unchanged.

        Args:
            properties (DiscretizationProperties): Capabilities of a device that represent the
                resolution with which the device can implement the parameters.

        Raises:
            DiscretizationError: If unable to discretize the program.

        Returns:
            AtomArrangement: A new discretized atom arrangement.
        """
        try:
            position_res = properties.lattice.geometry.positionResolution
            discretized_arrangement = AtomArrangement()
            for site in self._sites:
                new_coordinates = tuple(
                    round(Decimal(c) / position_res) * position_res for c in site.coordinate
                )
                discretized_arrangement.add(new_coordinates, site.site_type)
        except Exception as e:
            raise DiscretizationError(f"Failed to discretize register {e}") from e
        else:
            return discretized_arrangement

    @classmethod
    def from_square_lattice(
        cls,
        spacing: Number,
        canvas: Canvas,
        site_type: SiteType = SiteType.FILLED,
    ) -> AtomArrangement:
        """Create a square lattice arrangement within a canvas.

        Args:
            spacing (Number): Distance between adjacent atoms in meters.
            canvas (Canvas): Canvas defining the boundary where atoms can be placed.
            site_type (SiteType): The type of sites to create. Default is FILLED.

        Returns:
            AtomArrangement: A new atom arrangement with atoms placed in a square lattice.

        Raises:
            ValueError: If spacing is not positive.
        """
        return cls.from_rectangular_lattice(spacing, spacing, canvas, site_type)

    @classmethod
    def from_rectangular_lattice(
        cls,
        spacing_x: Number,
        spacing_y: Number,
        canvas: Canvas,
        site_type: SiteType = SiteType.FILLED,
    ) -> AtomArrangement:
        """Create a rectangular lattice arrangement within a canvas.

        Args:
            spacing_x (Number): Distance between adjacent atoms in x direction in meters.
            spacing_y (Number): Distance between adjacent atoms in y direction in meters.
            canvas (Canvas): Canvas defining the boundary where atoms can be placed.
            site_type (SiteType): The type of sites to create. Default is FILLED.

        Returns:
            AtomArrangement: A new atom arrangement with atoms placed in a rectangular lattice.

        Raises:
            ValueError: If either spacing is not positive.
        """
        if spacing_x <= 0 or spacing_y <= 0:
            raise ValueError("Spacings must be positive")

        # Rectangular lattice vectors
        a1 = (spacing_x, 0)
        a2 = (0, spacing_y)

        return cls.from_bravais_lattice(a1, a2, canvas, site_type=site_type)

    @classmethod
    def from_triangular_lattice(
        cls,
        spacing: Number,
        canvas: Canvas,
        site_type: SiteType = SiteType.FILLED,
    ) -> AtomArrangement:
        """Create a triangular lattice arrangement within a canvas.

        A triangular lattice has the same spacing between all nearest neighbors.
        The lattice vectors are (spacing, 0) and (spacing/2, spacing*sqrt(3)/2).

        Args:
            spacing (Number): Distance between nearest neighbor atoms in meters.
            canvas (Canvas): Canvas defining the boundary where atoms can be placed.
            site_type (SiteType): The type of sites to create. Default is FILLED.

        Returns:
            AtomArrangement: A new atom arrangement with atoms placed in a triangular lattice.

        Raises:
            ValueError: If spacing is not positive.
        """
        if spacing <= 0:
            raise ValueError("Spacing must be positive")

        # Triangular lattice vectors
        a1 = (spacing, 0)
        a2 = (spacing / 2, spacing * math.sqrt(3) / 2)

        return cls.from_bravais_lattice(a1, a2, canvas, site_type=site_type)

    @classmethod
    def from_honeycomb_lattice(
        cls,
        spacing: Number,
        canvas: Canvas,
        site_type: SiteType = SiteType.FILLED,
    ) -> AtomArrangement:
        """Create a honeycomb lattice arrangement within a canvas.

        A honeycomb lattice is a triangular Bravais lattice with a two-atom basis.
        The spacing parameter refers to the nearest neighbor distance.

        Args:
            spacing (Number): Distance between nearest neighbor atoms in meters.
            canvas (Canvas): Canvas defining the boundary where atoms can be placed.
            site_type (SiteType): The type of sites to create. Default is FILLED.

        Returns:
            AtomArrangement: A new atom arrangement with atoms placed in a honeycomb lattice.

        Raises:
            ValueError: If spacing is not positive.
        """
        if spacing <= 0:
            raise ValueError("Spacing must be positive")

        # Honeycomb is triangular lattice with 2-atom basis
        # Lattice parameter is sqrt(3) times the nearest neighbor distance
        lattice_spacing = spacing * math.sqrt(3)

        # Triangular lattice vectors
        a1 = (lattice_spacing, 0)
        a2 = (lattice_spacing / 2, lattice_spacing * math.sqrt(3) / 2)

        # Two-atom basis
        basis = [(0, 0), (a1[0] / 3 + a2[0] / 3, a1[1] / 3 + a2[1] / 3)]

        return cls.from_bravais_lattice(a1, a2, canvas, basis=basis, site_type=site_type)

    @classmethod
    def _calculate_lattice_bounds(
        cls,
        a1: tuple[Number, Number],
        a2: tuple[Number, Number],
        canvas_bounds: tuple[tuple[Number, Number], tuple[Number, Number]],
        basis: list[tuple[Number, Number]] | None = None,
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """Calculate the range of lattice indices needed to cover canvas bounds.

        Uses linear algebra to find the minimal bounding box in lattice coordinates
        that covers the entire canvas bounding box, accounting for basis offsets.

        Args:
            a1: First lattice vector (x, y)
            a2: Second lattice vector (x, y)
            canvas_bounds: ((min_x, min_y), (max_x, max_y))
            basis: List of basis vectors to account for in bounds calculation

        Returns:
            ((n1_min, n1_max), (n2_min, n2_max)): Range of lattice indices
        """
        if basis is None:
            basis = [(0, 0)]

        (min_x, min_y), (max_x, max_y) = canvas_bounds

        # Cache float conversions for performance
        a1_x, a1_y = float(a1[0]), float(a1[1])
        a2_x, a2_y = float(a2[0]), float(a2[1])

        # Calculate determinant with error checking
        det = a1_x * a2_y - a1_y * a2_x
        if abs(det) < 1e-12:
            raise ValueError(f"Lattice vectors are too close to parallel (det={det})")

        # Inverse matrix: [[a2_y, -a2_x], [-a1_y, a1_x]] / det
        inv_00, inv_01 = a2_y / det, -a2_x / det
        inv_10, inv_11 = -a1_y / det, a1_x / det

        # Canvas corners in real space, expanded with basis offsets
        base_corners = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
        corners = list(base_corners)  # Start with base corners

        # Add corners shifted by each basis vector (both positive and negative)
        for basis_x, basis_y in basis:
            if basis_x != 0 or basis_y != 0:  # Skip origin basis
                basis_x_f, basis_y_f = float(basis_x), float(basis_y)
                corners.extend([
                    (corner_x + basis_x_f, corner_y + basis_y_f)
                    for corner_x, corner_y in base_corners
                ])
                corners.extend([
                    (corner_x - basis_x_f, corner_y - basis_y_f)
                    for corner_x, corner_y in base_corners
                ])

        # Transform all points to lattice coordinates
        n1_values = []
        n2_values = []

        for x, y in corners:
            n1 = inv_00 * x + inv_01 * y
            n2 = inv_10 * x + inv_11 * y
            n1_values.append(n1)
            n2_values.append(n2)

        # margin calculation for lattice bounds
        lattice_magnitudes = [math.sqrt(a1_x**2 + a1_y**2), math.sqrt(a2_x**2 + a2_y**2)]
        min_lattice_mag = min(lattice_magnitudes)

        if basis:
            max_basis_mag = max(math.sqrt(float(bx) ** 2 + float(by) ** 2) for bx, by in basis)
            margin = max(2, math.ceil(max_basis_mag / min_lattice_mag) + 1)
        else:
            margin = 2

        # Convert to integer bounds
        n1_min = math.floor(min(n1_values)) - margin
        n1_max = math.ceil(max(n1_values)) + margin
        n2_min = math.floor(min(n2_values)) - margin
        n2_max = math.ceil(max(n2_values)) + margin

        return (n1_min, n1_max), (n2_min, n2_max)

    @classmethod
    def from_bravais_lattice(
        cls,
        a1: tuple[Number, Number],
        a2: tuple[Number, Number],
        canvas: Canvas,
        basis: list[tuple[Number, Number]] | None = None,
        site_type: SiteType = SiteType.FILLED,
    ) -> AtomArrangement:
        """Create a general Bravais lattice arrangement within a canvas.

        Args:
            a1 (tuple[Number, Number]): First lattice vector (x, y) in meters.
            a2 (tuple[Number, Number]): Second lattice vector (x, y) in meters.
            canvas (Canvas): Canvas defining the boundary where atoms can be placed.
            basis (list[tuple[Number, Number]] | None): Basis vectors for decorated lattice.
                If None, uses a single atom at (0, 0). Default is None.
            site_type (SiteType): The type of sites to create. Default is FILLED.

        Returns:
            AtomArrangement: A new atom arrangement with atoms placed in a Bravais lattice.

        Raises:
            ValueError: If lattice vectors are parallel or zero.
        """
        # Validate lattice vectors
        if a1 == (0, 0) or a2 == (0, 0):
            raise ValueError("Lattice vectors cannot be zero")

        # Check if vectors are parallel (cross product should be non-zero)
        cross_product = a1[0] * a2[1] - a1[1] * a2[0]
        if abs(cross_product) < 1e-12:
            raise ValueError("Lattice vectors cannot be parallel")

        if basis is None:
            basis = [(0, 0)]

        arrangement = cls()
        (min_x, min_y), (max_x, max_y) = canvas.get_bounding_box()

        # Calculate lattice bounds using linear algebra approach
        (n1_min, n1_max), (n2_min, n2_max) = cls._calculate_lattice_bounds(
            a1, a2, ((min_x, min_y), (max_x, max_y)), basis
        )

        # Cache float conversions
        a1_x, a1_y = float(a1[0]), float(a1[1])
        a2_x, a2_y = float(a2[0]), float(a2[1])
        basis_float = [(float(bx), float(by)) for bx, by in basis]

        # Generate lattice points
        for n1 in range(n1_min, n1_max + 1):
            for n2 in range(n2_min, n2_max + 1):
                # Calculate lattice site position
                lattice_x = n1 * a1_x + n2 * a2_x
                lattice_y = n1 * a1_y + n2 * a2_y

                # Add all basis atoms at this lattice site
                for basis_x, basis_y in basis_float:
                    point = (lattice_x + basis_x, lattice_y + basis_y)

                    # Check if point is within canvas
                    if canvas.contains_point(point):
                        arrangement.add(point, site_type)

        return arrangement
