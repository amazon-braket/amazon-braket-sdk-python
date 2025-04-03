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

import numpy as np

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
