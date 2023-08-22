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

"""AutoQASM tests exercising the @aq.gate decorator and related functionality.
"""

import pytest
from test_api import _test_on_local_sim

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.instructions import h, measure, rx, rz, x


@aq.gate
def empty_gate(q: aq.Qubit):
    pass


def test_empty_gate() -> None:
    @aq.function
    def my_program():
        empty_gate(0)

    expected = """OPENQASM 3.0;
gate empty_gate q {
}
qubit[1] __qubits__;
empty_gate __qubits__[0];"""

    program = my_program()
    assert program.to_ir() == expected

    _test_on_local_sim(program)


def test_double_gate_decorator() -> None:
    double_decorated = aq.gate(empty_gate)

    @aq.function
    def my_program():
        double_decorated(0)

    expected = """OPENQASM 3.0;
gate empty_gate q {
}
qubit[1] __qubits__;
empty_gate __qubits__[0];"""

    program = my_program()
    assert program.to_ir() == expected


def test_gate_class() -> None:
    """Tests the aq.gate decorator on something that is not a function."""

    @aq.gate
    class MyGate:
        def __init__(self, q: aq.Qubit):
            h(q)

    @aq.function
    def main():
        MyGate(0)

    with pytest.raises(ValueError):
        main()


def test_invalid_symbol() -> None:
    @aq.gate
    def my_gate(q: aq.Qubit):
        h(q)
        not_a_symbol()  # noqa: F821

    @aq.function
    def main():
        my_gate(0)

    with pytest.raises(NameError):
        main()


def test_incorrect_arg_count() -> None:
    @aq.gate
    def my_gate(q0: aq.Qubit, q1: aq.Qubit):
        h(q0)
        x(q1)

    @aq.function
    def incorrect_arg_count():
        my_gate(0)

    with pytest.raises(
        errors.ParameterTypeError,
        match='Incorrect number of arguments passed to gate "my_gate". ' "Expected 2, got 1.",
    ):
        incorrect_arg_count()


def test_incorrect_arg_types() -> None:
    @aq.gate
    def my_gate(q: aq.Qubit, theta: float):
        h(q)
        rx(q, theta)

    @aq.function
    def incorrect_arg_types():
        my_gate(0.25, 0)

    with pytest.raises(TypeError):
        incorrect_arg_types()


def test_missing_annotation() -> None:
    @aq.gate
    def my_gate(a):
        pass

    @aq.function
    def my_program():
        my_gate("test")

    with pytest.raises(errors.MissingParameterTypeError):
        my_program()


def test_incorrect_annotation() -> None:
    @aq.gate
    def my_gate(a: str):
        pass

    @aq.function
    def my_program():
        my_gate("test")

    with pytest.raises(errors.ParameterTypeError):
        my_program()


def test_no_qubit_args() -> None:
    @aq.gate
    def not_a_gate(angle: float):
        pass

    @aq.function
    def my_program():
        not_a_gate(aq.pi)

    with pytest.raises(
        errors.ParameterTypeError,
        match='Gate definition "not_a_gate" has no arguments of type aq.Qubit.',
    ):
        my_program()


def test_invalid_qubit_used() -> None:
    @aq.gate
    def my_gate(q: aq.Qubit):
        h(q)
        x(1)  # invalid

    @aq.function
    def my_program():
        my_gate(0)

    with pytest.raises(
        errors.InvalidGateDefinition,
        match='Gate definition "my_gate" uses qubit "1" which is not an argument to the gate.',
    ):
        my_program()


def test_nested_gates() -> None:
    @aq.gate
    def t(q: aq.Qubit):
        rz(q, aq.pi / 4)

    @aq.gate
    def my_gate(q: aq.Qubit, theta: float):
        h(q)
        t(q)
        rx(q, theta)

    @aq.function
    def my_program():
        my_gate(0, aq.pi / 4)
        my_gate(1, 3 * aq.pi / 4)
        measure([0, 1])

    expected = """OPENQASM 3.0;
gate t q {
    rz(pi / 4) q;
}
gate my_gate(theta) q {
    h q;
    t q;
    rx(theta) q;
}
qubit[2] __qubits__;
my_gate(pi / 4) __qubits__[0];
my_gate(3 * pi / 4) __qubits__[1];
bit[2] __bit_0__ = "00";
__bit_0__[0] = measure __qubits__[0];
__bit_0__[1] = measure __qubits__[1];"""

    program = my_program()
    assert program.to_ir() == expected

    _test_on_local_sim(program)


def test_gate_called_from_subroutine() -> None:
    @aq.gate
    def t(q: aq.Qubit):
        rz(q, aq.pi / 4)

    @aq.function
    def subroutine(q0: int, q1: int):
        t(q0)
        t(q1)

    @aq.function(num_qubits=4)
    def main():
        subroutine(0, 1)
        subroutine(2, 3)

    expected = """OPENQASM 3.0;
def subroutine(int[32] q0, int[32] q1) {
    t __qubits__[q0];
    t __qubits__[q1];
}
gate t q {
    rz(pi / 4) q;
}
qubit[4] __qubits__;
subroutine(0, 1);
subroutine(2, 3);"""

    program = main()
    assert program.to_ir() == expected


def test_gate_declaration_only() -> None:
    @aq.gate(declaration_only=True)
    def my_gate(q: aq.Qubit):
        pass

    @aq.function
    def main():
        h(0)
        my_gate(0)

    expected = """OPENQASM 3.0;
qubit[1] __qubits__;
h __qubits__[0];
my_gate __qubits__[0];"""

    program = main()
    assert program.to_ir() == expected
