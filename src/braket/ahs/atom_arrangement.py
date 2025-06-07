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
from typing import TYPE_CHECKING

import numpy as np

from braket.ahs.discretization_types import DiscretizationError, DiscretizationProperties

if TYPE_CHECKING:
    from braket.ahs.canvas import Canvas


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
            coordinate (Union[tuple[Number, Number], ndarray]): The coordinate of the
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
        if spacing <= 0:
            raise ValueError("Spacing must be positive")

        arrangement = cls()
        (min_x, min_y), (max_x, max_y) = canvas.get_bounding_box()

        # Calculate starting points aligned to spacing grid from origin
        start_x = math.floor(min_x / spacing) * spacing
        start_y = math.floor(min_y / spacing) * spacing

        # Generate lattice points
        x = start_x
        while x <= max_x + spacing / 2:  # Add small buffer to avoid floating point issues
            y = start_y
            while y <= max_y + spacing / 2:
                point = (x, y)
                if canvas.contains_point(point):
                    arrangement.add(point, site_type)
                y += spacing
            x += spacing

        return arrangement

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

        arrangement = cls()
        (min_x, min_y), (max_x, max_y) = canvas.get_bounding_box()

        # Calculate starting points aligned to spacing grid from origin
        start_x = math.floor(min_x / spacing_x) * spacing_x
        start_y = math.floor(min_y / spacing_y) * spacing_y

        # Generate lattice points
        x = start_x
        while x <= max_x + spacing_x / 2:
            y = start_y
            while y <= max_y + spacing_y / 2:
                point = (x, y)
                if canvas.contains_point(point):
                    arrangement.add(point, site_type)
                y += spacing_y
            x += spacing_x

        return arrangement

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
        basis = [(0, 0), (spacing, 0)]

        return cls.from_bravais_lattice(a1, a2, canvas, basis=basis, site_type=site_type)

    @classmethod
    def from_bravais_lattice(
        cls,
        a1: tuple[Number, Number],
        a2: tuple[Number, Number],
        canvas: Canvas,
        basis: list[tuple[Number, Number]] = None,
        site_type: SiteType = SiteType.FILLED,
    ) -> AtomArrangement:
        """Create a general Bravais lattice arrangement within a canvas.

        Args:
            a1 (tuple[Number, Number]): First lattice vector (x, y) in meters.
            a2 (tuple[Number, Number]): Second lattice vector (x, y) in meters.
            canvas (Canvas): Canvas defining the boundary where atoms can be placed.
            basis (list[tuple[Number, Number]], optional): Basis vectors for decorated lattice.
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

        # Determine the range of lattice indices needed
        # This is a conservative estimate to ensure we cover the entire bounding box
        max_extent = max(abs(float(max_x - min_x)), abs(float(max_y - min_y)))
        max_lattice_extent = max(
            abs(float(a1[0])) + abs(float(a1[1])) + abs(float(a2[0])) + abs(float(a2[1])), 1e-12
        )
        max_indices = int(max_extent / max_lattice_extent) + 2

        # Generate lattice points
        for n1 in range(-max_indices, max_indices + 1):
            for n2 in range(-max_indices, max_indices + 1):
                # Calculate lattice site position
                lattice_x = float(n1) * float(a1[0]) + float(n2) * float(a2[0])
                lattice_y = float(n1) * float(a1[1]) + float(n2) * float(a2[1])

                # Add all basis atoms at this lattice site
                for basis_x, basis_y in basis:
                    point = (lattice_x + float(basis_x), lattice_y + float(basis_y))
                    
                    # Check if point is within canvas
                    if canvas.contains_point(point):
                        arrangement.add(point, site_type)

        return arrangement
