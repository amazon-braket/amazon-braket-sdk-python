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
    assert BasisState(basis_state_input, size).as_tuple == as_tuple
    assert BasisState(basis_state_input, size).as_int == as_int
    assert BasisState(basis_state_input, size).as_string == as_string
