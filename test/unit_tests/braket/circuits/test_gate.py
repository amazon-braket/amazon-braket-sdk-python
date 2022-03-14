# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import pytest

from braket.circuits import Gate, QuantumOperator


@pytest.fixture
def gate():
    return Gate(qubit_count=1, ascii_symbols=["foo"])


def test_is_operator(gate):
    assert isinstance(gate, QuantumOperator)


@pytest.mark.xfail(raises=NotImplementedError)
def test_adjoint_expansion_not_implemented_by_default(gate):
    gate.adjoint_expansion()


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_ir_not_implemented_by_default(gate):
    gate.to_ir(None)


@pytest.mark.xfail(raises=ValueError)
def test_to_it_adjoints_in_expansion():
    class Foo(Gate):
        def adjoint_expansion(self):
            return [self.adjoint()]

    Foo(qubit_count=1, ascii_symbols=["foo"]).adjoint().to_ir(None)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_matrix_not_implemented_by_default(gate):
    gate.to_matrix(None)


def test_matrix_equivalence():
    gate1 = Gate.H()
    gate2 = Gate.H()
    gate3 = Gate.CNot()
    assert gate1.matrix_equivalence(gate2)
    assert not gate2.matrix_equivalence(gate3)


def test_matrix_equivalence_non_gate():
    gate1 = Gate.H()
    assert not gate1.matrix_equivalence(1)


def test_str(gate):
    expected = f"{gate.name}('qubit_count': {gate.qubit_count})"
    assert str(gate) == expected


def test_str_angle():
    gate = Gate.Rx(0.5)
    expected = f"{gate.name}('angle': {gate.angle}, 'qubit_count': {gate.qubit_count})"
    assert str(gate) == expected


def test_adjoint():
    gate_1 = Gate(qubit_count=2, ascii_symbols=["foo", "C"])
    gate_2 = Gate(qubit_count=2, ascii_symbols=["foo", "C"]).adjoint()
    adj = gate_1.adjoint()
    assert str(adj) == f"({gate_1.name})†('qubit_count': {gate_1.qubit_count})"
    assert adj.ascii_symbols == ("(foo)†", "C")
    assert gate_1 != adj
    assert adj == gate_2


def test_equality():
    gate_1 = Gate(qubit_count=1, ascii_symbols=["foo"])
    gate_2 = Gate(qubit_count=1, ascii_symbols=["bar"])
    other_gate = Gate.Rx(angle=0.34)
    non_gate = "non gate"

    assert gate_1 == gate_2
    assert gate_1 is not gate_2
    assert gate_1 != other_gate
    assert gate_1 != non_gate


def test_register_gate():
    class _FooGate(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["foo"])

    Gate.register_gate(_FooGate)
    assert Gate._FooGate().name == _FooGate().name
