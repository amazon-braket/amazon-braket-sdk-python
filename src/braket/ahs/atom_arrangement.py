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

from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from numbers import Number
from typing import Union

import numpy as np

from braket.ahs.discretization_types import DiscretizationError, DiscretizationProperties
from typing import Union, Tuple, List, Iterator
from dataclasses import dataclass
import numpy as np
from decimal import Decimal
from enum import Enum
from numbers import Number


# Define SiteType enum
class SiteType(Enum):
    FILLED = "filled"
    VACANT = "vacant"


@dataclass
class AtomArrangementItem:
    """Represents an item (coordinate and metadata) in an atom arrangement."""
    coordinate: Tuple[Number, Number]
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
        coordinate: Union[Tuple[Number, Number], np.ndarray],
        site_type: SiteType = SiteType.FILLED,
    ) -> "AtomArrangement":
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

    def coordinate_list(self, coordinate_index: Number) -> List[Number]:
        """Returns all the coordinates at the given index.
        Args:
            coordinate_index (Number): The index to get for each coordinate.
        Returns:
            List[Number]: The list of coordinates at the given index.
        Example:
            To get a list of all x-coordinates: coordinate_list(0)
            To get a list of all y-coordinates: coordinate_list(1)
        """
        return [site.coordinate[coordinate_index] for site in self._sites]

    def __iter__(self) -> Iterator:
        return iter(self._sites)

    def __len__(self):
        return len(self._sites)

    def discretize(self, properties: 'DiscretizationProperties') -> "AtomArrangement":
        """Creates a discretized version of the atom arrangement, rounding all site coordinates to the closest multiple of the resolution. The types of the sites are unchanged.
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
            return discretized_arrangement
        except Exception as e:
            raise DiscretizationError(f"Failed to discretize register {e}") from e

# Updated 
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
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from numbers import Number
from typing import Union, Tuple, List
import numpy as np
from shapely.geometry import Point, Polygon

# Define SiteType enum
class SiteType(Enum):
    VACANT = "Vacant"
    FILLED = "Filled"

@dataclass
class AtomArrangementItem:
    """Represents an item (coordinate and metadata) in an atom arrangement."""
    coordinate: Tuple[Number, Number]
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
        """Represents a set of coordinates that can be used as a register to an AnalogHamiltonianSimulation."""
        self._sites = []

    def add(self, coordinate: Union[Tuple[Number, Number], np.ndarray], site_type: SiteType = SiteType.FILLED) -> "AtomArrangement":
        """Add a coordinate to the atom arrangement.
        Args:
            coordinate (Union[tuple[Number, Number], ndarray]): The coordinate of the atom (in meters).
            site_type (SiteType): The type of site. Optional. Default is FILLED.
        Returns:
            AtomArrangement: returns self (to allow for chaining).
        """
        self._sites.append(AtomArrangementItem(tuple(coordinate), site_type))
        return self

    def coordinate_list(self, coordinate_index: Number) -> List[Number]:
        """Returns all the coordinates at the given index.
        Args:
            coordinate_index (Number): The index to get for each coordinate.
        Returns:
            List[Number]: The list of coordinates at the given index.
        Example:
            To get a list of all x-coordinates: coordinate_list(0)
            To get a list of all y-coordinates: coordinate_list(1)
        """
        return [site.coordinate[coordinate_index] for site in self._sites]

    def __iter__(self) -> Iterator:
        return iter(self._sites)

    def __len__(self):
        return len(self._sites)

    def discretize(self, properties: 'DiscretizationProperties') -> "AtomArrangement":
        """Creates a discretized version of the atom arrangement, rounding all site coordinates to the closest multiple of the resolution. The types of the sites are unchanged.
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
            return discretized_arrangement
        except Exception as e:
            raise DiscretizationError(f"Failed to discretize register {e}") from e

    # Factory methods for lattice structures
    @classmethod
    def from_square_lattice(cls, lattice_constant: float, canvas_boundary_points: List[Tuple[float, float]]) -> "AtomArrangement":
        """Create an atom arrangement with a square lattice."""
        arrangement = cls()
        x_min, y_min = canvas_boundary_points[0]
        x_max, y_max = canvas_boundary_points[2]
        x_range = np.arange(x_min, x_max, lattice_constant)
        y_range = np.arange(y_min, y_max, lattice_constant)
        for x in x_range:
            for y in y_range:
                arrangement.add((x, y))
        return arrangement

    @classmethod
    def from_rectangular_lattice(cls, dx: float, dy: float, canvas_boundary_points: List[Tuple[float, float]]) -> "AtomArrangement":
        """Create an atom arrangement with a rectangular lattice."""
        arrangement = cls()
        x_min, y_min = canvas_boundary_points[0]
        x_max, y_max = canvas_boundary_points[2]
        for x in np.arange(x_min, x_max, dx):
            for y in np.arange(y_min, y_max, dy):
                arrangement.add((x, y))
        return arrangement

    @classmethod
    def from_decorated_bravais_lattice(cls, lattice_vectors: List[Tuple[float, float]], decoration_points: List[Tuple[float, float]], canvas_boundary_points: List[Tuple[float, float]]) -> "AtomArrangement":
        arrangement = cls()
        vec_a, vec_b = np.array(lattice_vectors[0]), np.array(lattice_vectors[1])
        x_min, y_min = canvas_boundary_points[0]
        x_max, y_max = canvas_boundary_points[2]
        i = 0
        while (origin := i * vec_a)[0] < x_max:
            j = 0
            while (point := origin + j * vec_b)[1] < y_max:
                if x_min <= point[0] <= x_max and y_min <= point[1] <= y_max:
                    for dp in decoration_points:
                        decorated_point = point + np.array(dp)
                        if x_min <= decorated_point[0] <= x_max and y_min <= decorated_point[1] <= y_max:
                            arrangement.add(tuple(decorated_point))
                j += 1
            i += 1
        return arrangement

    @classmethod
    def from_honeycomb_lattice(cls, lattice_constant: float, canvas_boundary_points: List[Tuple[float, float]]) -> "AtomArrangement":
        a1 = (lattice_constant, 0)
        a2 = (lattice_constant / 2, lattice_constant * np.sqrt(3) / 2)
        decoration_points = [(0, 0), (lattice_constant / 2, lattice_constant * np.sqrt(3) / 6)]
        return cls.from_decorated_bravais_lattice([a1, a2], decoration_points, canvas_boundary_points)

    @classmethod
    def from_bravais_lattice(cls, lattice_vectors: List[Tuple[float, float]], canvas_boundary_points: List[Tuple[float, float]]) -> "AtomArrangement":
        return cls.from_decorated_bravais_lattice(lattice_vectors, [(0, 0)], canvas_boundary_points)

@dataclass
class LatticeGeometry:
    positionResolution: Decimal

@dataclass
class DiscretizationProperties:
    lattice: LatticeGeometry

class DiscretizationError(Exception):
    pass

# RectangularCanvas class
class RectangularCanvas:
    def __init__(self, bottom_left: Tuple[float, float], top_right: Tuple[float, float]):
        self.bottom_left = bottom_left
        self.top_right = top_right

    def is_within(self, point: Tuple[float, float]) -> bool:
        x_min, y_min = self.bottom_left
        x_max, y_max = self.top_right
        x, y = point
        return x_min <= x <= x_max and y_min <= y <= y_max

# Example usage
if __name__ == "__main__":
    canvas_boundary_points = [(0, 0), (7.5e-5, 0), (7.5e-5, 7.5e-5), (0, 7.5e-5)]

    # Create lattice structures
    square_lattice = AtomArrangement.from_square_lattice(4e-6, canvas_boundary_points)
    rectangular_lattice = AtomArrangement.from_rectangular_lattice(3e-6, 2e-6, canvas_boundary_points)
    decorated_bravais_lattice = AtomArrangement.from_decorated_bravais_lattice([(4e-6, 0), (0, 4e-6)], [(1e-6, 1e-6)], canvas_boundary_points)
    honeycomb_lattice = AtomArrangement.from_honeycomb_lattice(4e-6, canvas_boundary_points)
    bravais_lattice = AtomArrangement.from_bravais_lattice([(4e-6, 0), (0, 4e-6)], canvas_boundary_points)

    # Validation function
    def validate_lattice(arrangement, lattice_type):
        """Validate the lattice structure."""
        num_sites = len(arrangement)
        min_distance = None
        for i, atom1 in enumerate(arrangement):
            for j, atom2 in enumerate(arrangement):
                if i != j:
                    distance = np.linalg.norm(np.array(atom1.coordinate) - np.array(atom2.coordinate))
                    if min_distance is None or distance < min_distance:
                        min_distance = distance
        print(f"Lattice Type: {lattice_type}")
        print(f"Number of lattice points: {num_sites}")
        print(f"Minimum distance between lattice points: {min_distance:.2e} meters")
        print("-" * 40)

    # Validate lattice structures
    validate_lattice(square_lattice, "Square Lattice")
    validate_lattice(rectangular_lattice, "Rectangular Lattice")
    validate_lattice(decorated_bravais_lattice, "Decorated Bravais Lattice")
    validate_lattice(honeycomb_lattice, "Honeycomb Lattice")
    validate_lattice(bravais_lattice, "Bravais Lattice")
