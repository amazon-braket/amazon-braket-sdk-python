import numpy as np
import pytest

from braket.circuits.circuit import Circuit
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.noise import Noise
from braket.circuits.noise_helpers import NoiseInsertStrategy
from braket.circuits.qubit_set import QubitSet

invalid_data_noise_type = [Gate.X(), None, 1.5]
invalid_data_target_gates_type = [([-1, "foo"]), ([1.5, None, -1])]
invalid_data_target_times_type = [1.5, "foo", ["foo", 1]]


@pytest.fixture
def circuit_2qubit():
    return Circuit().x(0).y(1).x(0).x(1).cnot(0, 1)


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


def test_add_for_noise(circuit_2qubit, noise_1qubit):
    circ = circuit_2qubit.add(
        noise_1qubit,
        target_gates="X",
        target_qubits=None,
        target_times=range(circuit_2qubit.depth),
        insert_strategy="inclusive",
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


def test_add_noise_1QubitNoise_inclusive_1(circuit_2qubit, noise_1qubit):
    circ = circuit_2qubit.add_noise(
        noise_1qubit,
        target_gates="X",
        target_qubits=None,
        target_times=range(circuit_2qubit.depth),
        insert_strategy="inclusive",
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


def test_add_noise_1QubitNoise_inclusive_2(circuit_2qubit, noise_1qubit):
    circ = circuit_2qubit.add_noise(
        noise_1qubit,
        target_gates="X",
        target_qubits=QubitSet(0),
        target_times=[1],
        insert_strategy="inclusive",
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


def test_add_noise_1QubitNoise_no_target_gates_1(circuit_2qubit, noise_1qubit):
    circ = circuit_2qubit.add_noise(
        noise_1qubit,
        target_gates=None,
        target_qubits=circuit_2qubit.qubits,
        target_times=None,
        insert_strategy="inclusive",
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


def test_add_noise_1QubitNoise_no_target_gates_2(circuit_2qubit, noise_1qubit):
    circ = circuit_2qubit.add_noise(
        noise_1qubit,
        target_gates=None,
        target_qubits=QubitSet(1),
        target_times=[0, 2],
        insert_strategy="inclusive",
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


def test_add_noise_1QubitNoise_strict_1(circuit_3qubit, noise_1qubit):
    circ = circuit_3qubit.add_noise(
        noise_1qubit,
        target_gates="CZ",
        target_qubits=QubitSet([0, 1]),
        target_times=4,
        insert_strategy="strict",
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
    )

    assert circ == expected


def test_add_noise_1QubitNoise_strict_2(circuit_3qubit, noise_1qubit):
    circ = circuit_3qubit.add_noise(
        noise_1qubit,
        target_gates="CZ",
        target_qubits=QubitSet([1, 2]),
        target_times=None,
        insert_strategy="strict",
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
        .add_instruction(Instruction(noise_1qubit, 1))
        .add_instruction(Instruction(noise_1qubit, 2))
    )

    assert circ == expected


def test_add_noise_2QubitNoise_inclusive_1(circuit_3qubit, noise_2qubit):
    circ = circuit_3qubit.add_noise(
        noise_2qubit,
        target_gates="CNot",
        target_qubits=circuit_3qubit.qubits,
        target_times=range(circuit_3qubit.depth),
        insert_strategy="inclusive",
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


def test_add_noise_2QubitNoise_inclusive_2(circuit_3qubit, noise_2qubit):
    circ = circuit_3qubit.add_noise(
        noise_2qubit,
        target_gates="CZ",
        target_qubits=QubitSet([1, 2]),
        target_times=[1, 2],
        insert_strategy="inclusive",
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


def test_add_noise_2QubitNoise_inclusive_3(circuit_3qubit, noise_2qubit):
    circ = circuit_3qubit.add_noise(
        noise_2qubit,
        target_gates="CZ",
        target_qubits=QubitSet([1, 2]),
        target_times=[0, 1],
        insert_strategy="inclusive",
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
    )

    assert circ == expected


def test_add_noise_2QubitNoise_inclusive_4(circuit_3qubit, noise_2qubit):
    circ = circuit_3qubit.add_noise(
        noise_2qubit,
        target_gates="CZ",
        target_qubits=QubitSet(0),
        target_times=None,
        insert_strategy="inclusive",
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
    )

    assert circ == expected


def test_add_noise_2QubitNoise_strict_1(circuit_3qubit, noise_2qubit):
    circ = circuit_3qubit.add_noise(
        noise_2qubit,
        target_gates="CZ",
        target_qubits=QubitSet([1, 2]),
        target_times=range(circuit_3qubit.depth),
        insert_strategy="strict",
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
        .add_instruction(Instruction(noise_2qubit, [1, 2]))
    )

    assert circ == expected


def test_add_noise_2QubitNoise_strict_2(circuit_3qubit, noise_2qubit):
    circ = circuit_3qubit.add_noise(
        noise_2qubit,
        target_gates="CZ",
        target_qubits=QubitSet([2, 1]),
        target_times=[4],
        insert_strategy="strict",
    )

    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.Y(), 1))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.Z(), 2))
        .add_instruction(Instruction(Gate.CZ(), [2, 1]))
        .add_instruction(Instruction(Gate.CNot(), [0, 2]))
        .add_instruction(Instruction(Gate.CZ(), [1, 2]))
    )

    assert circ == expected


def test_add_noise_2QubitNoise_no_targetgates(circuit_3qubit, noise_2qubit):
    circ = circuit_3qubit.add_noise(
        noise_2qubit,
        target_gates=None,
        target_qubits=QubitSet([2, 1]),
        target_times=[4],
        insert_strategy="strict",
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


@pytest.mark.xfail(raises=NotImplementedError)
def test_noiseinsertstrategy_add_1qubit_noise():
    NoiseInsertStrategy._add_1qubit_noise()


@pytest.mark.xfail(raises=NotImplementedError)
def test_noiseinsertstrategy_add_Nqubit_noise():
    NoiseInsertStrategy._add_Nqubit_noise()
