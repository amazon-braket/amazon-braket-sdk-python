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

"""AutoQASM tests exercising the return statement for `aq.main`."""

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import measure


def test_float_lit():
    @aq.main
    def main():
        return 1.5

    expected = """OPENQASM 3.0;
output float[64] retval_;
retval_ = 1.5;"""

    assert main.to_ir() == expected


def test_int_lit():
    @aq.main
    def main():
        return 1

    expected = """OPENQASM 3.0;
output int[32] retval_;
retval_ = 1;"""

    assert main.to_ir() == expected


def test_named_value():
    @aq.main
    def main():
        output_name = 1
        return output_name

    expected = """OPENQASM 3.0;
output int[32] output_name;
output_name = 1;"""

    assert main.to_ir() == expected


def test_return_measure():
    @aq.main
    def main():
        return measure(0)

    expected = """OPENQASM 3.0;
output bit retval_;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
retval_ = __bit_0__;"""

    assert main.to_ir() == expected


def test_named_measure():
    @aq.main
    def main() -> int:
        b = measure(0)
        return b

    expected = """OPENQASM 3.0;
output bit b;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
b = __bit_0__;"""

    assert main.to_ir() == expected


@pytest.mark.xfail(reason="Not implemented yet")
def test_basic_arithmetic():
    @aq.main
    def main():
        val = aq.types.IntVar(1) + aq.types.IntVar(2)
        return val

    expected = """OPENQASM 3.0;
input int[32] input_a;
output int[32] val;
val = 3;"""

    assert main.to_ir() == expected


@pytest.mark.xfail(reason="Not implemented yet")
def test_expressions():
    @aq.main
    def main(input_a: int):
        val = 1
        val += input_a
        return val

    expected = """OPENQASM 3.0;
input int[32] input_a;
output int[32] val;
val = 1;
val = val + input_a;"""

    assert main.to_ir() == expected


@pytest.mark.xfail(reason="Not implemented yet")
def test_expressions_and_control_flow():
    @aq.main(num_qubits=3)
    def main():
        val = 0.5
        for i in aq.range(3):
            val = val + measure(i)
        return val

    expected = """OPENQASM 3.0;
output float[64] val;
qubit[5] __qubits__;
val = 0.5;
for int i in [0:3 - 1] {
    bit __bit_1__;
    __bit_1__ = measure __qubits__[i];
    val = val + __bit_1__;
}"""

    assert main.to_ir() == expected


@pytest.mark.xfail(reason="Not implemented yet")
def test_return_tuple():
    @aq.main
    def main():
        return 1, 2

    expected = """OPENQASM 3.0;
output int[32] retval1_;
output int[32] retval2_;
retval1_ = 1;
retval2_ = 2;"""

    assert main.to_ir() == expected


def test_name_collisions():
    @aq.main
    def main(val):
        return val

    expected = """OPENQASM 3.0;
input float[64] val;
output float[64] val_;
val_ = val;"""

    assert main.to_ir() == expected


@pytest.mark.xfail(raises=NotImplementedError)  # Needs OQPy 0.3.5
def test_return_inputs():
    @aq.main
    def main(val1, val2):
        return val1 + val2

    expected = """OPENQASM 3.0;
input float[64] val1;
input float[64] val2;
output float[64] retval_;
retval_ = val1 + val2;"""

    assert main.to_ir() == expected


def test_returns_with_subroutine():
    """Test returning the result of another function call."""

    @aq.subroutine
    def helper() -> int:
        res = aq.IntVar(1)
        return res

    @aq.main
    def ret_test() -> int:
        val = helper()
        return val

    expected = """OPENQASM 3.0;
def helper() -> int[32] {
    int[32] res = 1;
    return res;
}
output int[32] val;
int[32] __int_1__;
__int_1__ = helper();
val = __int_1__;"""

    assert ret_test.to_ir() == expected


def test_return_measure_range():
    @aq.subroutine
    def ghz(n: int):
        aq.instructions.h(0)
        for i in aq.range(n - 1):
            aq.instructions.cnot(i, i + 1)

    @aq.main(num_qubits=10)
    def program(n: int):
        ghz(n)
        return measure([0, 1, 2])

    expected = """OPENQASM 3.0;
def ghz(int[32] n) {
    h __qubits__[0];
    for int i in [0:n - 1 - 1] {
        cnot __qubits__[i], __qubits__[i + 1];
    }
}
input int[32] n;
output bit retval_;
qubit[10] __qubits__;
ghz(n);
bit[3] __bit_0__ = "000";
__bit_0__[0] = measure __qubits__[0];
__bit_0__[1] = measure __qubits__[1];
__bit_0__[2] = measure __qubits__[2];
retval_ = __bit_0__;"""

    assert program.to_ir() == expected
