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

from dataclasses import dataclass
from typing import Any


class DiscretizationError(Exception):
    """Raised if the discretization of the numerical values of the AHS program fails."""


@dataclass
class DiscretizationProperties:
    """Capabilities of a device that represent the resolution with which the device can
    implement the parameters.

    :parameter lattice (Any): configuration values for discretization of the lattice geometry,
        including the position resolution.
    :parameter rydberg (Any): configuration values for discretization of Rydberg fields.

    Examples:
        lattice.geometry.positionResolution = Decimal("1E-7")
        rydberg.rydbergGlobal.timeResolution = Decimal("1E-9")
        rydberg.rydbergGlobal.phaseResolution = Decimal("5E-7")
    """

    lattice: Any
    rydberg: Any
