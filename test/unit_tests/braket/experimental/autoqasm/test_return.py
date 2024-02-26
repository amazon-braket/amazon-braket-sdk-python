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
from braket.experimental.autoqasm.pulse import capture_v0
from braket.pulse import Frame, Port


def test_float_lit():
    @aq.main
    def main():
        return 1.5

    expected = """OPENQASM 3.0;
output float[64] return_value;
return_value = 1.5;"""

    assert main.to_ir() == expected


def test_int_lit():
    @aq.main
    def main():
        return 1

    expected = """OPENQASM 3.0;
output int[32] return_value;
return_value = 1;"""

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
output bit return_value;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
return_value = __bit_0__;"""

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


def test_basic_arithmetic():
    @aq.main
    def main():
        val = aq.types.IntVar(1) + aq.types.IntVar(2)
        return val

    expected = """OPENQASM 3.0;
int[32] __int_0__ = 1;
int[32] __int_1__ = 2;
output int[32] val;
val = __int_0__ + __int_1__;"""

    assert main.to_ir() == expected


def test_expressions():
    @aq.main
    def main(input_a: int):
        val = 1
        val += input_a
        return val

    expected = """OPENQASM 3.0;
input int[32] input_a;
output int[32] val;
val = 1 + input_a;"""

    assert main.to_ir() == expected


def test_return_tuple():
    @aq.main
    def main():
        return 1, 2

    expected = """OPENQASM 3.0;
output int[32] return_value0;
output int[32] return_value1;
return_value0 = 1;
return_value1 = 2;"""

    assert main.to_ir() == expected


def test_return_list_floats():
    @aq.main
    def main():
        return [11.1, 2.222]

    expected = """OPENQASM 3.0;
output float[64] return_value0;
output float[64] return_value1;
return_value0 = 11.1;
return_value1 = 2.222;"""

    assert main.to_ir() == expected


def test_return_multi_meas():
    @aq.main
    def main():
        a = measure(0)
        b = measure(1)
        return a, b, measure(2)

    expected = """OPENQASM 3.0;
bit a;
bit b;
output bit return_value0;
output bit return_value1;
output bit return_value2;
qubit[3] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
a = __bit_0__;
bit __bit_1__;
__bit_1__ = measure __qubits__[1];
b = __bit_1__;
bit __bit_2__;
__bit_2__ = measure __qubits__[2];
return_value0 = a;
return_value1 = b;
return_value2 = __bit_2__;"""

    assert main.to_ir() == expected


def test_return_multi_types():
    @aq.main
    def main():
        a = measure(0)
        b = 1.11
        return a, True, b

    expected = """OPENQASM 3.0;
bit a;
output bit return_value0;
output bool return_value1;
output float[64] return_value2;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
a = __bit_0__;
return_value0 = a;
return_value1 = true;
return_value2 = 1.11;"""

    assert main.to_ir() == expected


def test_name_collisions():
    with pytest.raises(aq.errors.NameConflict):

        @aq.main
        def main(val):
            return val


def test_return_inputs():
    @aq.main
    def main(val1, val2):
        return val1 + val2

    expected = """OPENQASM 3.0;
input float val1;
input float val2;
output float[64] return_value;
return_value = val1 + val2;"""

    assert main.to_ir() == expected


def test_return_ints():
    @aq.main
    def main(val1: int, val2: int):
        return val1 + val2

    expected = """OPENQASM 3.0;
input int[32] val1;
input int[32] val2;
output int[32] return_value;
return_value = val1 + val2;"""

    assert main.to_ir() == expected


def test_return_bools():
    @aq.main
    def main(val1: bool, val2: bool):
        return val1 or val2

    expected = """OPENQASM 3.0;
input bool val1;
input bool val2;
output bool return_value;
bool __bool_0__;
__bool_0__ = val1 || val2;
return_value = __bool_0__;"""

    assert main.to_ir() == expected


def test_return_bits():
    @aq.main
    def main():
        b0 = measure(0)
        b1 = measure(1)
        return b0 + b1

    expected = """OPENQASM 3.0;
bit b0;
bit b1;
output bit return_value;
qubit[2] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
b0 = __bit_0__;
bit __bit_1__;
__bit_1__ = measure __qubits__[1];
b1 = __bit_1__;
return_value = b0 + b1;"""

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
output bit[3] return_value;
qubit[10] __qubits__;
ghz(n);
bit[3] __bit_0__ = "000";
__bit_0__[0] = measure __qubits__[0];
__bit_0__[1] = measure __qubits__[1];
__bit_0__[2] = measure __qubits__[2];
return_value = __bit_0__;"""

    assert program.to_ir() == expected


def test_return_pulse_capture():
    port = Port(port_id="device_port_x0", dt=1e-9, properties={})
    frame = Frame(frame_id="frame1", frequency=2e9, port=port, phase=0, is_predefined=True)

    @aq.main
    def program():
        return capture_v0(frame), capture_v0(frame)

    expected = """OPENQASM 3.0;
bit __bit_0__;
bit __bit_1__;
output bit return_value0;
output bit return_value1;
cal {
    __bit_0__ = capture_v0(frame1);
    __bit_1__ = capture_v0(frame1);
}
return_value0 = __bit_0__;
return_value1 = __bit_1__;"""

    assert program.to_ir() == expected
