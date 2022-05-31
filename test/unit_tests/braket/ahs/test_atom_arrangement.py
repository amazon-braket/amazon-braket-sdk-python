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

from decimal import Decimal

from braket.ahs.atom_arrangement import AtomArrangement, SiteType


def test_add_chaining():
    atom_arrangement = (
        AtomArrangement()
        .add(coord=(0, 0), site_type=SiteType.FILLED)
        .add((0, 3), SiteType.FILLED)
        .add((0, 6))
        .add((3, 0))
        .add((3, 3))
        .add((3, 6))
        .add((3, 0))
    )
    assert len(atom_arrangement) == 7


def test_iteration():
    values = [(0, 0), (0.1, 0.2), (Decimal(0.3), Decimal(0.4))]
    atom_arrangement = AtomArrangement()
    for value in values:
        atom_arrangement.add(value)
    returned_values = []
    for site in atom_arrangement:
        returned_values.append(site.coordinate)
    assert values == returned_values


def test_coordinate_list():
    values = [(0, 0), (0.1, 0.2), (Decimal(0.3), Decimal(0.4))]
    atom_arrangement = AtomArrangement()
    for value in values:
        atom_arrangement.add(value)
    for coord_index in range(2):
        coords = atom_arrangement.coordinate_list(coord_index)
        assert coords == [value[coord_index] for value in values]
