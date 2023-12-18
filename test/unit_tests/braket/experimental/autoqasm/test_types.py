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

"""Tests for the types module."""

import oqpy
import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.types import Range


@pytest.mark.parametrize(
    "range_params, expected_range_params",
    [
        ((0, 5, 1), (0, 5, 1)),
        ((5, None, 2), (0, 5, 2)),
    ],
)
def test_range(
    range_params: tuple[int, int, int], expected_range_params: tuple[int, int, int]
) -> None:
    """Test `Range()` returning correct `Range` object.

    Args:
        range_params (tuple[int, int, int]): Range parameters to instantiate `Range`
        expected_range_params (tuple[int, int, int]): Expected range parameters
    """
    start, stop, step = range_params
    qrange = Range(start, stop, step)
    assert isinstance(qrange, oqpy.Range)
    assert (qrange.start, qrange.stop, qrange.step) == expected_range_params


def test_return_bit():
    """Test type discovery of bit return values."""

    @aq.subroutine
    def ret_test() -> aq.BitVar:
        res = aq.BitVar(1)
        return res

    @aq.main
    def main() -> aq.BitVar:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> bit {
    bit res = 1;
    return res;
}
bit __bit_1__;
__bit_1__ = ret_test();"""

    assert main.to_ir() == expected


def test_return_int():
    """Test type discovery of int return values."""

    @aq.subroutine
    def ret_test() -> int:
        res = aq.IntVar(1)
        return res

    @aq.main
    def main() -> int:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> int[32] {
    int[32] res = 1;
    return res;
}
int[32] __int_1__;
__int_1__ = ret_test();"""

    assert main.to_ir() == expected


def test_return_float():
    """Test type discovery of float return values."""

    @aq.subroutine
    def ret_test() -> float:
        res = aq.FloatVar(1.0)
        return res

    @aq.main
    def main() -> float:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> float[64] {
    float[64] res = 1.0;
    return res;
}
float[64] __float_1__;
__float_1__ = ret_test();"""

    assert main.to_ir() == expected


def test_return_bool():
    """Test type discovery of boolean return values."""

    @aq.subroutine
    def ret_test() -> bool:
        res = aq.BoolVar(True)
        return res

    @aq.main
    def main() -> bool:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> bool {
    bool res = true;
    return res;
}
bool __bool_1__;
__bool_1__ = ret_test();"""

    assert main.to_ir() == expected


def test_return_bin_expr():
    """Test type discovery of int return values from an expression."""

    @aq.subroutine
    def add(a: int, b: int) -> int:
        return a + b

    @aq.main
    def ret_test() -> int:
        a = aq.IntVar(5)
        b = aq.IntVar(6)
        return add(a, b)

    expected = """OPENQASM 3.0;
def add(int[32] a, int[32] b) -> int[32] {
    return a + b;
}
int[32] a = 5;
int[32] b = 6;
int[32] __int_2__;
__int_2__ = add(a, b);"""

    assert ret_test.to_ir() == expected


def test_return_none():
    """Test discovery of None return annotation."""

    @aq.main
    def ret_test() -> None:
        return None

    expected = "OPENQASM 3.0;"

    assert ret_test.to_ir() == expected


def test_declare_array():
    """Test declaring and assigning an array."""

    @aq.main
    def declare_array():
        a = aq.ArrayVar([1, 2, 3], base_type=aq.IntVar, dimensions=[3])
        a[0] = 11
        b = aq.ArrayVar([4, 5, 6], base_type=aq.IntVar, dimensions=[3])
        b[2] = 14
        b = a

    expected = """OPENQASM 3.0;
array[int[32], 3] a = {1, 2, 3};
a[0] = 11;
array[int[32], 3] b = {4, 5, 6};
b[2] = 14;
b = a;"""

    assert declare_array.to_ir() == expected


def test_invalid_array_assignment():
    """Test invalid array assignment."""
    with pytest.raises(aq.errors.InvalidAssignmentStatement):

        @aq.main
        def invalid():
            a = aq.ArrayVar([1, 2, 3], base_type=aq.IntVar, dimensions=[3])
            b = aq.ArrayVar([4, 5], base_type=aq.IntVar, dimensions=[2])
            a = b  # noqa: F841


def test_declare_array_in_local_scope():
    """Test declaring an array inside a local scope."""
    with pytest.raises(aq.errors.InvalidArrayDeclaration):

        @aq.main
        def declare_array():
            if aq.BoolVar(True):
                _ = aq.ArrayVar([1, 2, 3], base_type=aq.IntVar, dimensions=[3])


def test_declare_array_in_subroutine():
    """Test declaring an array inside a subroutine."""

    @aq.subroutine
    def declare_array():
        _ = aq.ArrayVar([1, 2, 3], dimensions=[3])

    with pytest.raises(aq.errors.InvalidArrayDeclaration):

        @aq.main
        def main() -> list[int]:
            return declare_array()


def test_return_python_array():
    """Test returning a python array of ints."""

    @aq.subroutine
    def tester() -> list[int]:
        return [1, 2, 3]

    with pytest.raises(aq.errors.UnsupportedSubroutineReturnType):

        @aq.main(num_qubits=4)
        def main():
            tester()


def test_return_array_unsupported():
    """Test unsupported array type."""

    @aq.subroutine
    def tester(arr: list[float]) -> list[float]:
        return [1.2, 2.1]

    with pytest.raises(aq.errors.ParameterTypeError):

        @aq.main(num_qubits=4)
        def main():
            tester([3.3])


def test_return_func_call():
    """Test returning the result of another function call."""

    @aq.subroutine
    def helper() -> int:
        res = aq.IntVar(1)
        return res

    @aq.main
    def ret_test() -> int:
        return helper()

    expected = """OPENQASM 3.0;
def helper() -> int[32] {
    int[32] res = 1;
    return res;
}
int[32] __int_1__;
__int_1__ = helper();"""

    assert ret_test.to_ir() == expected


def test_map_bool():
    """Test boolean input parameter type."""

    @aq.subroutine
    def annotation_test(input: bool):
        pass

    @aq.main
    def main():
        annotation_test(True)

    expected = """OPENQASM 3.0;
def annotation_test(bool input) {
}
annotation_test(true);"""

    assert main.to_ir() == expected


def test_map_int():
    """Test integer input parameter type."""

    @aq.subroutine
    def annotation_test(input: int):
        pass

    @aq.main
    def main():
        annotation_test(1)

    expected = """OPENQASM 3.0;
def annotation_test(int[32] input) {
}
annotation_test(1);"""

    assert main.to_ir() == expected


def test_map_float():
    """Test float input parameter type."""

    @aq.subroutine
    def annotation_test(input: float):
        pass

    @aq.main
    def main():
        annotation_test(1.0)

    expected = """OPENQASM 3.0;
def annotation_test(float[64] input) {
}
annotation_test(1.0);"""

    assert main.to_ir() == expected


def test_map_array():
    """Test array input parameter type."""

    @aq.subroutine
    def annotation_test(input: list[int]):
        pass

    with pytest.raises(aq.errors.ParameterTypeError):

        @aq.main
        def main():
            a = aq.ArrayVar([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dimensions=[10])
            annotation_test(a)


def test_map_other():
    """Test unexpected input parameter type handling."""

    @aq.subroutine
    def annotation_test(input: aq.BitVar):
        pass

    @aq.main
    def main():
        a = aq.BitVar(1)
        annotation_test(a)

    expected = """OPENQASM 3.0;
def annotation_test(bit input) {
}
bit a = 1;
annotation_test(a);"""

    assert main.to_ir() == expected


def test_map_other_unnamed_arg():
    """Test unexpected input parameter type handling with unnamed arg."""

    @aq.subroutine
    def annotation_test(input: aq.BitVar):
        pass

    @aq.main
    def main():
        annotation_test(aq.BitVar(1))

    expected = """OPENQASM 3.0;
def annotation_test(bit input) {
}
bit __bit_0__ = 1;
annotation_test(__bit_0__);"""

    assert main.to_ir() == expected


def test_map_and_assign_arg():
    """Test input parameter handling which is assigned to another variable."""

    @aq.subroutine
    def assign_param(c: int) -> None:
        d = aq.IntVar(4)
        c = d  # noqa: F841

    @aq.main
    def main():
        c = aq.IntVar(0)
        assign_param(c)

    expected = """OPENQASM 3.0;
def assign_param(int[32] c) {
    int[32] d = 4;
    c = d;
}
int[32] c = 0;
assign_param(c);"""

    assert main.to_ir() == expected


def test_unnamed_retval_python_type() -> None:
    """Tests subroutines which return unnamed Python values."""

    @aq.subroutine
    def retval_test() -> int:
        return 1

    @aq.main
    def caller() -> int:
        return retval_test()

    expected_qasm = """OPENQASM 3.0;
def retval_test() -> int[32] {
    int[32] retval_ = 1;
    return retval_;
}
int[32] __int_1__;
__int_1__ = retval_test();"""

    assert caller.to_ir() == expected_qasm


def test_unnamed_retval_qasm_type() -> None:
    """Tests subroutines which return unnamed QASM values."""

    @aq.subroutine
    def retval_test() -> aq.BitVar:
        return aq.BitVar(1)

    @aq.main
    def caller() -> aq.BitVar:
        return retval_test()

    expected_qasm = """OPENQASM 3.0;
def retval_test() -> bit {
    bit retval_ = 1;
    return retval_;
}
bit __bit_1__;
__bit_1__ = retval_test();"""

    assert caller.to_ir() == expected_qasm


def test_recursive_unassigned_retval_python_type() -> None:
    """Tests recursive subroutines which do not assign the return value to a variable."""

    @aq.subroutine
    def retval_recursive() -> int:
        retval_recursive()
        return 1

    @aq.main
    def main():
        retval_recursive()

    expected_qasm = """OPENQASM 3.0;
def retval_recursive() -> int[32] {
    int[32] __int_1__;
    __int_1__ = retval_recursive();
    int[32] retval_ = 1;
    return retval_;
}
int[32] __int_3__;
__int_3__ = retval_recursive();"""

    assert main.to_ir() == expected_qasm


def test_recursive_assigned_retval_python_type() -> None:
    """Tests recursive subroutines which assign the return value to a variable."""

    @aq.subroutine
    def retval_recursive() -> int:
        a = retval_recursive()  # noqa: F841
        return 1

    @aq.main
    def main():
        retval_recursive()

    expected_qasm = """OPENQASM 3.0;
def retval_recursive() -> int[32] {
    int[32] a;
    int[32] __int_1__;
    __int_1__ = retval_recursive();
    a = __int_1__;
    int[32] retval_ = 1;
    return retval_;
}
int[32] __int_3__;
__int_3__ = retval_recursive();"""

    assert main.to_ir() == expected_qasm


def test_recursive_retval_expression_python_type() -> None:
    """Tests recursive subroutines which use the return value in an expression."""

    @aq.subroutine
    def retval_constant() -> int:
        return 3

    @aq.subroutine
    def retval_recursive() -> float:
        a = 2 * retval_recursive() + (retval_constant() + 2) / 3
        return a

    @aq.main
    def caller() -> int:
        return retval_recursive()

    expected_qasm = """OPENQASM 3.0;
def retval_recursive() -> float[64] {
    float[64] __float_1__;
    __float_1__ = retval_recursive();
    int[32] __int_3__;
    __int_3__ = retval_constant();
    return 2 * __float_1__ + (__int_3__ + 2) / 3;
}
def retval_constant() -> int[32] {
    int[32] retval_ = 3;
    return retval_;
}
float[64] __float_4__;
__float_4__ = retval_recursive();"""

    assert caller.to_ir() == expected_qasm


def test_recursive_oqpy_type() -> None:
    """Tests recursive subroutines which returns an oqpy type."""

    @aq.subroutine
    def retval_recursive() -> aq.BitVar:
        retval_recursive()
        return aq.BitVar(0)

    @aq.main
    def main():
        retval_recursive()

    assert "-> bit" in main.to_ir()


def test_error_for_tuple_param() -> None:
    """Tuples are not supported as parameters."""

    @aq.subroutine
    def param_test(input: tuple):
        pass

    with pytest.raises(aq.errors.ParameterTypeError):

        @aq.main
        def main():
            param_test(aq.BitVar(1))


def test_error_for_missing_param_type() -> None:
    """Parameters require type hints."""

    @aq.subroutine
    def param_test(input):
        pass

    with pytest.raises(aq.errors.MissingParameterTypeError):

        @aq.main
        def main():
            param_test(aq.BitVar(1))


def test_ignore_ret_typehint_bool():
    """Test type discovery of boolean return values."""

    @aq.subroutine
    def ret_test() -> list[int]:
        return True

    @aq.main
    def main() -> bool:
        ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> bool {
    bool retval_ = true;
    return retval_;
}
bool __bool_1__;
__bool_1__ = ret_test();"""

    assert main.to_ir() == expected


def test_ignore_ret_typehint_list():
    """Test type discovery of list return values."""

    @aq.subroutine
    def ret_test() -> int:
        return [1, 2, 3]

    with pytest.raises(aq.errors.UnsupportedSubroutineReturnType):

        @aq.main(num_qubits=4)
        def main() -> float:
            ret_test()


def test_ignore_missing_ret_typehint_list():
    """Test type discovery of return types with no annotations."""

    @aq.subroutine
    def ret_test():
        return [1, 2, 3]

    with pytest.raises(aq.errors.UnsupportedSubroutineReturnType):

        @aq.main(num_qubits=4)
        def main():
            ret_test()


def test_ignore_missing_ret_typehint_float():
    """Test type discovery of return types with no annotations."""

    @aq.subroutine
    def ret_test():
        return 1.2

    @aq.main(num_qubits=4)
    def main():
        ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> float[64] {
    float[64] retval_ = 1.2;
    return retval_;
}
qubit[4] __qubits__;
float[64] __float_1__;
__float_1__ = ret_test();"""

    assert main.to_ir() == expected


def test_param_array_list_missing_arg():
    """Test list parameter with missing type arg (list rather than list[int])."""

    @aq.subroutine
    def param_test(arr: list) -> int:
        return 1

    with pytest.raises(aq.errors.ParameterTypeError):

        @aq.main(num_qubits=4)
        def main():
            param_test()
