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

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from numbers import Number
from typing import Iterator, List, Tuple

from braket.ahs.discretization_types import DiscretizationError, DiscretizationProperties


class SiteType(Enum):
    VACANT = "Vacant"
    FILLED = "Filled"


@dataclass
class AtomArrangementItem:
    coordinate: Tuple[Number, Number]
    site_type: SiteType


class AtomArrangement:
    def __init__(self):
        """Represents a set of coordinates that can be used as a register to an
        AnalogHamiltonianSimulation.
        """
        self._sites = []

    def add(
        self, coord: Tuple[Number, Number], site_type: SiteType = SiteType.FILLED
    ) -> AtomArrangement:
        """Add a coordinate to the atom arrangement.

        Args:
            coord (Tuple[Number, Number]): The coordinate of the atom (in meters). The coordinates
                can be int, float or Decimal.
            site_type (SiteType): The type of site. Optional. Default is FILLED.
        Returns:
            AtomArrangement: returns self (to allow for chaining).
        """
        self._sites.append(AtomArrangementItem(tuple(coord), site_type))
        return self

    def coordinate_list(self, coordinate_index: Number) -> List[Number]:
        """Returns all the coordinates at the given index.

        Args:
            coordinate_index (Number): The index to get for each coordinate.

        Returns:
            List[Number]:The list of coordinates at the given index.

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
            properties (DiscretizationProperties): Discretization will be done according to
                the properties of the device.

        Returns:
            AtomArrangement: A new discretized atom arrangement.
        """
        try:
            position_res = properties.lattice.geometry.positionResolution
            discretized_arrangement = AtomArrangement()
            for site in self._sites:
                new_coordinates = tuple(
                    (round(Decimal(c) / position_res) * position_res for c in site.coordinate)
                )
                discretized_arrangement.add(new_coordinates, site.site_type)
            return discretized_arrangement
        except Exception as e:
            raise DiscretizationError(f"Failed to discretize register {e}")
