import pytest

from braket.emulators.criteria import SupportedGateCriterion
from braket.circuits import Circuit
import numpy as np

@pytest.fixture 
def h_cnot_gates():
    return ["h", "cnot"]


@pytest.fixture
def aspen3_supported_gates():
    return ['cz', 'xy', 'ccnot', 'cnot', 'cphaseshift', 'cphaseshift00', 'cphaseshift01', \
            'cphaseshift10', 'cswap', 'h', 'i', 'iswap', 'phaseshift', 'pswap', 'rx', 'ry', 'rz',\
             's', 'si', 'swap', 't', 'ti', 'x', 'y', 'z']

@pytest.mark.parametrize(
    "circuit", 
    [
        Circuit(),
        Circuit().h(range(5)).cnot(0, 1),
        Circuit().swap(0, 1).h(2).add_verbatim_box(
            Circuit().h(0).cnot(0, 1)
        ).z(3), 
        Circuit().phaseshift(0, np.pi/4).rx(1, np.pi/4).iswap(0, 1).si(2), 
        Circuit().add_verbatim_box(
            Circuit()
        ), 
        Circuit().cphaseshift01(0, 1, np.pi/4)
    ]
)
def test_valid_circuits(aspen3_supported_gates, circuit):
    """
        SupportedGateCriterion should not raise any errors when validating these circuits.
    """
    SupportedGateCriterion(aspen3_supported_gates).validate(circuit)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().z(0),
        Circuit().h(0).cnot(0, 1).z(2), 
        Circuit().add_verbatim_box(
            Circuit().z(2)
        ),
        Circuit().cphaseshift01(0, 1, np.pi/4).h(0).cnot(0, 1), 
        Circuit().h(0).add_verbatim_box(
            Circuit().cnot(1, 2).h(range(5)).h(3)
        ).rx(range(4), np.pi/4)
    ]
)
def test_invalid_circuits(h_cnot_gates, circuit):
    """
        SupportedGateCriterion should raise errors when validating these circuits.
    """
    with pytest.raises(ValueError):
        SupportedGateCriterion(h_cnot_gates).validate(circuit)


def test_empty_supported_gates():
    with pytest.raises(ValueError):
        SupportedGateCriterion([])


@pytest.mark.parametrize(
    "gate_set_1, gate_set_2",
    [
        (["h"], ["h"]),
        (["cnot", "h"], ["h", "cnot"]),
        (["phaseshift", "cnot", "rx", "ry"], ["ry", "rx", "cnot", "phaseshift"])
    ],
)
def test_equality(gate_set_1, gate_set_2):
    assert SupportedGateCriterion(gate_set_1) == SupportedGateCriterion(gate_set_2)


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
    assert SupportedGateCriterion(gate_set_1) != SupportedGateCriterion(gate_set_2)