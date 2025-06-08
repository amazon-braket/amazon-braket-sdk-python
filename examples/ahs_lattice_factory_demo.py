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

"""
Demonstration of AHS AtomArrangement factory methods.

This example shows how to use the new factory methods to create common
lattice arrangements for Analog Hamiltonian Simulation (AHS).
"""

from braket.ahs import AtomArrangement, Canvas, SiteType

# Define a canvas (boundary region) where atoms can be placed
canvas_boundary = [
    (0, 0),  # Bottom-left corner
    (30e-6, 0),  # Bottom-right corner
    (30e-6, 30e-6),  # Top-right corner
    (0, 30e-6),  # Top-left corner
]
canvas = Canvas(canvas_boundary)

print("AHS AtomArrangement Factory Methods Demo")
print("=" * 50)

# 1. Square Lattice
print("\n1. Square Lattice:")
spacing = 5e-6
square_arrangement = AtomArrangement.from_square_lattice(spacing, canvas)
print(f"   Created {len(square_arrangement)} atoms in square lattice")
print(f"   Spacing: {spacing * 1e6:.1f} μm")

# 2. Rectangular Lattice
print("\n2. Rectangular Lattice:")
spacing_x = 4e-6
spacing_y = 6e-6
rect_arrangement = AtomArrangement.from_rectangular_lattice(spacing_x, spacing_y, canvas)
print(f"   Created {len(rect_arrangement)} atoms in rectangular lattice")
print(f"   X spacing: {spacing_x * 1e6:.1f} μm, Y spacing: {spacing_y * 1e6:.1f} μm")

# 3. Triangular Lattice
print("\n3. Triangular Lattice:")
tri_spacing = 6e-6
tri_arrangement = AtomArrangement.from_triangular_lattice(tri_spacing, canvas)
print(f"   Created {len(tri_arrangement)} atoms in triangular lattice")
print(f"   Nearest neighbor distance: {tri_spacing * 1e6:.1f} μm")

# 4. Honeycomb Lattice
print("\n4. Honeycomb Lattice:")
honey_spacing = 4e-6
honey_arrangement = AtomArrangement.from_honeycomb_lattice(honey_spacing, canvas)
print(f"   Created {len(honey_arrangement)} atoms in honeycomb lattice")
print(f"   Nearest neighbor distance: {honey_spacing * 1e6:.1f} μm")

# 5. Custom Bravais Lattice
print("\n5. Custom Bravais Lattice:")
a1 = (8e-6, 0)
a2 = (4e-6, 7e-6)
custom_arrangement = AtomArrangement.from_bravais_lattice(a1, a2, canvas)
print(f"   Created {len(custom_arrangement)} atoms in custom Bravais lattice")
print(f"   Lattice vectors: a1={a1}, a2={a2}")

# 6. Decorated Bravais Lattice
print("\n6. Decorated Bravais Lattice:")
a1 = (10e-6, 0)
a2 = (0, 10e-6)
basis = [(0, 0), (3e-6, 3e-6), (7e-6, 7e-6)]
decorated_arrangement = AtomArrangement.from_bravais_lattice(a1, a2, canvas, basis=basis)
print(f"   Created {len(decorated_arrangement)} atoms in decorated lattice")
print(f"   Unit cell contains {len(basis)} atoms")

# 7. Using VACANT sites
print("\n7. Square Lattice with VACANT sites:")
vacant_arrangement = AtomArrangement.from_square_lattice(
    spacing=8e-6, canvas=canvas, site_type=SiteType.VACANT
)
print(f"   Created {len(vacant_arrangement)} VACANT sites")

# 8. Complex Canvas Shape (L-shape)
print("\n8. Square Lattice in L-shaped Canvas:")
l_shape_boundary = [(0, 0), (20e-6, 0), (20e-6, 10e-6), (10e-6, 10e-6), (10e-6, 20e-6), (0, 20e-6)]
l_canvas = Canvas(l_shape_boundary)
l_arrangement = AtomArrangement.from_square_lattice(4e-6, l_canvas)
print(f"   Created {len(l_arrangement)} atoms in L-shaped region")

print("\n" + "=" * 50)
print("Demo completed! The factory methods make it easy to create")
print("complex atom arrangements for AHS without manual coordinate calculation.")
