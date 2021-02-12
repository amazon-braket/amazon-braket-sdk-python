import numpy as np
import pytest

from braket.circuits.circuit import Circuit
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.noise import Noise
from braket.circuits.noise_helpers import add_noise_to_gates, add_noise_to_moments
from braket.circuits.qubit_set import QubitSet

invalid_data_noise_type = [Gate.X(), Gate.X, None, 1.5]
invalid_data_target_gates_type = [([-1, "foo"]), ([1.5, None, -1]), "X", ([Gate.X, "CNot"])]
invalid_data_target_times_type = [1.5, "foo", ["foo", 1]]


@pytest.fixture
def circuit_2qubit():
    return Circuit().x(0).y(1).x(0).x(1).cnot(0, 1)


@pytest.fixture
def circuit_2qubit_not_dense():
    # there are some qubits and some time that are not occupied by a gate
    return Circuit().x(0).y(1).x(0).cnot(0, 1)


@pytest.fixture
def circuit_3qubit():
    return Circuit().x(0).y(1).cnot(0, 1).z(2).cz(2, 1).cnot(0, 2).cz(1, 2)


@pytest.fixture
def noise_1qubit():
    return Noise.BitFlip(probability=0.1)


@pytest.fixture
def noise_2qubit():
    E0 = np.sqrt(0.8) * np.eye(4)
    E1 = np.sqrt(0.2) * np.kron(np.array([[0, 1], [1, 0]]), np.array([[0, 1], [1, 0]]))
    return Noise.Kraus(matrices=[E0, E1])


@pytest.mark.xfail(raises=TypeError)
@pytest.mark.parametrize("noise", invalid_data_noise_type)
def test_add_noise_invalid_noise_type(circuit_2qubit, noise):
    circuit_2qubit.add_noise(noise)


@pytest.mark.xfail(raises=TypeError)
@pytest.mark.parametrize("target_gates", invalid_data_target_gates_type)
def test_add_noise_invalid_target_gates_type(circuit_2qubit, noise_1qubit, target_gates):
    circuit_2qubit.add_noise(noise_1qubit, target_gates=target_gates)


@pytest.mark.xfail(raises=TypeError)
@pytest.mark.parametrize("target_times", invalid_data_target_times_type)
def test_add_noise_invalid_target_times_type(circuit_2qubit, noise_1qubit, target_times):
    circuit_2qubit.add_noise(noise_1qubit, target_times=target_times)


@pytest.mark.xfail(raises=ValueError)
def test_add_noise_mismatch_qubit_count_with_target_gates(noise_2qubit):
    circ = Circuit().cswap(0, 1, 2)
    circ.add_noise(noise_2qubit, target_gates=Gate.CSwap)


@pytest.mark.xfail(raises=ValueError)
def test_add_noise_mismatch_qubit_count_with_target_qubits(noise_2qubit):
    circ = Circuit().cswap(0, 1, 2)
    circ.add_noise(noise_2qubit, target_qubits=[0, 1, 2])


def test_circuit_add_with_noise(circuit_2qubit, noise_1qubit):
    circ = circuit_2qubit.add(
        noise_1qubit,
        target_gates=Gate.X,
        target_qubits=None,
        target_times=None,
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(Gate.X(), 1))
        .add_instruction(Instruction(noise_1qubit, 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
    )

    assert circ == expected


def test_add_noise_to_gates_1QubitNoise_1(circuit_2qubit, noise_1qubit):
    circ = add_noise_to_gates(
        circuit_2qubit,
        noise_1qubit,
        target_gates=[Gate.X],
        target_qubits=None,
        target_times=None,
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(Gate.X(), 1))
        .add_instruction(Instruction(noise_1qubit, 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
    )

    assert circ == expected


def test_add_noise_to_gates_1QubitNoise_2(circuit_2qubit, noise_1qubit):
    circ = add_noise_to_gates(
        circuit_2qubit,
        noise_1qubit,
        target_gates=[Gate.X],
        target_qubits=QubitSet(0),
        target_times=[1],
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(Gate.X(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
    )

    assert circ == expected


def test_add_noise_to_gates_2QubitNoise_1(circuit_3qubit, noise_2qubit):
    circ = add_noise_to_gates(
        circuit_3qubit,
        noise_2qubit,
        target_gates=[Gate.CNot],
        target_qubits=None,
        target_times=None,
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(noise_2qubit, [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(noise_2qubit, [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
    )

    assert circ == expected


def test_add_noise_to_gates_2QubitNoise_2(circuit_3qubit, noise_2qubit):
    circ = add_noise_to_gates(
        circuit_3qubit,
        noise_2qubit,
        target_gates=[Gate.CZ],
        target_qubits=QubitSet([1, 2]),
        target_times=[1, 2],
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(noise_2qubit, [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
    )

    assert circ == expected


def test_add_noise_to_moments_1QubitNoise_1(circuit_2qubit, noise_1qubit):
    circ = add_noise_to_moments(
        circuit_2qubit,
        noise_1qubit,
        target_qubits=None,
        target_times=None,
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(noise_1qubit, 1))
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.X(), 1))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(noise_1qubit, 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(noise_1qubit, 0))
        .add_instruction(Instruction(noise_1qubit, 1))
    )

    assert circ == expected


def test_add_noise_to_moments_1QubitNoise_2(circuit_2qubit, noise_1qubit):
    circ = add_noise_to_moments(
        circuit_2qubit,
        noise_1qubit,
        target_qubits=QubitSet(1),
        target_times=[0, 2],
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(noise_1qubit, 1))
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.X(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(noise_1qubit, 1))
    )

    assert circ == expected


def test_add_noise_to_moments_1QubitNoise_not_dense(circuit_2qubit_not_dense, noise_1qubit):
    circ = add_noise_to_moments(
        circuit_2qubit_not_dense,
        noise_1qubit,
        target_qubits=None,
        target_times=None,
    )

    expected_moments = Moments()
    expected_moments._add(Instruction(Gate.X(), 0))
    expected_moments._add(Instruction(Gate.Y(), 1))
    expected_moments._add_noise(Instruction(noise_1qubit, 0))
    expected_moments._add_noise(Instruction(noise_1qubit, 1))
    expected_moments._add(Instruction(Gate.X(), 0))
    expected_moments._add_noise(Instruction(noise_1qubit, 0))
    expected_moments._add_noise(Instruction(noise_1qubit, 1), 1)
    expected_moments._add(Instruction(Gate.CNot(), [0, 1]))
    expected_moments._add_noise(Instruction(noise_1qubit, 0))
    expected_moments._add_noise(Instruction(noise_1qubit, 1))

    assert circ.moments == expected_moments


def test_add_noise_to_moments_2QubitNoise(circuit_3qubit, noise_2qubit):
    circ = add_noise_to_moments(
        circuit_3qubit,
        noise_2qubit,
        target_qubits=QubitSet([2, 1]),
        target_times=[4],
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
        .add_instruction(Instruction(noise_2qubit, [2, 1]))
    )

    assert circ == expected


def test_add_noise_with_target_gates(circuit_2qubit, noise_1qubit):
    circ1 = circuit_2qubit.copy()
    circ2 = circuit_2qubit.copy()

    circ1 = circ1.add(
        noise_1qubit,
        target_gates=Gate.X,
        target_qubits=None,
        target_times=None,
    )

    circ2 = add_noise_to_gates(
        circ2,
        noise_1qubit,
        target_gates=[Gate.X],
        target_qubits=None,
        target_times=None,
    )

    assert circ1 == circ2


def test_add_noise_no_target_gates(circuit_2qubit, noise_1qubit):
    circ1 = circuit_2qubit.copy()
    circ2 = circuit_2qubit.copy()

    circ1 = circ1.add(
        noise_1qubit,
        target_gates=None,
        target_qubits=0,
        target_times=1,
    )

    circ2 = add_noise_to_moments(
        circ2,
        noise_1qubit,
        target_qubits=[0],
        target_times=[1],
    )

    assert circ1 == circ2
