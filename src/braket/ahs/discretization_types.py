from dataclasses import dataclass
from typing import Any


class DiscretizationError(Exception):
    """Raised if the discretization of the numerical values of the AHS program fails."""

    pass


@dataclass
class DiscretizationProperties:
    """Capabilities of a device that represent the resolution with which the device can
    implement the parameters.

    lattice (Any): configuration values for discretization of the lattice geometry,
        including the position resolution.
    rydberg (Any): configuration values for discretization of Rydberg fields.

    Examples:
        lattice.geometry.positionResolution = Decimal("1E-7")
        rydberg.rydbergGlobal.timeResolution = Decimal("1E-9")
        rydberg.rydbergGlobal.phaseResolution = Decimal("5E-7")
    """

    lattice: Any
    rydberg: Any
