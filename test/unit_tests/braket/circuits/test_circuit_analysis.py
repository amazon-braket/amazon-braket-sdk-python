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


def test_include_gate_noise_type():
    circ = Circuit().h(0)
    circ.apply_gate_noise(BitFlip(0.1))
    result = circ.count(include_types=[MomentType.GATE, MomentType.GATE_NOISE])
    assert result == Counter({"H": 1, "BitFlip": 1})


def test_qubit_filter_single_qubit(mixed_circuit):
    assert mixed_circuit.count(qubits=0) == Counter({"H": 1, "CNot": 1, "Rx": 1})


def test_qubit_filter_multiple_qubits_any():
    circ = Circuit().h(0).h(2).cnot(0, 1)
    assert circ.count(qubits=[0, 2]) == Counter({"H": 2, "CNot": 1})


def test_qubit_filter_multiple_qubits_all(mixed_circuit):
    assert mixed_circuit.count(qubits=[0, 1], qubit_match=QubitMatch.ALL) == Counter({"CNot": 1})


def test_operator_and_qubit_filters_intersect(mixed_circuit):
    assert mixed_circuit.count(operators="CNot", qubits=[1]) == Counter({"CNot": 1})


def test_unknown_operator_returns_empty(mixed_circuit):
    assert mixed_circuit.count(operators="ZZZ") == Counter()


def test_qubit_not_in_circuit_returns_empty(mixed_circuit):
    assert mixed_circuit.count(qubits=99) == Counter()


def test_partial_qubits_not_in_circuit_any(mixed_circuit):
    assert mixed_circuit.count(qubits=[0, 99]) == Counter({"H": 1, "CNot": 1, "Rx": 1})


def test_partial_qubits_not_in_circuit_all(mixed_circuit):
    assert mixed_circuit.count(qubits=[0, 99], qubit_match=QubitMatch.ALL) == Counter()
