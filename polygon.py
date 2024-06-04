from typing import Tuple

class RectangularCanvas:
    def __init__(self, bottom_left: Tuple[float, float], top_right: Tuple[float, float]):
        """
        Initializes the RectangularCanvas with bottom-left and top-right coordinates.
        
        Args:
            bottom_left (Tuple[float, float]): The (x, y) coordinates of the bottom-left corner.
            top_right (Tuple[float, float]): The (x, y) coordinates of the top-right corner.
        """
        self.bottom_left = bottom_left
        self.top_right = top_right

    def is_within(self, point: Tuple[float, float]) -> bool:
        """
        Checks if a point is within the rectangular canvas.
        
        Args:
            point (Tuple[float, float]): The (x, y) coordinates of the point to check.
        
        Returns:
            bool: True if the point is within the canvas, False otherwise.
        """
        x_min, y_min = self.bottom_left
        x_max, y_max = self.top_right
        x, y = point
        return x_min <= x <= x_max and y_min <= y <= y_max

# Example usage
canvas = RectangularCanvas((0, 0), (7.5e-5, 7.6e-5))
print(canvas.is_within((3e-5, 3e-5)))  # Should print True
print(canvas.is_within((8e-5, 3e-5)))  # Should print False



from enum import Enum
from typing import Tuple, List, Iterator, Union
from decimal import Decimal

class SiteType(Enum):
    FILLED = "filled"
    EMPTY = "empty"

class AtomArrangementItem:
    def __init__(self, coordinate: Tuple[Union[int, float, Decimal], Union[int, float, Decimal]], site_type: SiteType):
        self.coordinate = coordinate
        self.site_type = site_type

class DiscretizationError(Exception):
    pass

class Geometry:
    def __init__(self, positionResolution: float):
        self.positionResolution = positionResolution

class Lattice:
    def __init__(self, geometry: Geometry):
        self.geometry = geometry

class DiscretizationProperties:
    def __init__(self, lattice: Lattice):
        self.lattice = lattice

class RectangularCanvas:
    def __init__(self, bottom_left: Tuple[float, float], top_right: Tuple[float, float]):
        self.bottom_left = bottom_left
        self.top_right = top_right

    def is_within(self, point: Tuple[float, float]) -> bool:
        x_min, y_min = self.bottom_left
        x_max, y_max = self.top_right
        x, y = point
        return x_min <= x <= x_max and y_min <= y <= y_max

from enum import Enum
from typing import Tuple, List, Iterator, Union
from decimal import Decimal
import numpy as np

# Enum for SiteType
class SiteType(Enum):
    FILLED = "filled"
    EMPTY = "empty"

# Class for AtomArrangementItem
class AtomArrangementItem:
    def __init__(self, coordinate: Tuple[Union[int, float, Decimal], Union[int, float, Decimal]], site_type: SiteType):
        self.coordinate = coordinate
        self.site_type = site_type

# Exception for discretization errors
class DiscretizationError(Exception):
    pass

# Classes for discretization properties
class Geometry:
    def __init__(self, positionResolution: float):
        self.positionResolution = positionResolution

class Lattice:
    def __init__(self, geometry: Geometry):
        self.geometry = geometry

class DiscretizationProperties:
    def __init__(self, lattice: Lattice):
        self.lattice = lattice

# RectangularCanvas class
class RectangularCanvas:
    def __init__(self, bottom_left: Tuple[float, float], top_right: Tuple[float, float]):
        self.bottom_left = bottom_left
        self.top_right = top_right

    def is_within(self, point: Tuple[float, float]) -> bool:
        x_min, y_min = self.bottom_left
        x_max, y_max = self.top_right
        x, y = point
        return x_min <= x <= x_max and y_min <= y <= y_max

# AtomArrangement class
class AtomArrangement:
    def __init__(self):
        self._sites = []

    def add(self, coordinate: Tuple[Union[int, float, Decimal], Union[int, float, Decimal]], site_type: SiteType = SiteType.FILLED) -> 'AtomArrangement':
        self._sites.append(AtomArrangementItem(tuple(coordinate), site_type))
        return self

    def coordinate_list(self, coordinate_index: int) -> List[Union[int, float, Decimal]]:
        return [site.coordinate[coordinate_index] for site in self._sites]

    def __iter__(self) -> Iterator:
        return iter(self._sites)

    def __len__(self):
        return len(self._sites)

    def discretize(self, properties: DiscretizationProperties) -> 'AtomArrangement':
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

    @classmethod
    def from_decorated_bravais_lattice(
        cls,
        lattice_vectors: List[Tuple[float, float]],
        decoration_points: List[Tuple[float, float]],
        canvas: RectangularCanvas
    ) -> 'AtomArrangement':
        arrangement = cls()
        vec_a, vec_b = np.array(lattice_vectors[0]), np.array(lattice_vectors[1])
        
        i = 0
        while (origin := i * vec_a)[0] < canvas.top_right[0]:
            j = 0
            while (point := origin + j * vec_b)[1] < canvas.top_right[1]:
                if canvas.is_within(point):
                    for dp in decoration_points:
                        decorated_point = point + np.array(dp)
                        if canvas.is_within(decorated_point):
                            arrangement.add(tuple(decorated_point))
                j += 1
            i += 1
        return arrangement

    @classmethod
    def from_honeycomb_lattice(cls, lattice_constant: float, canvas: RectangularCanvas) -> 'AtomArrangement':
        a1 = (lattice_constant, 0)
        a2 = (lattice_constant / 2, lattice_constant * np.sqrt(3) / 2)
        decoration_points = [(0, 0), (lattice_constant / 2, lattice_constant * np.sqrt(3) / 6)]
        return cls.from_decorated_bravais_lattice([a1, a2], decoration_points, canvas)

    @classmethod
    def from_bravais_lattice(cls, lattice_vectors: List[Tuple[float, float]], canvas: RectangularCanvas) -> 'AtomArrangement':
        return cls.from_decorated_bravais_lattice(lattice_vectors, [(0, 0)], canvas)

# Example usage
canvas = RectangularCanvas((0, 0), (7.5e-5, 7.6e-5))
atom_arrangement = AtomArrangement.from_honeycomb_lattice(4e-6, canvas)
print(len(atom_arrangement))  # Check the number of atoms arranged


from typing import List, Tuple
from shapely.geometry import Point, Polygon

class ArbitraryPolygonCanvas:
    def __init__(self, vertices: List[Tuple[float, float]]):
        """
        Initializes the ArbitraryPolygonCanvas with a list of vertices.
        
        Args:
            vertices (List[Tuple[float, float]]): The vertices of the polygon in order.
        """
        self.polygon = Polygon(vertices)

    def is_within(self, point: Tuple[float, float]) -> bool:
        """
        Checks if a point is within the polygon canvas.
        
        Args:
            point (Tuple[float, float]): The (x, y) coordinates of the point to check.
        
        Returns:
            bool: True if the point is within the canvas, False otherwise.
        """
        return self.polygon.contains(Point(point))

# Example usage
vertices = [(0, 0), (7.5e-5, 0), (7.5e-5, 7.6e-5), (0, 7.6e-5)]
canvas = ArbitraryPolygonCanvas(vertices)
print(canvas.is_within((3e-5, 3e-5)))  # Should print True
print(canvas.is_within((8e-5, 3e-5)))  # Should print False
