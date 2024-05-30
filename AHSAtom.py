from typing import Union, Tuple, List
from dataclasses import dataclass
import numpy as np
from enum import Enum

# Define SiteType enum
class SiteType(Enum):
    FILLED = "filled"
    VACANT = "vacant"

@dataclass
class AtomArrangementItem:
    """Represents an item (coordinate and metadata) in an atom arrangement."""

    coordinate: Tuple[float, float]
    site_type: SiteType

class AtomArrangement:
    def __init__(self):
        """Represents a set of coordinates that can be used as a register to an
        AnalogHamiltonianSimulation.
        """
        self._sites = []

    def add(
        self,
        coordinate: Union[Tuple[float, float], np.ndarray],
        site_type: SiteType = SiteType.FILLED,
    ) -> "AtomArrangement":
        """Add a coordinate to the atom arrangement.
        Args:
            coordinate (Union[tuple[float, float], ndarray]): The coordinate of the
                atom (in meters). The coordinates can be a numpy array of shape (2,)
                or a tuple of float.
            site_type (SiteType): The type of site. Optional. Default is FILLED.
        Returns:
            AtomArrangement: returns self (to allow for chaining).
        """
        self._sites.append(AtomArrangementItem(tuple(coordinate), site_type))
        return self

    # Define factory methods for different lattice structures
    @classmethod
    def from_square_lattice(
        cls, lattice_constant: float, canvas_boundary_points: List[Tuple[float, float]]
    ) -> "AtomArrangement":
        # Calculate coordinates for square lattice
        arrangement = cls()
        for x in np.arange(canvas_boundary_points[0][0], canvas_boundary_points[1][0], lattice_constant):
            for y in np.arange(canvas_boundary_points[0][1], canvas_boundary_points[2][1], lattice_constant):
                arrangement.add((x, y))
        return arrangement

    @classmethod
    def from_rectangular_lattice(
        cls,
        dx: float,
        dy: float,
        canvas_boundary_points: List[Tuple[float, float]]
    ) -> "AtomArrangement":
        # Calculate coordinates for rectangular lattice
        arrangement = cls()
        for x in np.arange(canvas_boundary_points[0][0], canvas_boundary_points[1][0], dx):
            for y in np.arange(canvas_boundary_points[0][1], canvas_boundary_points[2][1], dy):
                arrangement.add((x, y))
        return arrangement

    # Similar methods for other lattice types

# Example usage
canvas_boundary_points = [(0,0), (7.5e-5, 0), (0, 7.6e-5), (7.5e-5, 7.6e-5)]
canvas = AtomArrangement.from_square_lattice(4e-6, canvas_boundary_points)

@dataclass
class AtomArrangementItem:
    """Represents an item (coordinate and metadata) in an atom arrangement."""

    coordinate: Tuple[float, float]
    site_type: str = "FILLED"

    def _validate_coordinate(self) -> None:
        if len(self.coordinate) != 2:
            raise ValueError(f"{self.coordinate} must be of length 2")
        for idx, num in enumerate(self.coordinate):
            if not isinstance(num, (int, float)):
                raise TypeError(f"{num} at position {idx} must be a number")

    def __post_init__(self) -> None:
        self._validate_coordinate()

class AtomArrangement:
    def __init__(self):
        """Represents a set of coordinates that can be used as a register to an
        AnalogHamiltonianSimulation.
        """
        self._sites = []

    @classmethod
    def from_square_lattice(cls, d: float, canvas_boundary_points: List[Tuple[float, float]]) -> 'AtomArrangement':
        """Create an atom arrangement with a square lattice."""
        arrangement = cls()
        # Generate coordinates for square lattice
        x_min, y_min = canvas_boundary_points[0]
        x_max, y_max = canvas_boundary_points[2]
        x_range = np.arange(x_min, x_max, d)
        y_range = np.arange(y_min, y_max, d)
        for x in x_range:
            for y in y_range:
                arrangement.add((x, y))
        return arrangement

    def add(
        self,
        coordinate: Tuple[float, float],
        site_type: str = "FILLED",
    ) -> None:
        """Add a coordinate to the atom arrangement.

        Args:
            coordinate (Tuple[float, float]): The coordinate of the
                atom (in meters).
            site_type (str): The type of site. Optional. Default is FILLED.
        """
        self._sites.append(AtomArrangementItem(coordinate, site_type))

    
