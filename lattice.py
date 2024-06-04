from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from numbers import Number
from typing import Union, List, Tuple

import numpy as np

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
        """Represents a set of coordinates that can be used as a register to an AnalogHamiltonianSimulation."""
        self._sites = []

    def add(self, coordinate: Union[tuple[Number, Number], np.ndarray], site_type: SiteType = SiteType.FILLED) -> "AtomArrangement":
        """Add a coordinate to the atom arrangement.

        Args:
            coordinate (Union[tuple[Number, Number], ndarray]): The coordinate of the atom (in meters).
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
            list[Number]: The list of coordinates at the given index.

        Example:
            To get a list of all x-coordinates: coordinate_list(0)
            To get a list of all y-coordinates: coordinate_list(1)
        """
        return [site.coordinate[coordinate_index] for site in self._sites]

    def __iter__(self) -> Iterator:
        return iter(self._sites)

    def __len__(self):
        return len(self._sites)

    def discretize(self, properties: "DiscretizationProperties") -> "AtomArrangement":
        """Creates a discretized version of the atom arrangement,
        rounding all site coordinates to the closest multiple of the resolution.
        The types of the sites are unchanged.

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

    @classmethod
    def from_decorated_bravais_lattice(
        cls,
        lattice_vectors: List[Tuple[float, float]],
        decoration_points: List[Tuple[float, float]],
        canvas_boundary_points: List[Tuple[float, float]]
    ) -> "AtomArrangement":
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

# Example usage
canvas_boundary_points = [(0, 0), (7.5e-5, 0), (0, 7.6e-5), (7.5e-5, 7.6e-5)]
canvas = AtomArrangement.from_honeycomb_lattice(4e-6, canvas_boundary_points)
