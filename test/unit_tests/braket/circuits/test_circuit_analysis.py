from collections import Counter

import pytest

from braket.circuits import Circuit, gates
from braket.circuits.circuit_analysis import QubitMatch, count_instructions
from braket.circuits.moments import MomentType
from braket.circuits.noises import BitFlip


@pytest.fixture
def mixed_circuit():
    return Circuit().h(0).cnot(0, 1).rx(0, 0.5).h(1)


def test_qubit_match_values():
    assert QubitMatch.ANY == "ANY"
    assert QubitMatch.ALL == "ALL"


def test_qubit_match_accepts_string_literal():
    assert "ANY" == QubitMatch.ANY
    assert "ALL" == QubitMatch.ALL


def test_no_filters_returns_all_gates(mixed_circuit):
    result = count_instructions(mixed_circuit)
    assert result == Counter({"H": 2, "CNot": 1, "Rx": 1})


def test_no_filters_empty_circuit():
    result = count_instructions(Circuit())
    assert result == Counter()


def test_default_include_types_excludes_gate_noise():
    circ = Circuit().h(0)
    circ.apply_gate_noise(BitFlip(0.1))
    result = count_instructions(circ)
    assert result == Counter({"H": 1})
    assert "BitFlip" not in result


def test_include_gate_noise_type():
    circ = Circuit().h(0)
    circ.apply_gate_noise(BitFlip(0.1))
    result = count_instructions(circ, include_types=[MomentType.GATE, MomentType.GATE_NOISE])
    assert result["H"] == 1
    assert result["BitFlip"] == 1


def test_operator_filter_uppercase_string(mixed_circuit):
    result = count_instructions(mixed_circuit, operators="H")
    assert result == Counter({"H": 2})


def test_operator_filter_lowercase_string(mixed_circuit):
    result = count_instructions(mixed_circuit, operators="h")
    assert result == Counter({"H": 2})


def test_operator_filter_mixed_case_string(mixed_circuit):
    result = count_instructions(mixed_circuit, operators="cNoT")
    assert result == Counter({"CNot": 1})


def test_operator_filter_gate_class(mixed_circuit):
    result = count_instructions(mixed_circuit, operators=gates.CNot)
    assert result == Counter({"CNot": 1})


def test_operator_filter_gate_instance(mixed_circuit):
    result = count_instructions(mixed_circuit, operators=gates.CNot())
    assert result == Counter({"CNot": 1})


def test_operator_filter_multiple_or(mixed_circuit):
    result = count_instructions(mixed_circuit, operators=["H", "CNot"])
    assert result == Counter({"H": 2, "CNot": 1})


def test_operator_filter_multiple_mixed_identifiers(mixed_circuit):
    result = count_instructions(mixed_circuit, operators=["h", gates.CNot])
    assert result == Counter({"H": 2, "CNot": 1})


def test_operator_filter_unknown_name_returns_empty(mixed_circuit):
    result = count_instructions(mixed_circuit, operators="ZZZ")
    assert result == Counter()


def test_operators_empty_list_is_no_filter(mixed_circuit):
    assert count_instructions(mixed_circuit, operators=[]) == count_instructions(mixed_circuit)


def test_qubits_empty_list_is_no_filter(mixed_circuit):
    assert count_instructions(mixed_circuit, qubits=[]) == count_instructions(mixed_circuit)


def test_operator_empty_list_and_qubits_empty_list_is_no_filter(mixed_circuit):
    assert count_instructions(mixed_circuit, operators=[], qubits=[]) == count_instructions(
        mixed_circuit
    )


def test_qubit_filter_single_qubit():
    circ = Circuit().h(0).cnot(0, 1).rx(1, 0.5)
    result = count_instructions(circ, qubits=0)
    assert result == Counter({"H": 1, "CNot": 1})


def test_qubit_filter_multiple_qubits_any():
    circ = Circuit().h(0).h(2).cnot(0, 1)
    result = count_instructions(circ, qubits=[0, 2])
    assert result == Counter({"H": 2, "CNot": 1})


def test_qubit_filter_multiple_qubits_all():
    circ = Circuit().h(0).h(1).cnot(0, 1)
    result = count_instructions(circ, qubits=[0, 1], qubit_match=QubitMatch.ALL)
    assert result == Counter({"CNot": 1})


def test_qubit_filter_no_match():
    circ = Circuit().h(0).h(1)
    result = count_instructions(circ, qubits=5)
    assert result == Counter()


def test_both_filters_counts_intersection():
    circ = Circuit().h(0).rx(1, 0.5).cnot(0, 1)
    result = count_instructions(circ, operators="CNot", qubits=[1])
    assert result == Counter({"CNot": 1})


def test_both_filters_no_overlap():
    circ = Circuit().h(0).rx(1, 0.5)
    result = count_instructions(circ, operators="H", qubits=[1])
    assert result == Counter()


def test_only_qubit_filter_no_operator_filter():
    circ = Circuit().h(0).cnot(0, 1)
    result = count_instructions(circ, qubits=[0])
    assert result == Counter({"H": 1, "CNot": 1})


def test_only_operator_filter_no_qubit_filter():
    circ = Circuit().h(0).h(1)
    result = count_instructions(circ, operators="H")
    assert result == Counter({"H": 2})


def test_circuit_method_matches_standalone(mixed_circuit):
    assert mixed_circuit.count_instructions() == count_instructions(mixed_circuit)


def test_circuit_method_positional_single_operator(mixed_circuit):
    assert mixed_circuit.count_instructions("H") == Counter({"H": 2})


def test_circuit_method_positional_list_of_operators(mixed_circuit):
    assert mixed_circuit.count_instructions(["H", "CNot"]) == Counter({"H": 2, "CNot": 1})


def test_circuit_method_passes_kwargs(mixed_circuit):
    expected = count_instructions(mixed_circuit, operators="H", qubits=[0])
    actual = mixed_circuit.count_instructions(operators="H", qubits=[0])
    assert expected == actual


def test_qubit_match_importable_from_braket_circuits():
    from braket.circuits import QubitMatch as QM

    assert QM.ANY == "ANY"
