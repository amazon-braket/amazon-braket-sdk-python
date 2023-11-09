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

"""Tests for the operators module."""

from collections.abc import Callable
from typing import Any

import numpy as np
import oqpy.base
import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.errors import UnsupportedConditionalExpressionError
from braket.experimental.autoqasm.instructions import cnot, h, measure, x


@pytest.fixture
def if_true() -> dict:
    return {"body": lambda: h(0), "qasm": "h __qubits__[0];"}


@pytest.fixture
def if_false() -> dict:
    return {"body": lambda: h(1), "qasm": "h __qubits__[1];"}


def test_conditional_expressions_qasm_cond(if_true: dict, if_false: dict) -> None:
    """Tests aq.operators.if_exp with a QASM condition.

    Args:
        if_true (dict): Fixture for true case.
        if_false (dict): Fixture for false case.
    """
    with aq.build_program() as program_conversion_context:
        qasm_cond = oqpy.BoolVar(True)
        aq.operators.if_exp(qasm_cond, if_true["body"], if_false["body"], expr_repr=None)

    qasm = program_conversion_context.make_program().to_ir()
    assert if_true["qasm"] in qasm
    assert if_false["qasm"] in qasm


def test_conditional_expressions_qasm_measurement(if_true: dict, if_false: dict) -> None:
    """Tests operators.if_exp with a QASM measurement condition.

    Args:
        if_true (dict): Fixture for true case.
        if_false (dict): Fixture for false case.
    """
    with aq.build_program() as program_conversion_context:
        qasm_cond = measure(0)
        aq.operators.if_exp(qasm_cond, if_true["body"], if_false["body"], expr_repr=None)

    qasm = program_conversion_context.make_program().to_ir()
    assert if_true["qasm"] in qasm
    assert if_false["qasm"] in qasm


def test_conditional_expressions_py_cond(if_true: dict, if_false: dict) -> None:
    """Tests aq.operators.if_exp with a Python condition.

    Args:
        if_true (dict): Fixture for true case.
        if_false (dict): Fixture for false case.
    """
    with aq.build_program() as program_conversion_context:
        py_cond = True
        aq.operators.if_exp(py_cond, if_true["body"], if_false["body"], expr_repr=None)

    qasm = program_conversion_context.make_program().to_ir()
    assert str(py_cond) not in qasm
    assert if_true["qasm"] in qasm
    assert if_false["qasm"] not in qasm


def test_inline_conditional_assignment() -> None:
    """Tests conditional expression where the if and else clauses return different types."""

    @aq.main
    def cond_exp_assignment():
        a = aq.IntVar(2) * aq.IntVar(3) if aq.BoolVar(True) else aq.IntVar(4)  # noqa: F841

    expected = """OPENQASM 3.0;
int[32] __int_3__;
int[32] __int_1__ = 2;
int[32] __int_2__ = 3;
bool __bool_0__ = true;
int[32] __int_4__ = 4;
int[32] a;
if (__bool_0__) {
    __int_3__ = __int_1__ * __int_2__;
} else {
    __int_3__ = __int_4__;
}
a = __int_3__;"""

    assert cond_exp_assignment().to_ir() == expected


@pytest.mark.parametrize(
    "else_value",
    [
        lambda: aq.FloatVar(2),
        lambda: aq.BoolVar(False),
        lambda: aq.BitVar(0),
    ],
)
def test_unsupported_inline_conditional_assignment(else_value) -> None:
    """Tests conditional expression where the if and else clauses return different types."""

    @aq.main
    def cond_exp_assignment_different_types():
        a = aq.IntVar(1) if aq.BoolVar(True) else else_value()  # noqa: F841

    with pytest.raises(UnsupportedConditionalExpressionError):
        cond_exp_assignment_different_types()


def test_branch_assignment_undeclared() -> None:
    """Tests if-else branch where an undeclared variable is assigned in both branches."""

    @aq.main
    def branch_assignment_undeclared():
        if aq.BoolVar(True):
            a = aq.IntVar(1)  # noqa: F841
        else:
            a = aq.IntVar(2)  # noqa: F841

    expected = """OPENQASM 3.0;
int[32] a;
bool __bool_0__ = true;
if (__bool_0__) {
    a = 1;
} else {
    a = 2;
}"""

    assert branch_assignment_undeclared().to_ir() == expected


def test_branch_assignment_declared() -> None:
    """Tests if-else branch where a declared variable is assigned in both branches."""

    @aq.main
    def branch_assignment_declared():
        a = aq.IntVar(5)
        if aq.BoolVar(True):
            a = aq.IntVar(6)  # noqa: F841
        else:
            a = aq.IntVar(7)  # noqa: F841

    expected = """OPENQASM 3.0;
bool __bool_1__ = true;
int[32] a = 5;
if (__bool_1__) {
    a = 6;
} else {
    a = 7;
}"""

    assert branch_assignment_declared().to_ir() == expected


def for_body(i: aq.Qubit) -> None:
    h(i)


def test_control_flow_for_loop_qasm() -> None:
    """Tests aq.operators.for_stmt with a QASM iterable."""
    with aq.build_program(aq.program.UserConfig(num_qubits=10)) as program_conversion_context:
        aq.operators.for_stmt(
            iter=aq.types.qasm_range(3),
            extra_test=None,
            body=for_body,
            get_state=None,
            set_state=None,
            symbol_names=None,
            opts={"iterate_names": "idx"},
        )

    qasm = program_conversion_context.make_program().to_ir()
    expected_qasm = """OPENQASM 3.0;
for int idx in [0:3 - 1] {
    h __qubits__[idx];
}"""

    assert qasm == expected_qasm


def test_control_flow_for_loop_py() -> None:
    """Tests aq.operators.for_stmt with a Python iterable."""
    with aq.build_program() as program_conversion_context:
        aq.operators.for_stmt(
            iter=range(3),
            extra_test=None,
            body=for_body,
            get_state=None,
            set_state=None,
            symbol_names=None,
            opts={"iterate_names": "idx"},
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert "for" not in qasm
    for i in range(3):
        assert f"h __qubits__[{i}];" in qasm


def while_test(value: bool) -> Callable[[], bool]:
    return lambda: value


def while_body() -> None:
    cnot(0, 1)


def test_control_flow_while_loop_qasm() -> None:
    """Tests aq.operators.while_stmt with a QASM condition."""
    with aq.build_program() as program_conversion_context:
        qasm_cond = oqpy.BoolVar(False)
        aq.operators.while_stmt(
            test=while_test(qasm_cond),
            body=while_body,
            get_state=None,
            set_state=None,
            symbol_names=None,
            opts=None,
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert "while" in qasm


def test_control_flow_while_loop_py() -> None:
    """Tests aq.operators.while_stmt with a Python condition."""
    with aq.build_program() as program_conversion_context:
        py_cond = False
        aq.operators.while_stmt(
            test=while_test(py_cond),
            body=while_body,
            get_state=None,
            set_state=None,
            symbol_names=None,
            opts=None,
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert str(py_cond) not in qasm
    assert "while" not in qasm


def test_control_flow_if_qasm(if_true: dict, if_false: dict) -> None:
    """Tests aq.operators.if_stmt with a QASM condition.

    Args:
        if_true (dict): Fixture for true case.
        if_false (dict): Fixture for false case.
    """
    with aq.build_program() as program_conversion_context:
        qasm_cond = oqpy.BoolVar(True)
        aq.operators.if_stmt(
            qasm_cond,
            if_true["body"],
            if_false["body"],
            get_state=None,
            set_state=None,
            symbol_names=None,
            nouts=None,
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert if_true["qasm"] in qasm
    assert if_false["qasm"] in qasm


def test_control_flow_if_qasm_measurement(if_true: dict, if_false: dict) -> None:
    """Tests operators.if_stmt with a QASM measurement condition.

    Args:
        if_true (dict): Fixture for true case.
        if_false (dict): Fixture for false case.
    """
    with aq.build_program() as program_conversion_context:
        qasm_cond = measure(0)
        aq.operators.if_stmt(
            qasm_cond,
            if_true["body"],
            if_false["body"],
            get_state=None,
            set_state=None,
            symbol_names=None,
            nouts=None,
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert if_true["qasm"] in qasm
    assert if_false["qasm"] in qasm


def test_control_flow_if_py(if_true: dict, if_false: dict) -> None:
    """Tests aq.operators.if_stmt with a Python condition.

    Args:
        if_true (dict): Fixture for true case.
        if_false (dict): Fixture for false case.
    """
    with aq.build_program() as program_conversion_context:
        py_cond = True
        aq.operators.if_stmt(
            py_cond,
            if_true["body"],
            if_false["body"],
            get_state=None,
            set_state=None,
            symbol_names=None,
            nouts=None,
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert str(py_cond) not in qasm
    assert if_true["qasm"] in qasm
    assert if_false["qasm"] not in qasm


def test_data_structures_new_list() -> None:
    """Tests aq.operators.new_list."""
    assert isinstance(aq.operators.new_list([2, 3, 4]), list)
    assert isinstance(aq.operators.new_list(range(2)), list)
    assert isinstance(aq.operators.new_list(None), list)


def test_logical_eq_py_cond() -> None:
    """Tests aq.operators.eq for Python expressions."""
    with aq.build_program() as program_conversion_context:
        a = 2
        b = 2
        aq.operators.eq(a, b)

    qasm = program_conversion_context.make_program().to_ir()
    assert "==" not in qasm


def test_logical_eq_qasm_cond() -> None:
    """Tests aq.operators.eq for QASM expressions."""
    with aq.build_program() as program_conversion_context:
        a = oqpy.IntVar(2)
        b = 2
        aq.operators.eq(a, b)

    qasm = program_conversion_context.make_program().to_ir()
    assert "==" in qasm


def test_logical_op_and() -> None:
    @aq.subroutine
    def do_and(a: bool, b: bool):
        return a and b

    @aq.main
    def prog():
        do_and(True, False)

    expected = """OPENQASM 3.0;
def do_and(bool a, bool b) -> bool {
    bool __bool_0__;
    __bool_0__ = a && b;
    return __bool_0__;
}
bool __bool_1__;
__bool_1__ = do_and(true, false);"""

    assert prog().to_ir() == expected


def test_logical_op_or() -> None:
    @aq.subroutine
    def do_or(a: bool, b: bool):
        return a or b

    @aq.main
    def prog():
        do_or(True, False)

    expected = """OPENQASM 3.0;
def do_or(bool a, bool b) -> bool {
    bool __bool_0__;
    __bool_0__ = a || b;
    return __bool_0__;
}
bool __bool_1__;
__bool_1__ = do_or(true, false);"""

    assert prog().to_ir() == expected


def test_logical_op_not() -> None:
    @aq.subroutine
    def do_not(a: bool):
        return not a

    @aq.main
    def prog():
        do_not(True)

    expected = """OPENQASM 3.0;
def do_not(bool a) -> bool {
    bool __bool_0__;
    __bool_0__ = !a;
    return __bool_0__;
}
bool __bool_1__;
__bool_1__ = do_not(true);"""

    assert prog().to_ir() == expected


def test_logical_op_eq() -> None:
    @aq.subroutine
    def do_eq(a: int, b: int):
        return a == b

    @aq.main
    def prog():
        do_eq(1, 2)

    expected = """OPENQASM 3.0;
def do_eq(int[32] a, int[32] b) -> bool {
    bool __bool_0__;
    __bool_0__ = a == b;
    return __bool_0__;
}
bool __bool_1__;
__bool_1__ = do_eq(1, 2);"""

    assert prog().to_ir() == expected


def test_logical_op_not_eq() -> None:
    @aq.subroutine
    def do_not_eq(a: int, b: int):
        return a != b

    @aq.main
    def prog():
        do_not_eq(1, 2)

    expected = """OPENQASM 3.0;
def do_not_eq(int[32] a, int[32] b) -> bool {
    bool __bool_0__;
    __bool_0__ = a != b;
    return __bool_0__;
}
bool __bool_1__;
__bool_1__ = do_not_eq(1, 2);"""

    assert prog().to_ir() == expected


def test_logical_ops_py() -> None:
    """Tests the logical aq.operators for Python expressions."""

    @aq.main
    def prog():
        a = True
        b = False
        c = a and b
        d = a or c
        e = not c
        f = a == e
        g = d != f
        assert all([a, not b, not c, d, e, f, not g])

    expected = """OPENQASM 3.0;"""

    assert prog().to_ir() == expected


def test_comparison_lt() -> None:
    """Tests aq.operators.lt_."""

    @aq.main
    def prog():
        a = measure(0)
        if a < 1:
            h(0)

    expected = """OPENQASM 3.0;
bit a;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
a = __bit_0__;
bool __bool_1__;
__bool_1__ = a < 1;
if (__bool_1__) {
    h __qubits__[0];
}"""
    qasm = prog().to_ir()
    assert qasm == expected


def test_comparison_gt() -> None:
    """Tests aq.operators.lt_."""

    @aq.main
    def prog():
        a = measure(0)
        if a > 1:
            h(0)

    expected = """OPENQASM 3.0;
bit a;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
a = __bit_0__;
bool __bool_1__;
__bool_1__ = a > 1;
if (__bool_1__) {
    h __qubits__[0];
}"""
    qasm = prog().to_ir()
    assert qasm == expected


def test_comparison_ops_py() -> None:
    """Tests the comparison aq.operators for Python expressions."""

    @aq.main
    def prog():
        a = 1.2
        b = 12
        c = a < b
        d = a <= b
        e = a > b
        f = a >= b
        g = 1.2
        h = a <= g
        assert all([c, d, not e, not f, h])

    expected = """OPENQASM 3.0;"""
    assert prog().to_ir() == expected


@pytest.mark.parametrize(
    "target", [oqpy.ArrayVar(dimensions=[3], name="arr"), oqpy.BitVar(size=3, name="arr")]
)
def test_slices_get_item_qasm(target) -> None:
    """Tests aq.operators.get_item with QASM target array."""
    with aq.build_program() as program_conversion_context:
        i = 1
        var = aq.operators.get_item(target=target, i=i, opts=aq.operators.GetItemOpts(int))
        assert isinstance(var, oqpy._ClassicalVar)

    qasm = program_conversion_context.make_program().to_ir()
    assert "arr[1]" in qasm


@pytest.mark.parametrize("target", [oqpy.IntVar(size=32), oqpy.FloatVar(size=32)])
def test_slices_get_item_qasm_invalid_target_type(target) -> None:
    """Tests aq.operators.get_item validation on QASM target type."""
    expected_error_message = f"{str(type(target))} object is not subscriptable"

    with aq.build_program():
        i = 1
        with pytest.raises(TypeError) as exc_info:
            _ = aq.operators.get_item(target=target, i=i, opts=aq.operators.GetItemOpts(int))
            assert expected_error_message in str(exc_info.value)


@pytest.mark.parametrize(
    "target", [oqpy.ArrayVar(dimensions=[3], name="arr"), oqpy.BitVar(size=3, name="arr")]
)
def test_slices_get_item_qasm_with_qasm_index(target) -> None:
    """Tests aq.operators.get_item with QASM target array."""
    with aq.build_program() as program_conversion_context:
        i = oqpy.IntVar(name="index")
        var = aq.operators.get_item(target=target, i=i, opts=aq.operators.GetItemOpts(int))
        assert isinstance(var, oqpy._ClassicalVar)

    qasm = program_conversion_context.make_program().to_ir()
    assert "arr[index]" in qasm


def test_slices_get_item_py() -> None:
    """Tests aq.operators.get_item with Python target list."""
    with aq.build_program() as program_conversion_context:
        target = [5, 6, 7]
        i = 1
        var = aq.operators.get_item(target=target, i=i, opts=aq.operators.GetItemOpts(int))
        assert isinstance(var, int)

    qasm = program_conversion_context.make_program().to_ir()
    assert "array" not in qasm


def test_slices_set_item_qasm() -> None:
    """Tests aq.operators.set_item with QASM target array."""
    with aq.build_program() as program_conversion_context:
        i = oqpy.IntVar(1, name="index")
        target = oqpy.BitVar(size=2, name="target")
        new_value = oqpy.BitVar(1, name="x")
        var = aq.operators.set_item(target=target, i=i, x=new_value)

    qasm = program_conversion_context.make_program().to_ir()
    assert "target[index] = 1;" in qasm
    assert var.__dict__ == target.__dict__


def test_slices_set_item_py() -> None:
    """Tests aq.operators.set_item with Python target list."""
    target = [5, 6, 7]
    i = 1
    new_value = 0
    var = aq.operators.set_item(target=target, i=i, x=new_value)
    assert isinstance(var, list)
    assert var[i] == new_value


def test_slice_bits() -> None:
    """Test that bit var slicing and assignment works when assigning to a
    size 1 bit."""

    @aq.main
    def slice():
        a = aq.BitVar(0, size=6)
        b = aq.BitVar(1)
        a[3] = b

    expected = """OPENQASM 3.0;
bit[6] a = "000000";
bit b = 1;
a[3] = b;"""

    assert slice().to_ir() == expected


def test_slice_bits_w_measure() -> None:
    """Test assignment of one bit in an array to a measurement result."""

    @aq.main
    def measure_to_slice():
        b0 = aq.BitVar(size=10)
        c = measure(0)
        b0[3] = c

    expected = """OPENQASM 3.0;
bit c;
qubit[1] __qubits__;
bit[10] b0 = "0000000000";
bit __bit_1__;
__bit_1__ = measure __qubits__[0];
c = __bit_1__;
b0[3] = c;"""

    assert measure_to_slice().to_ir() == expected


@pytest.mark.parametrize(
    "target_name,value,expected_qasm",
    [
        ("foo", oqpy.IntVar(5), "\nint[32] foo = 5;"),
        ("bar", oqpy.FloatVar(1.2), "\nfloat[64] bar = 1.2;"),
        ("baz", oqpy.BitVar(0), "\nbit baz = 0;"),
    ],
)
def test_assignment_qasm_undeclared_target(
    target_name: str, value: oqpy.base.Var, expected_qasm: str
) -> None:
    """Tests operators.assign_stmt with a QASM assignment value that is
    undeclared in the program.

    Args:
        target_name (str): Name of the assignment target.
        value (oqpy.base.Var): Assignment value.
        expected_qasm (str): Expected QASM script.
    """
    with aq.build_program() as program_conversion_context:
        _ = aq.operators.assign_stmt(
            target_name=target_name,
            value=value,
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert expected_qasm in qasm


@pytest.mark.parametrize(
    "target_name,value,expected_qasm",
    [
        ("foo", oqpy.IntVar(5), "\nfoo = 5;"),
        ("bar", oqpy.FloatVar(1.2), "\nbar = 1.2;"),
        ("baz", oqpy.BitVar(0), "\nbaz = 0;"),
    ],
)
def test_assignment_qasm_declared_target(
    target_name: str, value: oqpy.base.Var, expected_qasm: str
) -> None:
    """Tests operators.assign_stmt with a QASM assignment value that is
    declared in the program.

    Args:
        target_name (str): Name of the assignment target.
        value (oqpy.base.Var): Assignment value.
        expected_qasm (str): Expected QASM script.
    """
    with aq.build_program() as program_conversion_context:
        oqpy_program = program_conversion_context.get_oqpy_program()
        var = type(value)(name=target_name)
        oqpy_program.declare(var)

        _ = aq.operators.assign_stmt(
            target_name=target_name,
            value=value,
        )

    qasm = program_conversion_context.make_program().to_ir()
    assert expected_qasm in qasm


@pytest.mark.parametrize(
    "target_name,declared_var,value,expected_error_message",
    [
        (
            "a",
            oqpy.BitVar(name="a", size=2),
            oqpy.BitVar(name="a", size=3),
            "Variables in assignment statements must have the same size",
        ),
        (
            "a",
            oqpy.BitVar(name="a"),
            oqpy.IntVar(name="a"),
            "Variables in assignment statements must have the same type",
        ),
    ],
)
def test_assignment_qasm_invalid_size_type(
    target_name, declared_var, value, expected_error_message
) -> None:
    """Tests operators.assign_stmt validation against variable size and type."""
    with aq.build_program() as program_conversion_context:
        oqpy_program = program_conversion_context.get_oqpy_program()
        oqpy_program.declare(declared_var)

        with pytest.raises(errors.InvalidAssignmentStatement) as exc_info:
            _ = aq.operators.assign_stmt(
                target_name=target_name,
                value=value,
            )
    assert str(exc_info.value) == expected_error_message


def test_assignment_measurement() -> None:
    """Tests operators.assign_stmt with a Measurement being the
    assignment value.
    """
    target_name = "foo"
    with aq.build_program():
        new_value = aq.operators.assign_stmt(
            target_name=target_name,
            value=measure(3),
        )
    assert isinstance(new_value, oqpy.BitVar)


@pytest.mark.parametrize("value", [0, 2.6, True])
def test_assignment_py(value: Any) -> None:
    """Tests operators.assign_stmt with a python assignment value.

    Args:
        value (Any): Assignment value.
    """
    with aq.build_program():
        new_value = aq.operators.assign_stmt(
            target_name="foo",
            value=value,
        )
    assert new_value == value


@pytest.mark.parametrize("value", [0, 1])
def test_py_if_stmt(value: int) -> None:
    """Test Python if branches on true and false conditions."""

    @aq.main
    def test_control_flow(a: int):
        "Quick if statement test"
        if a:
            h(0)
        else:
            x(0)

    expected = """OPENQASM 3.0;
qubit[1] __qubits__;
{} __qubits__[0];""".format(
        "h" if value else "x"
    )
    assert test_control_flow(value).to_ir() == expected


def test_py_while() -> None:
    """Test Python while loop."""

    @aq.main
    def test_control_flow():
        "Quick while loop test"
        a = 3
        while a >= 2:
            a -= 1
            h(0)

    expected = """OPENQASM 3.0;
qubit[1] __qubits__;
h __qubits__[0];
h __qubits__[0];"""

    assert test_control_flow().to_ir() == expected


def test_py_assert() -> None:
    """Test Python assertions inside an AutoQASM program."""

    @aq.main
    def test_assert(value: bool):
        assert value

    test_assert(True)
    with pytest.raises(AssertionError):
        test_assert(False)


def test_measurement_assert() -> None:
    """Test assertions on measurement results inside an AutoQASM program."""

    @aq.main
    def test_assert():
        assert measure(0)

    with pytest.raises(NotImplementedError):
        test_assert()


def test_py_list_ops() -> None:
    """Test Python list operations inside an AutoQASM program."""

    @aq.main
    def test_list_ops():
        a = [1, 2, 3]
        a.append(4)
        b = a.pop(0)
        assert b == 1
        c = np.stack([a, a])
        assert np.array_equal(c, [[2, 3, 4], [2, 3, 4]])

    test_list_ops()
