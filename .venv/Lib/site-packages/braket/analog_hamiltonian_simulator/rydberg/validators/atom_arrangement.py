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

import warnings
from decimal import Decimal

import numpy as np
from pydantic.v1.class_validators import root_validator

from braket.analog_hamiltonian_simulator.rydberg.validators.capabilities_constants import (
    CapabilitiesConstants,
)
from braket.ir.ahs.atom_arrangement import AtomArrangement


def _euclidean_distance(
    site_1: tuple[Decimal, Decimal], site_2: tuple[Decimal, Decimal]
) -> Decimal:
    # Compute the Euclidean distance between two sets of 2-D points, (x1, y1) and (x2, y2)

    return np.linalg.norm(np.array(site_1) - np.array(site_2))


class AtomArrangementValidator(AtomArrangement):
    capabilities: CapabilitiesConstants

    # Each site has two coordinates (minItems=maxItems=2)
    @root_validator(pre=True, skip_on_failure=True)
    def sites_have_length_2(cls, values: dict) -> dict:
        """
        Validate that the sites in the atom arrangement have only two coordinates

        Args:
            values (Dict): The site and capability constants

        Returns:
            Dict: The validated sites
        """
        sites = values["sites"]
        capabilities = values["capabilities"]
        for index, site in enumerate(sites):
            if len(site) != capabilities.DIMENSIONS:
                raise ValueError(
                    f"Site {index}({site}) has length {len(site)}; it must be "
                    f"{capabilities.DIMENSIONS}."
                )
        return values

    # All lattice sites should fit within a (BOUNDING_BOX_SIZE_X) x (BOUNDING_BOX_SIZE_Y)
    # bounding box. If not, a warning message will issue to remind the user that the SI
    # units are used here.
    @root_validator(pre=True, skip_on_failure=True)
    def sites_fit_in_bounding_box(cls, values):
        sites = values["sites"]
        if sites:
            capabilities = values["capabilities"]
            sorted_sites = sorted(sites, key=lambda xy: xy[0])
            biggest_x_distance = sorted_sites[-1][0] - sorted_sites[0][0]
            if biggest_x_distance > capabilities.BOUNDING_BOX_SIZE_X:
                warnings.warn(
                    f"Sites {sorted_sites[0]} and {sorted_sites[-1]} "
                    "have x-separation bigger than the typical scale "
                    f"({capabilities.BOUNDING_BOX_SIZE_X} meters). "
                    "The coordinates of the atoms should be specified in SI units."
                )

            if biggest_x_distance <= capabilities.BOUNDING_BOX_SIZE_X:
                sorted_sites = sorted(sites, key=lambda xy: xy[1])
                biggest_y_distance = sorted_sites[-1][1] - sorted_sites[0][1]
                if biggest_y_distance > capabilities.BOUNDING_BOX_SIZE_Y:
                    warnings.warn(
                        f"Sites {sorted_sites[0]} and {sorted_sites[-1]} "
                        "have y-separation bigger than the typical scale "
                        f"({capabilities.BOUNDING_BOX_SIZE_Y} meters). "
                        "The coordinates of the atoms should be specified in SI units."
                    )

        return values

    #  Filling has only integers which are either 0 or 1
    @root_validator(pre=True, skip_on_failure=True)
    def filling_contains_only_0_and_1(cls, values):
        filling = values["filling"]
        for idx, f in enumerate(filling):
            if f not in {0, 1}:
                raise ValueError(f"Invalid value at {idx} (value: {f}). Only 0 and 1 are allowed.")
        return values

    # Filling must have the same length as `lattice_sites`.
    @root_validator(pre=True, skip_on_failure=True)
    def filling_same_length_as_sites(cls, values):
        filling = values["filling"]
        expected_length = len(values["sites"])
        length = len(filling)
        if length != expected_length:
            raise ValueError(
                f"Filling length ({length}) does not match sites length ({expected_length})"
            )
        return values

    # Two lattice sites cannot be closer (in terms of Euclidean distance) than MIN_DISTANCE
    @root_validator(pre=True, skip_on_failure=True)
    def sites_not_too_close(cls, values):
        sites = values["sites"]
        capabilities = values["capabilities"]
        for index_1, site_1 in enumerate(sites):
            for index_2, site_2 in enumerate(sites[index_1 + 1 :], start=index_1 + 1):
                distance = _euclidean_distance(site_1, site_2)
                if distance < capabilities.MIN_DISTANCE:
                    warnings.warn(
                        f"Sites {index_1}({site_1}) and site {index_2}({site_2}) are too close. "
                        f"Their Euclidean distance ({Decimal(str(distance))} meters) is smaller "
                        f"than the typical scale ({capabilities.MIN_DISTANCE} meters). "
                        "The coordinates of the sites should be specified in SI units."
                    )
        return values
