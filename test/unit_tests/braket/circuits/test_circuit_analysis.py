from collections import Counter

import pytest

from braket.circuits import Circuit, gates
from braket.circuits.circuit import QubitMatch
from braket.circuits.moments import MomentType
from braket.circuits.noises import BitFlip


@pytest.fixture
def mixed_circuit():
    return Circuit().h(0).cnot(0, 1).rx(0, 0.5).h(1)


def test_no_filters_returns_all_gates(mixed_circuit):
    assert mixed_circuit.count() == Counter({"H": 2, "CNot": 1, "Rx": 1})


def test_operator_filter_multiple_mixed_identifiers(mixed_circuit):
    assert mixed_circuit.count(operators=["h", gates.CNot]) == Counter({"H": 2, "CNot": 1})


def test_operator_filter_gate_instance(mixed_circuit):
    assert mixed_circuit.count(operators=gates.CNot()) == Counter({"CNot": 1})


def test_include_gate_noise_type():
    circ = Circuit().h(0)
    circ.apply_gate_noise(BitFlip(0.1))
    result = circ.count(include_types=[MomentType.GATE, MomentType.GATE_NOISE])
    assert result == Counter({"H": 1, "BitFlip": 1})


def test_gate_noise_excluded_by_default():
    circ = Circuit().h(0)
    circ.apply_gate_noise(BitFlip(0.1))
    assert circ.count() == Counter({"H": 1})


def test_qubit_filter_single_qubit(mixed_circuit):
    assert mixed_circuit.count(qubits=0) == Counter({"H": 1, "CNot": 1, "Rx": 1})


def test_qubit_filter_multiple_qubits_any():
    circ = Circuit().h(0).h(2).cnot(0, 1)
    assert circ.count(qubits=[0, 2]) == Counter({"H": 2, "CNot": 1})


def test_qubit_filter_multiple_qubits_all(mixed_circuit):
    assert mixed_circuit.count(qubits=[0, 1], qubit_match=QubitMatch.ALL) == Counter({"CNot": 1})


def test_operator_and_qubit_filters_intersect(mixed_circuit):
    assert mixed_circuit.count(operators="CNot", qubits=[1]) == Counter({"CNot": 1})


def test_unknown_operator_raises(mixed_circuit):
    with pytest.raises(ValueError, match="Unknown operator"):
        mixed_circuit.count(operators="ZZZ")


def test_valid_operator_absent_from_circuit_returns_empty(mixed_circuit):
    assert mixed_circuit.count(operators="S") == Counter()


def test_qubit_not_in_circuit_raises(mixed_circuit):
    with pytest.raises(ValueError, match="not part of the circuit"):
        mixed_circuit.count(qubits=99)


def test_partial_qubits_not_in_circuit_raises(mixed_circuit):
    with pytest.raises(ValueError, match="not part of the circuit"):
        mixed_circuit.count(qubits=[0, 99])


def test_in_circuit_qubit_without_gates_returns_empty():
    circ = Circuit().h(0).measure(1)
    assert circ.count(qubits=1) == Counter()
