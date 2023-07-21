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

from typing import List, Tuple

import oqpy
import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.types.types import qasm_range


@pytest.mark.parametrize(
    "range_params, expected_range_params",
    [
        ((0, 5, 1), (0, 5, 1)),
        ((5, None, 2), (0, 5, 2)),
    ],
)
def test_qasm_range(
    range_params: Tuple[int, int, int], expected_range_params: Tuple[int, int, int]
) -> None:
    """Test `qasm_range()` returning correct `Range` object.

    Args:
        range_params (Tuple[int, int, int]): Range parameters to instantiate `oqpy.Range`
        expected_range_params (Tuple[int, int, int]): Expected range parameters
    """
    start, stop, step = range_params
    qrange = qasm_range(start, stop, step)
    assert isinstance(qrange, oqpy.Range)
    assert (qrange.start, qrange.stop, qrange.step) == expected_range_params


def test_return_bit():
    """Test type discovery of bit return values."""

    @aq.function
    def ret_test() -> aq.BitVar:
        # TODO: These should work even in one line
        res = aq.BitVar(1)
        return res

    @aq.function
    def main() -> aq.BitVar:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> bit {
    bit res = 1;
    return res;
}
bit __bit_0__;
__bit_0__ = ret_test();"""

    assert main().to_ir() == expected


def test_return_int():
    """Test type discovery of int return values."""

    @aq.function
    def ret_test() -> int:
        res = aq.IntVar(1)
        return res

    @aq.function
    def main() -> int:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> int[32] {
    int[32] res = 1;
    return res;
}
int[32] __int_0__ = 0;
__int_0__ = ret_test();"""

    assert main().to_ir() == expected


def test_return_float():
    """Test type discovery of float return values."""

    @aq.function
    def ret_test() -> float:
        res = aq.FloatVar(1.0)
        return res

    @aq.function
    def main() -> float:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> float[64] {
    float[64] res = 1.0;
    return res;
}
float[64] __float_0__ = 0.0;
__float_0__ = ret_test();"""

    assert main().to_ir() == expected


def test_return_bool():
    """Test type discovery of boolean return values."""

    @aq.function
    def ret_test() -> bool:
        res = aq.BoolVar(True)
        return res

    @aq.function
    def main() -> bool:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> bool {
    bool res = true;
    return res;
}
bool __bool_0__ = false;
__bool_0__ = ret_test();"""

    assert main().to_ir() == expected


def test_return_bin_expr():
    """Test type discovery of int return values from an expression."""

    @aq.function
    def add(a: int, b: int) -> int:
        return a + b

    @aq.function
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
int[32] __int_0__ = 0;
__int_0__ = add(a, b);"""

    assert ret_test().to_ir() == expected


def test_return_none():
    """Test discovery of None return annotation."""

    @aq.function
    def ret_test() -> None:
        return None

    ret_test().to_ir()


def test_return_array():
    """Test return type discovery of array values."""

    @aq.function
    def ret_test() -> List[int]:
        res = aq.ArrayVar([1, 2, 3], dimensions=[3])
        return res

    @aq.function
    def main() -> List[int]:
        return ret_test()

    expected = """OPENQASM 3.0;
def ret_test() -> array[int[32], 3] {
    array[int[32], 3] res = {1, 2, 3};
    return res;
}
array[int[32], 3] __arr_0__ = {};
__arr_0__ = ret_test();"""

    assert main().to_ir() == expected


def test_return_func_call():
    """Test returning the result of another function call."""

    @aq.function
    def helper() -> int:
        res = aq.IntVar(1)
        return res

    @aq.function
    def ret_test() -> int:
        return helper()

    expected = """OPENQASM 3.0;
def helper() -> int[32] {
    int[32] res = 1;
    return res;
}
int[32] __int_0__ = 0;
__int_0__ = helper();"""

    assert ret_test().to_ir() == expected


def test_map_bool():
    """Test boolean input parameter type."""

    @aq.function
    def annotation_test(input: bool):
        pass

    @aq.function
    def main():
        annotation_test(True)

    expected = """OPENQASM 3.0;
def annotation_test(bool input) {
}
annotation_test(true);"""

    assert main().to_ir() == expected


def test_map_int():
    """Test integer input parameter type."""

    @aq.function
    def annotation_test(input: int):
        pass

    @aq.function
    def main():
        annotation_test(1)

    expected = """OPENQASM 3.0;
def annotation_test(int[32] input) {
}
annotation_test(1);"""

    assert main().to_ir() == expected


def test_map_float():
    """Test float input parameter type."""

    @aq.function
    def annotation_test(input: float):
        pass

    @aq.function
    def main():
        annotation_test(1.0)

    expected = """OPENQASM 3.0;
def annotation_test(float[64] input) {
}
annotation_test(1.0);"""

    assert main().to_ir() == expected


def test_map_array():
    """Test array input parameter type."""

    @aq.function
    def annotation_test(input: List[int]):
        pass

    @aq.function
    def main():
        a = aq.ArrayVar([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dimensions=[10])
        annotation_test(a)

    expected = """OPENQASM 3.0;
def annotation_test(array[int[32], 10] input) {
}
array[int[32], 10] a = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
annotation_test(a);"""

    assert main().to_ir() == expected


def test_map_other():
    """Test unexpected input parameter type handling."""

    # TODO: Should be able to pass aq.Bit directly to annotation_test

    @aq.function
    def annotation_test(input: aq.BitVar):
        pass

    @aq.function
    def main():
        a = aq.BitVar(1)
        annotation_test(a)

    expected = """OPENQASM 3.0;
def annotation_test(bit input) {
}
bit a = 1;
annotation_test(a);"""

    assert main().to_ir() == expected
