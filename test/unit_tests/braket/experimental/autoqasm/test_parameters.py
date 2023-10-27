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

"""AutoQASM tests for parameter support."""

import braket.experimental.autoqasm as aq
from braket.circuits import FreeParameter
from braket.default_simulator import StateVectorSimulator
from braket.devices.local_simulator import LocalSimulator
from braket.experimental.autoqasm.instructions import cnot, cphaseshift, measure, ms, rx, rz
from braket.tasks.local_quantum_task import LocalQuantumTask


def _test_parametric_on_local_sim(program: aq.Program, inputs: dict[str, float]) -> None:
    device = LocalSimulator(backend=StateVectorSimulator())
    task = device.run(program, shots=10, inputs=inputs)
    assert isinstance(task, LocalQuantumTask)
    assert isinstance(task.result().measurements, dict)
    return task.result().measurements


@aq.main
def simple_parametric():
    rx(0, FreeParameter("theta"))
    measure(0)


def test_simple_parametric():
    """Test a program with a parameter can be serialized."""

    expected = """OPENQASM 3.0;
input float[64] theta;
qubit[1] __qubits__;
rx(theta) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""
    assert simple_parametric().to_ir() == expected


def test_sim_simple():
    measurements = _test_parametric_on_local_sim(simple_parametric(), {"theta": 0})
    assert 1 not in measurements["__bit_0__"]
    measurements = _test_parametric_on_local_sim(simple_parametric(), {"theta": 3.14})
    assert 0 not in measurements["__bit_0__"]


@aq.main
def multi_parametric():
    rx(0, FreeParameter("alpha"))
    rx(1, FreeParameter("theta"))
    c = measure([0, 1])  # noqa: F841


def test_multiple_parameters():
    """Test that multiple free parameters all appear in the processed program."""

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
    assert multi_parametric().to_ir() == expected


def test_typed_parameters():
    """Test that multiple free parameters all appear in the processed program."""

    @aq.main
    def multi_parametric():
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
    assert multi_parametric().to_ir() == expected


def test_sim_multi_param():
    measurements = _test_parametric_on_local_sim(multi_parametric(), {"alpha": 3.14, "theta": 0})
    assert all(val == "10" for val in measurements["c"])
    measurements = _test_parametric_on_local_sim(multi_parametric(), {"alpha": 0, "theta": 3.14})
    assert all(val == "01" for val in measurements["c"])


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


def test_sim_multi_angle():
    @aq.main
    def parametric(phi: float, theta: float):
        ms(0, 1, phi, phi, theta)

    _test_parametric_on_local_sim(parametric(FreeParameter("phi"), 0.0), {"phi": 3.14})


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


def test_simple_subroutine_arg():
    """Test that parameters work when passed as input values."""

    @aq.subroutine
    def silly_rz(theta: float):
        rz(0, theta)

    @aq.main(num_qubits=1)
    def parametric():
        silly_rz(FreeParameter("alpha"))

    expected = """OPENQASM 3.0;
def silly_rz(float[64] theta) {
    rz(theta) __qubits__[0];
}
input float[64] alpha;
qubit[1] __qubits__;
silly_rz(alpha);"""
    assert parametric().to_ir() == expected


def test_parameters_passed_as_subroutine_arg():
    """Test that parameters work when passed as input values."""

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


def test_sim_subroutine_arg():
    @aq.subroutine
    def rx_theta(theta: float):
        rx(0, theta)

    @aq.main
    def parametric():
        rx_theta(FreeParameter("theta"))
        measure(0)

    measurements = _test_parametric_on_local_sim(parametric(), {"theta": 3.14})
    assert 0 not in measurements["__bit_0__"]


def test_parametric_gate_args():
    """Test that gates can be used with parameters."""

    @aq.gate
    def rx_theta(q: aq.Qubit, theta: float):
        rx(q, theta)

    @aq.main(num_qubits=3)
    def parametric():
        rx_theta(2, FreeParameter("θ"))

    expected = """OPENQASM 3.0;
gate rx_theta(theta) q {
    rx(theta) q;
}
input float[64] θ;
qubit[3] __qubits__;
rx_theta(θ) __qubits__[2];"""
    assert parametric().to_ir() == expected
