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

from test_api import _test_on_local_sim

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import h, measure, rx, rz


def test_empty_gate() -> None:
    @aq.gate
    def my_gate(q: aq.qubit):
        pass

    @aq.function
    def my_program():
        my_gate(0)

    expected = """OPENQASM 3.0;
gate my_gate q {
}
qubit[1] __qubits__;
my_gate __qubits__[0];"""

    program = my_program()
    assert program.to_ir() == expected

    _test_on_local_sim(program)


def test_nested_gates() -> None:
    @aq.gate
    def t(q: aq.qubit):
        rz(q, aq.pi / 8)

    @aq.gate
    def my_gate(q: aq.qubit, theta: float):
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
    rz(pi / 8) q;
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
