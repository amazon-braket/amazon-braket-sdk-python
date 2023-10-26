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

"""AutoQASM tests for FreeParameter support."""

import braket.experimental.autoqasm as aq
from braket.circuits import FreeParameter
from braket.default_simulator import StateVectorSimulator
from braket.devices.local_simulator import LocalSimulator
from braket.experimental.autoqasm.instructions import cnot, cphaseshift, gpi, h, measure, ms, rx, rz
from braket.tasks.local_quantum_task import LocalQuantumTask


def _test_on_local_sim(program: aq.Program) -> None:
    device = LocalSimulator(backend=StateVectorSimulator())
    task = device.run(program, shots=10)
    assert isinstance(task, LocalQuantumTask)
    assert isinstance(task.result().measurements, dict)


def test_simple_parametric():
    """Test a program with a parameter can be serialized."""

    @aq.main
    def parametric():
        rx(0, FreeParameter("theta"))
        measure(0)

    expected = """OPENQASM 3.0;
input float[64] theta;
qubit[1] __qubits__;
rx(theta) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""
    assert parametric().to_ir() == expected


def test_multiple_parameters():
    """Test that multiple free parameters all appear in the processed program."""

    @aq.main
    def parametric():
        rx(0, FreeParameter("alpha"))
        rx(1, FreeParameter("theta"))
        c = measure([0, 1])  # noqa: F841

    expected = """OPENQASM 3.0;
bit[2] c;
input float[64] alpha;
input float[64] theta;
qubit[2] __qubits__;
rx(alpha) __qubits__[0];
rx(theta) __qubits__[1];
bit[2] __bit_0__ = "00";
__bit_0__[0] = measure __qubits__[0];
__bit_0__[1] = measure __qubits__[1];
c = __bit_0__;"""
    assert parametric().to_ir() == expected


def test_repeat_parameter():
    """Test that programs can use the same parameter multiple times."""

    @aq.main
    def parametric():
        alpha = FreeParameter("alpha")
        theta = FreeParameter("theta")
        rx(0, alpha)
        rx(1, theta)
        cnot(0, 1)
        rx(0, theta)
        rx(1, alpha)

    expected = """OPENQASM 3.0;
input float[64] alpha;
input float[64] theta;
qubit[2] __qubits__;
rx(alpha) __qubits__[0];
rx(theta) __qubits__[1];
cnot __qubits__[0], __qubits__[1];
rx(theta) __qubits__[0];
rx(alpha) __qubits__[1];"""
    assert parametric().to_ir() == expected


def test_parameter_in_subroutine():
    """Test that parameters in subroutines are declared appropriately."""

    @aq.subroutine
    def rx_alpha(qubit: int):
        rx(qubit, FreeParameter("alpha"))

    @aq.main(num_qubits=3)
    def parametric():
        rx_alpha(2)

    expected = """OPENQASM 3.0;
def rx_alpha(int[32] qubit) {
    rx(alpha) __qubits__[qubit];
}
input float[64] alpha;
qubit[3] __qubits__;
rx_alpha(2);"""
    assert parametric().to_ir() == expected


def test_captured_parameter():
    """Test that a parameter declared in a larger scope is captured
    and functions correctly.
    """

    alpha = FreeParameter("alpha")

    @aq.main
    def parametric():
        rz(0, alpha)
        rx(1, alpha)

    expected = """OPENQASM 3.0;
input float[64] alpha;
qubit[2] __qubits__;
rz(alpha) __qubits__[0];
rx(alpha) __qubits__[1];"""
    assert parametric().to_ir() == expected


def test_multi_angle_gates():
    """Test that FreeParameters work with gates that take multiple inputs."""

    @aq.main(num_qubits=5)
    def parametric(qubit_0: int, phi: float, theta: float):
        ms(0, qubit_0, phi, phi, theta)

    expected = """OPENQASM 3.0;
input float[64] phi;
qubit[5] __qubits__;
ms(phi, phi, 0.5) __qubits__[0], __qubits__[2];"""
    assert parametric(2, FreeParameter("phi"), 0.5).to_ir() == expected


def test_parameters_passed_as_main_arg():
    """Test that parameters work when passed as input values."""

    @aq.main
    def parametric(phi: float):
        cphaseshift(0, 1, phi)

    expected = """OPENQASM 3.0;
input float[64] my_phi;
qubit[2] __qubits__;
cphaseshift(my_phi) __qubits__[0], __qubits__[1];"""
    assert parametric(FreeParameter("my_phi")).to_ir() == expected


def test_parameters_passed_as_subroutine_arg():
    """Test that parameters work when passed as input values."""
    # FIXME

    @aq.subroutine
    def silly_ms(qubit_0: int, phi: float, theta: float):
        ms(0, qubit_0, phi, phi, theta)

    @aq.main(num_qubits=5)
    def parametric():
        silly_ms(1, FreeParameter("alpha"), 0.707)
        silly_ms(3, 0.5, FreeParameter("beta"))

    expected = """OPENQASM 3.0;
def silly_ms(int[32] qubit_0, float[64] phi, float[64] theta) {
    ms(phi, phi, theta) __qubits__[0], __qubits__[qubit_0];
}
input float[64] alpha;
input float[64] beta;
qubit[5] __qubits__;
silly_ms(1, alpha, 0.707);
silly_ms(3, 0.5, beta);"""
    assert parametric().to_ir() == expected


def test_parameter_expressions():
    """Test expressions of free parameters with numeric literals."""

    @aq.main
    def parametric():
        expr = (2 * FreeParameter("theta")) + 1.5
        rx(0, expr)

    # TODO
    expected = """OPENQASM 3.0;"""
    assert parametric().to_ir() == expected


def test_multi_parameter_expressions():
    """Test expresssions of multiple free parameters."""

    @aq.main
    def parametric():
        expr = FreeParameter("alpha") * FreeParameter("theta")
        gpi(0, expr)

    # TODO
    expected = """OPENQASM 3.0;"""
    assert parametric().to_ir() == expected


def test_integer_parameters():
    """Test integer input parameter type."""

    @aq.main
    def parametric(qubit: int):
        basis = FreeParameter("basis")
        if basis == 0:
            h(qubit)
        elif basis == 1:
            rx(qubit, 0.5)
        else:
            pass
        result = measure(qubit)  # noqa: F841

    # TODO
    expected = """OPENQASM 3.0;
bit result;
input int[32] basis;
qubit[2] __qubits__;
if (basis == 0) {
    h __qubits__[1];
} else if (basis == 1) {
    rx(0.5) __qubits__[1];
}
bit __bit_0__;
__bit_0__ = measure __qubits__[1];
result = __bit_0__;"""
    assert parametric(1).to_ir() == expected


def test_execution():
    """TODO"""
    # tests on local simulator


# TODO
# - local sim doesn't seem to support angle input types
# TODO: gate args?
