import pytest

from braket.emulators.emulator_passes.criteria import NativeGateCriterion
from braket.circuits import Circuit, Gate, gates


@pytest.fixture
def h_cnot_gates():
    return ["h", "cnot"]


@pytest.mark.parametrize(
    "circuit", 
    [
        Circuit(), 
        Circuit().x(0).h(1).swap(0, 1),
        Circuit().add_verbatim_box(
            Circuit().h(0).cnot(0, 1).h(2).cnot(0, 3).h(range(3))
        ),
        Circuit().cswap(0, 1, 2).z(3).add_verbatim_box(
            Circuit().h(0).cnot(0, 1).h(2).cnot(0, 3)
        ).cnot(2, 4).rx(5, 0).add_verbatim_box(
            Circuit().h(0).cnot(0, 1).h(5).cnot(4, 6)
        )
    ]
)
def test_valid_circuits(h_cnot_gates, circuit):
    """
        NativeGateCriterion should not raise any errors when validating these circuits given
        a native gate set of [H, CNOT]
    """
    NativeGateCriterion(h_cnot_gates).validate(circuit)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().add_verbatim_box(
            Circuit().z(0)
        ),
        Circuit().phaseshift(0, 0).h(0).add_verbatim_box(
            Circuit().h(0).cnot(1, 2).rx(3, 0)
        ).add_verbatim_box(
            Circuit().h(0).cnot(0, 1).h(0).cnot(1, 3)
        ), 
        Circuit().h(0).cnot(0, 1).h(2).add_verbatim_box(
            Circuit().h(2).cnot(2, 3).h(4)
        ).add_verbatim_box(
            Circuit().cy(2, 3)
        )
    ]
)
def test_invalid_circuits(h_cnot_gates, circuit):
    """
        NativeGateCriterion should raise an error when validating these circuits given
        a native gate set of [H, CNOT]
    """
    with pytest.raises(ValueError):
        NativeGateCriterion(h_cnot_gates).validate(circuit)


def test_empty_native_gates():
    with pytest.raises(ValueError):
        NativeGateCriterion([])


@pytest.mark.parametrize(
    "gate_set_1, gate_set_2",
    [
        (["h"], ["h"]),
        (["cnot", "h"], ["h", "cnot"]),
        (["phaseshift", "cnot", "rx", "ry"], ["ry", "rx", "cnot", "phaseshift"])
    ],
)
def test_equality(gate_set_1, gate_set_2):
    assert NativeGateCriterion(gate_set_1) == NativeGateCriterion(gate_set_2)


@pytest.mark.parametrize(
    "gate_set_1, gate_set_2",
    [
        (["h"], ["x"]),
        (["cnot"], ["h", "cnot"]),
        (["cnot", "h"], ["h"]),
        (["phaseshift", "cnot", "ms", "ry"], ["ry", "rx", "cnot", "ms"])
    ],
)
def test_inequality(gate_set_1, gate_set_2):
    assert NativeGateCriterion(gate_set_1) != NativeGateCriterion(gate_set_2)


