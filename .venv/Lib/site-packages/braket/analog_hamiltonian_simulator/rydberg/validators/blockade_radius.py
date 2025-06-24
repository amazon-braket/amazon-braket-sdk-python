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

from braket.analog_hamiltonian_simulator.rydberg.constants import MIN_BLOCKADE_RADIUS


def validate_blockade_radius(blockade_radius: float) -> float:
    """Validate the Blockade radius

    Args:
        blockade_radius (float): The user-specified blockade radius

    Returns:
        float: The validated blockade radius

    Raises:
        ValueError: If blockade_radius < 0
    """
    blockade_radius = float(blockade_radius)
    if blockade_radius < 0:
        raise ValueError("`blockade_radius` needs to be non-negative.")

    if 0 < blockade_radius and blockade_radius < MIN_BLOCKADE_RADIUS:
        warnings.warn(
            f"Blockade radius {blockade_radius} meter is smaller than the typical value "
            f"({MIN_BLOCKADE_RADIUS} meter). "
            "The blockade radius should be specified in SI units."
        )

    return blockade_radius
