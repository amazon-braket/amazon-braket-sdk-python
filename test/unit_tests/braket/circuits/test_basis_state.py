# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import pytest

from braket.circuits.basis_state import BasisState


@pytest.mark.parametrize(
    "basis_state_input, size, as_tuple, as_int, as_string",
    (
        (
            [1, 0, 1],
            None,
            (1, 0, 1),
            5,
            "101",
        ),
        (
            [1, 0, 1],
            5,
            (0, 0, 1, 0, 1),
            5,
            "00101",
        ),
        (
            "1",
            3,
            (0, 0, 1),
            1,
            "001",
        ),
        (
            "101",
            None,
            (1, 0, 1),
            5,
            "101",
        ),
        (
            5,
            None,
            (1, 0, 1),
            5,
            "101",
        ),
        (
            5,
            4,
            (0, 1, 0, 1),
            5,
            "0101",
        ),
    ),
)
def test_as_props(basis_state_input, size, as_tuple, as_int, as_string):
    basis_state = BasisState(basis_state_input, size)
    assert basis_state.as_tuple == as_tuple
    assert basis_state.as_int == as_int
    assert basis_state.as_string == as_string == str(basis_state)
    assert repr(basis_state) == f'BasisState("{as_string}")'


@pytest.mark.parametrize(
    "basis_state_input, index, substate_input",
    (
        (
            "1001",
            slice(None),
            "1001",
        ),
        (
            "1001",
            3,
            "1",
        ),
        (
            "1010",
            slice(None, None, 2),
            "11",
        ),
        (
            "1010",
            slice(1, None, 2),
            "00",
        ),
        (
            "1010",
            slice(None, -2),
            "10",
        ),
        (
            "1010",
            -1,
            "0",
        ),
    ),
)
def test_indexing(basis_state_input, index, substate_input):
    assert BasisState(basis_state_input)[index] == BasisState(substate_input)


def test_bool():
    assert all([
        BasisState("100"),
        BasisState("111"),
        BasisState("1"),
    ])
    assert not BasisState("0")
