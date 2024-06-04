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

    # Factory methods for lattice structures
    @classmethod
    def from_square_lattice(
        cls, lattice_constant: float, canvas_boundary_points: List[Tuple[float, float]]
    ) -> "AtomArrangement":
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
    def from_rectangular_lattice(
        cls, dx: float, dy: float, canvas_boundary_points: List[Tuple[float, float]]
    ) -> "AtomArrangement":
        """Create an atom arrangement with a rectangular lattice."""
        arrangement = cls()
        x_min, y_min = canvas_boundary_points[0]
        x_max, y_max = canvas_boundary_points[2]
        for x in np.arange(x_min, x_max, dx):
            for y in np.arange(y_min, y_max, dy):
                arrangement.add((x, y))
        return arrangement

# Define DiscretizationProperties and DiscretizationError for completeness
@dataclass
class LatticeGeometry:
    positionResolution: Decimal

@dataclass
class DiscretizationProperties:
    lattice: LatticeGeometry

class DiscretizationError(Exception):
    pass

# Example usage
canvas_boundary_points = [(0, 0), (7.5e-5, 0), (0, 7.5e-5), (7.5e-5, 7.5e-5)]
canvas = AtomArrangement.from_square_lattice(4e-6, canvas_boundary_points)

