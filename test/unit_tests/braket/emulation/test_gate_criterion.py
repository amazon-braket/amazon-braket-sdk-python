import numpy as np
import pytest

from braket.circuits import Circuit, Gate, Instruction
from braket.emulators.emulator_passes.criteria import GateCriterion
from braket.circuits.noises import BitFlip
from braket.circuits.compiler_directives import StartVerbatimBox


@pytest.fixture
def basic_gate_set():
    return (["h", "cnot"], ["cz", "prx"])


@pytest.fixture
def mock_qpu_gates():
    supported_gates = [
        "ccnot",
        "cnot",
        "cphaseshift",
        "cswap",
        "swap",
        "iswap",
        "pswap",
        "ecr",
        "cy",
        "cz",
        "xy",
        "zz",
        "h",
        "i",
        "phaseshift",
        "rx",
        "ry",
        "v",
        "vi",
        "x",
        "y",
        "z",
    ]

    native_gates = ["cz", "prx"]
    return (supported_gates, native_gates)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit()
        .h(range(4))
        .cnot(0, 5)
        .pswap(0, 1, np.pi / 4)
        .xy(0, 1, 0.5)
        .cphaseshift(0, 1, np.pi / 4),
        Circuit()
        .swap(0, 1)
        .rx(0, 0.5)
        .v(1)
        .h(2)
        .add_verbatim_box(Circuit().cz(0, 1).cz(0, 6).prx(0, np.pi / 4, np.pi / 5))
        .z(3),
        Circuit()
        .add_verbatim_box(Circuit().cz(0, 2).prx(0, 0.5, 0.5))
        .add_verbatim_box(Circuit().cz(0, 4).cz(3, 6)),
        Circuit().h(0).add_verbatim_box(Circuit()),
        Circuit().add_verbatim_box(
            Circuit().prx(0, np.pi/4, np.pi/4).apply_gate_noise(BitFlip(0.1), Gate.PRx)
        ).v(1)
    ],
)
def test_valid_circuits(mock_qpu_gates, circuit):
    """
    GateCriterion should not raise any errors when validating these circuits.
    """
    GateCriterion(mock_qpu_gates[0], mock_qpu_gates[1]).validate(circuit)


def test_only_supported_gates():
    supported_gates = ["h", "cnot", "rx", "xx", "y"]
    criterion = GateCriterion(supported_gates=supported_gates)
    circuit = Circuit().h(0).cnot(0, 1).rx(4, np.pi / 4).xx(2, 3, np.pi / 4).y(7)
    criterion.validate(circuit)


def test_verbatim_circuit_only_supported_gates():
    supported_gates = ["h", "cnot", "rx", "xx", "y"]
    criterion = GateCriterion(supported_gates=supported_gates)
    circuit = Circuit().add_verbatim_box(Circuit().h(0))

    with pytest.raises(ValueError):
        criterion.validate(circuit)


def test_only_native_gates():
    native_gates = ["h", "cnot", "rx", "xx", "y"]
    criterion = GateCriterion(native_gates=native_gates)
    vb = Circuit().h(0).cnot(0, 1).rx(4, np.pi / 4).xx(2, 3, np.pi / 4).y(7)
    circuit = Circuit().add_verbatim_box(vb)
    criterion.validate(circuit)


def test_non_verbatim_circuit_only_native_gates():
    native_gates = ["h", "cnot", "rx", "xx", "y"]
    criterion = GateCriterion(native_gates=native_gates)
    vb = Circuit().h(0).cnot(0, 1).rx(4, np.pi / 4).xx(2, 3, np.pi / 4).y(7)
    circuit = Circuit().add_verbatim_box(vb)
    circuit.i(0)
    with pytest.raises(ValueError):
        criterion.validate(circuit)


@pytest.mark.parametrize(
    "supported_gates,native_gates",
    [
        ([],[]),
        (["CX"], [])
    ]
)
def test_invalid_instantiation(supported_gates, native_gates):
    with pytest.raises(ValueError):
        GateCriterion(supported_gates, native_gates)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().z(0),
        Circuit().h(0).cnot(0, 1).cz(0, 1),
        Circuit().add_verbatim_box(Circuit().h(2)),
        Circuit().cphaseshift01(0, 1, np.pi / 4).h(0).cnot(0, 1),
        Circuit()
        .h(0)
        .add_verbatim_box(Circuit().cz(1, 2).prx(range(5), np.pi / 4, np.pi / 2).cz(2, 6))
        .prx(range(4), np.pi / 4, np.pi / 6),
        Circuit().add_instruction(Instruction(StartVerbatimBox()))
    ],
)
def test_invalid_circuits(basic_gate_set, circuit):
    """
    GateCriterion should raise errors when validating these circuits.
    """
    with pytest.raises(ValueError):
        GateCriterion(basic_gate_set[0], basic_gate_set[1]).validate(circuit)


@pytest.mark.parametrize(
    "gate_set_1, gate_set_2",
    [
        (["h"], ["h"]),
        (["cnot", "h"], ["h", "cnot"]),
        (["phaseshift", "cnot", "rx", "ry"], ["ry", "rx", "cnot", "phaseshift"])
    ],
)
def test_equality(gate_set_1, gate_set_2):
    assert GateCriterion(gate_set_1) == GateCriterion(gate_set_2)


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
    assert GateCriterion(gate_set_1) != GateCriterion(gate_set_2)
