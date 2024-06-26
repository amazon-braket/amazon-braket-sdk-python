import re

import pytest
from pytket.circuit import Bit, Circuit, OpType
from sympy import Symbol

from braket.emulators.pytket_translator import tket_to_qasm3


@pytest.fixture
def simple_bell_circuit():
    circ = Circuit(3)
    for i in range(3):
        circ.add_bit(Bit("c", i))
    circ.Rx(0.5, 0)
    circ.H(0)
    circ.CX(1, 2)
    circ.CX(0, 1)
    circ.Measure(0, 0)
    circ.Measure(1, 1)
    circ.Measure(2, 2)
    return circ


@pytest.fixture
def simple_parametric_circuit():
    circ = Circuit(1)
    circ.add_bit(Bit("c", 0))
    circ.Rx(Symbol("theta"), 0)
    circ.Measure(0, 0)
    return circ


def test_simple_bell(simple_bell_circuit):
    expected = """
OPENQASM 3.0;
bit[3] c;
rx(0.5*pi) $0;
cnot $1,$2;
h $0;
cnot $0,$1;
c[2] = measure $2;
c[0] = measure $0;
c[1] = measure $1;
""".strip()
    qasm_result = tket_to_qasm3(simple_bell_circuit).strip()
    assert qasm_result == expected


def test_parametric_circuit(simple_parametric_circuit):
    expected = """
OPENQASM 3.0;
input float theta;
bit[1] c;
rx(pi*theta) $0;
c[0] = measure $0;
""".strip()
    qasm_result = tket_to_qasm3(simple_parametric_circuit).strip()
    assert expected == qasm_result


def test_empty_circuit():
    circ = Circuit(0)
    expected = """OPENQASM 3.0;
"""
    qasm_result = tket_to_qasm3(circ)
    assert expected == qasm_result


def test_multiple_parameter_circuits():
    theta = Symbol("theta")
    phi = Symbol("phi")
    circ = Circuit(1)
    circ.add_bit(Bit("c", 0))
    circ.Rx(theta, 0)
    circ.Rx(theta + phi, 0)
    expected = """
OPENQASM 3.0;
input float theta;
input float phi;
bit[1] c;
rx(pi*theta) $0;
rx(pi*(phi + theta)) $0;
""".strip()
    qasm_result = tket_to_qasm3(circ).strip()
    assert expected == qasm_result


def test_invalid_operation_on_measured_targets():
    circ = Circuit(1)
    circ.add_bit(Bit("c", 0))
    circ.Measure(0, 0)
    circ.X(0)

    error_message = re.escape(
        "Circuit QASM cannot be generated as circuit contains midcircuit\
            measurements on qubit: q[0]"
    )
    with pytest.raises(ValueError, match=error_message):
        tket_to_qasm3(circ)


def test_translation_with_gate_overrides(simple_bell_circuit):
    gate_override = {OpType.CX: "CNOT", OpType.H: "HADAMARD"}
    expected = """
OPENQASM 3.0;
bit[3] c;
rx(0.5*pi) $0;
CNOT $1,$2;
HADAMARD $0;
CNOT $0,$1;
c[2] = measure $2;
c[0] = measure $0;
c[1] = measure $1;
""".strip()
    qasm_result = tket_to_qasm3(simple_bell_circuit, gate_overrides=gate_override).strip()
    assert qasm_result == expected
