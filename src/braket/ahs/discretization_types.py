from dataclasses import dataclass
from typing import Any


class DiscretizationError(Exception):
    """Raised if the discretization of the numerical values of the AHS program fails."""

    pass


@dataclass
class DiscretizationProperties:
    """These properties can be used to discretize a problem to the capabilities of a device."""

    lattice: Any
    rydberg: Any
