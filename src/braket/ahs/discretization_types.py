from dataclasses import dataclass
from typing import Any


class DiscretizationError(Exception):
    """Raised if the discretization of the numerical values of the AHS program fails."""

    pass


@dataclass
class DiscretizationProperties:
    lattice: Any
    rydberg: Any
