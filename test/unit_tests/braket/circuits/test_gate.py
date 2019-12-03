# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from braket.circuits import Gate, Operator


@pytest.fixture
def gate():
    return Gate(qubit_count=1, ascii_symbols=["foo"])


def test_is_operator(gate):
    assert isinstance(gate, Operator)


@pytest.mark.xfail(raises=ValueError)
def test_qubit_count_lt_one():
    Gate(qubit_count=0, ascii_symbols=[])


@pytest.mark.xfail(raises=ValueError)
def test_none_ascii():
    Gate(qubit_count=1, ascii_symbols=None)


@pytest.mark.xfail(raises=ValueError)
def test_mismatch_length_ascii():
    Gate(qubit_count=1, ascii_symbols=["foo", "bar"])


def test_name(gate):
    expected = gate.__class__.__name__
    assert gate.name == expected


def test_getters():
    qubit_count = 2
    ascii_symbols = ("foo", "bar")
    gate = Gate(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    assert gate.qubit_count == qubit_count
    assert gate.ascii_symbols == ascii_symbols


@pytest.mark.xfail(raises=AttributeError)
def test_qubit_count_setter(gate):
    gate.qubit_count = 10


@pytest.mark.xfail(raises=AttributeError)
def test_ascii_symbols_setter(gate):
    gate.ascii_symbols = ["foo", "bar"]


@pytest.mark.xfail(raises=AttributeError)
def test_name_setter(gate):
    gate.name = "hi"


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_ir_not_implemented_by_default(gate):
    gate.to_ir(None)


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
    x = 1
    assert gate1.matrix_equivalence(x) == NotImplemented


def test_str(gate):
    expected = "{}('qubit_count': {})".format(gate.name, gate.qubit_count)
    assert str(gate) == expected


def test_str_angle():
    gate = Gate.Rx(0.5)
    expected = "{}('angle': {}, 'qubit_count': {})".format(gate.name, gate.angle, gate.qubit_count)
    assert str(gate) == expected


def test_equality():
    gate_1 = Gate(qubit_count=1, ascii_symbols=["foo"])
    gate_2 = Gate(qubit_count=1, ascii_symbols=["foo"])
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
