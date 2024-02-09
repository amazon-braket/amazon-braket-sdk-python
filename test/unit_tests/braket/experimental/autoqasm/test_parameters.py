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

import numpy as np
import pytest

import braket.experimental.autoqasm as aq
from braket.circuits import FreeParameter
from braket.default_simulator import StateVectorSimulator
from braket.devices.local_simulator import LocalSimulator
from braket.experimental.autoqasm import pulse
from braket.experimental.autoqasm.instructions import (
    cnot,
    cphaseshift,
    gpi,
    h,
    measure,
    ms,
    rx,
    rz,
    x,
)
from braket.tasks.local_quantum_task import LocalQuantumTask


def _test_parametric_on_local_sim(program: aq.Program, inputs: dict[str, float]) -> np.ndarray:
    device = LocalSimulator(backend=StateVectorSimulator())
    task = device.run(program, shots=100, inputs=inputs)
    assert isinstance(task, LocalQuantumTask)
    assert isinstance(task.result().measurements, dict)
    return task.result().measurements


@pytest.fixture
def simple_parametric():
    @aq.main
    def simple_parametric(theta):
        rx(0, theta)
        measure(0)

    return simple_parametric


@pytest.fixture
def simple_parametric_fp():
    @aq.main
    def simple_parametric():
        rx(0, FreeParameter("theta"))
        measure(0)

    return simple_parametric


def test_simple_parametric(simple_parametric):
    """Test a program with a parameter can be serialized."""

    expected = """OPENQASM 3.0;
input float theta;
qubit[1] __qubits__;
rx(theta) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""
    assert simple_parametric.to_ir() == expected


def test_simple_parametric_fp(simple_parametric_fp):
    """Test a program with an explicit free parameter can be serialized."""

    expected = """OPENQASM 3.0;
input float theta;
qubit[1] __qubits__;
rx(theta) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""
    assert simple_parametric_fp.to_ir() == expected


def test_sim_simple(simple_parametric):
    measurements = _test_parametric_on_local_sim(simple_parametric, {"theta": 0})
    assert 1 not in measurements["__bit_0__"]
    measurements = _test_parametric_on_local_sim(simple_parametric, {"theta": np.pi})
    assert 0 not in measurements["__bit_0__"]


def test_sim_simple_fp(simple_parametric_fp):
    measurements = _test_parametric_on_local_sim(simple_parametric_fp, {"theta": 0})
    assert 1 not in measurements["__bit_0__"]
    measurements = _test_parametric_on_local_sim(simple_parametric_fp, {"theta": np.pi})
    assert 0 not in measurements["__bit_0__"]


@pytest.fixture
def multi_parametric():
    @aq.main
    def multi_parametric(alpha, theta):
        rx(0, alpha)
        rx(1, theta)
        c = measure([0, 1])  # noqa: F841

    return multi_parametric


def test_multiple_parameters(multi_parametric):
    """Test that multiple free parameters all appear in the processed program."""

    expected = """OPENQASM 3.0;
input float alpha;
input float theta;
bit[2] c;
qubit[2] __qubits__;
rx(alpha) __qubits__[0];
rx(theta) __qubits__[1];
bit[2] __bit_0__ = "00";
__bit_0__[0] = measure __qubits__[0];
__bit_0__[1] = measure __qubits__[1];
c = __bit_0__;"""
    assert multi_parametric.to_ir() == expected


def test_sim_multi_param(multi_parametric):
    measurements = _test_parametric_on_local_sim(multi_parametric, {"alpha": np.pi, "theta": 0})
    assert all(val == "10" for val in measurements["c"])
    measurements = _test_parametric_on_local_sim(multi_parametric, {"alpha": 0, "theta": np.pi})
    assert all(val == "01" for val in measurements["c"])


def test_repeat_parameter():
    """Test that programs can use the same parameter multiple times."""

    @aq.main
    def parametric(alpha, theta):
        rx(0, alpha)
        rx(1, theta)
        cnot(0, 1)
        rx(0, theta)
        rx(1, alpha)

    expected = """OPENQASM 3.0;
input float alpha;
input float theta;
qubit[2] __qubits__;
rx(alpha) __qubits__[0];
rx(theta) __qubits__[1];
cnot __qubits__[0], __qubits__[1];
rx(theta) __qubits__[0];
rx(alpha) __qubits__[1];"""
    assert parametric.to_ir() == expected


@pytest.mark.xfail(
    reason="Regression: FreeParameters create FloatVar with _needs_declaration=False"
)
def test_parameter_in_subroutine():
    """Test that parameters in subroutines are declared appropriately."""
    # TODO (#816): the openqasm generated here isn't strictly valid
    # (cannot close over non-const global variables)
    # https://openqasm.com/language/scope.html#subroutine-and-gate-scope

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
input float alpha;
qubit[3] __qubits__;
rx_alpha(2);"""
    assert parametric.to_ir() == expected


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
input float alpha;
qubit[2] __qubits__;
rz(alpha) __qubits__[0];
rx(alpha) __qubits__[1];"""
    assert parametric.to_ir() == expected


def test_multi_angle_gates():
    """Test that FreeParameters work with gates that take multiple inputs."""
    qubit_0 = 2
    theta = 0.5

    @aq.main(num_qubits=5)
    def parametric(phi: float):
        ms(0, qubit_0, phi, phi, theta)

    expected = """OPENQASM 3.0;
input float phi;
qubit[5] __qubits__;
ms(phi, phi, 0.5) __qubits__[0], __qubits__[2];"""
    assert parametric.to_ir() == expected


def test_sim_multi_angle():
    theta = 0

    @aq.main
    def parametric(phi: float):
        ms(0, 1, phi, phi, theta)

    _test_parametric_on_local_sim(
        parametric,
        inputs={"phi": np.pi},
    )


def test_parameters_passed_as_main_arg():
    """Test that parameters work when passed as input values."""

    @aq.main
    def parametric(my_phi: float):
        cphaseshift(0, 1, my_phi)

    expected = """OPENQASM 3.0;
input float my_phi;
qubit[2] __qubits__;
cphaseshift(my_phi) __qubits__[0], __qubits__[1];"""
    assert parametric.to_ir() == expected


def test_simple_subroutine_arg():
    """Test that parameters work when passed as input values."""

    @aq.subroutine
    def silly_rz(theta: float):
        rz(0, theta)

    @aq.main(num_qubits=1)
    def parametric(alpha):
        silly_rz(alpha)

    expected = """OPENQASM 3.0;
def silly_rz(float theta) {
    rz(theta) __qubits__[0];
}
input float alpha;
qubit[1] __qubits__;
silly_rz(alpha);"""
    assert parametric.to_ir() == expected


def test_parameters_passed_as_subroutine_arg():
    """Test that parameters work when passed as input values."""

    @aq.subroutine
    def silly_ms(qubit_0: int, phi: float, theta: float):
        ms(0, qubit_0, phi, phi, theta)

    @aq.main(num_qubits=5)
    def parametric(alpha):
        silly_ms(1, alpha, 0.707)
        silly_ms(3, 0.5, FreeParameter("beta"))

    expected = """OPENQASM 3.0;
def silly_ms(int[32] qubit_0, float phi, float theta) {
    ms(phi, phi, theta) __qubits__[0], __qubits__[qubit_0];
}
input float alpha;
input float beta;
qubit[5] __qubits__;
silly_ms(1, alpha, 0.707);
silly_ms(3, 0.5, beta);"""
    assert parametric.to_ir() == expected


def test_sim_subroutine_arg():
    @aq.subroutine
    def rx_theta(theta: float):
        rx(0, theta)

    @aq.main
    def parametric(theta):
        rx_theta(theta)
        measure(0)

    measurements = _test_parametric_on_local_sim(parametric, {"theta": np.pi})
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
input float θ;
qubit[3] __qubits__;
rx_theta(θ) __qubits__[2];"""
    assert parametric.to_ir() == expected


def test_parametric_pulse_cals():
    """Test that pulse calibrations work with free parameters."""

    @aq.gate_calibration(implements=rx, target="$1")
    def cal_1(angle: float):
        pulse.delay("$1", angle)

    @aq.main
    def my_program(theta):
        rx("$1", theta)

    expected = """OPENQASM 3.0;
input float theta;
defcal rx(angle[32] angle) $1 {
    delay[angle * 1s] $1;
}
rx(theta) $1;"""
    qasm = my_program.with_calibrations(cal_1).to_ir()
    assert qasm == expected


def test_bind_parameters():
    """Test binding FreeParameters to concrete values."""

    @aq.main
    def parametric(alpha: float):
        rx(0, alpha)
        measure(0)

    unbound_expected = """OPENQASM 3.0;
input float alpha;
qubit[1] __qubits__;
rx(alpha) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""

    bound_template = """OPENQASM 3.0;
float alpha = {};
qubit[1] __qubits__;
rx(alpha) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""

    assert parametric.to_ir() == unbound_expected
    bound_prog = parametric.make_bound_program({"alpha": 0.5})
    # Original program unchanged
    assert parametric.to_ir() == unbound_expected
    assert bound_prog.to_ir() == bound_template.format(0.5)
    # Can rebind
    bound_prog = parametric.make_bound_program({"alpha": 0.432143})
    assert bound_prog.to_ir() == bound_template.format(0.432143)


def test_multi_bind_parameters():
    """Test binding FreeParameters to concrete values."""

    @aq.subroutine
    def sub(alpha: float, theta: float):
        rx(0, alpha)
        rx(1, theta)
        cnot(0, 1)
        rx(0, theta)
        rx(1, alpha)

    @aq.subroutine
    def rx_alpha(qubit: int):
        rx(qubit, FreeParameter("alpha"))

    @aq.main(num_qubits=3)
    def parametric(alpha: float, beta: float):
        sub(alpha, beta)
        rx_alpha(2)

    bound_prog = parametric.make_bound_program({"alpha": 0.5, "beta": 1.5})

    expected = """OPENQASM 3.0;
def sub(float alpha, float theta) {
    rx(alpha) __qubits__[0];
    rx(theta) __qubits__[1];
    cnot __qubits__[0], __qubits__[1];
    rx(theta) __qubits__[0];
    rx(alpha) __qubits__[1];
}
def rx_alpha(int[32] qubit) {
    rx(alpha) __qubits__[qubit];
}
float alpha = 0.5;
float beta = 1.5;
qubit[3] __qubits__;
sub(alpha, beta);
rx_alpha(2);"""
    assert bound_prog.to_ir() == expected


def test_partial_bind():
    """Test binding some but not all FreeParameters."""

    @aq.subroutine
    def rx_alpha(qubit: int, theta: float):
        rx(qubit, theta)

    @aq.main(num_qubits=3)
    def parametric(alpha: float, beta: float):
        rx_alpha(2, alpha)
        rx_alpha(2, beta)

    bound_prog = parametric.make_bound_program({"beta": np.pi})

    expected = """OPENQASM 3.0;
def rx_alpha(int[32] qubit, float theta) {
    rx(theta) __qubits__[qubit];
}
input float alpha;
float beta = 3.141592653589793;
qubit[3] __qubits__;
rx_alpha(2, alpha);
rx_alpha(2, beta);"""
    assert bound_prog.to_ir() == expected


def test_binding_pulse_parameters():
    """Test binding programs with parametric pulse instructions."""

    @aq.gate_calibration(implements=rx, target="$1")
    def cal_1(angle: float):
        pulse.delay("$1", angle)

    @aq.main
    def my_program(theta):
        rx("$1", theta)

    qasm1 = my_program.with_calibrations(cal_1).make_bound_program({"theta": 0.6}).to_ir()
    qasm2 = my_program.make_bound_program({"theta": 0.6}).with_calibrations(cal_1).to_ir()
    assert qasm1 == qasm2

    expected = """OPENQASM 3.0;
float theta = 0.6;
defcal rx(angle[32] angle) $1 {
    delay[angle * 1s] $1;
}
rx(theta) $1;"""
    assert expected == qasm1


def test_bind_empty_program():
    """Test that binding behaves well on empty programs."""

    @aq.main
    def empty_program():
        pass

    qasm = empty_program.to_ir()
    bound_program1 = empty_program.make_bound_program({}).to_ir()
    bound_program2 = empty_program.make_bound_program({"alpha": 0.5}).to_ir()
    assert qasm == bound_program1 == bound_program2


def test_strict_parameter_bind():
    """Test make_bound_program with strict set to True."""

    @aq.main
    def parametric(alpha: float):
        rx(0, alpha)
        measure(0)

    template = """OPENQASM 3.0;
float alpha = {};
qubit[1] __qubits__;
rx(alpha) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""

    bound_prog = parametric.make_bound_program({"alpha": 0.5}, strict=True)
    assert bound_prog.to_ir() == template.format(0.5)


def test_strict_parameter_bind_failure():
    """Test make_bound_program with strict set to True."""

    @aq.main
    def parametric(alpha: float):
        rx(0, alpha)
        measure(0)

    with pytest.raises(
        aq.errors.ParameterNotFoundError, match="No parameter in the program named: beta"
    ):
        parametric.make_bound_program({"beta": 0.5}, strict=True)


def test_duplicate_variable_name_fails():
    """Test using a variable and FreeParameter with the same name."""

    with pytest.raises(RuntimeError, match="conflicting variables with name alpha"):

        @aq.main
        def parametric_explicit():
            alpha = aq.FloatVar(1.2)  # noqa: F841
            rx(0, FreeParameter("alpha"))

    with pytest.raises(RuntimeError, match="conflicting variables with name alpha"):

        @aq.main
        def parametric(alpha):
            alpha = aq.FloatVar(1.2)  # noqa: F841
            rx(0, alpha)


def test_binding_variable_fails():
    """Test that trying to bind a variable that isn't declared as a FreeParameter fails."""

    @aq.main
    def parametric():
        alpha = aq.FloatVar(1.2)  # noqa: F841

    with pytest.raises(
        aq.errors.ParameterNotFoundError, match="No parameter in the program named: beta"
    ):
        parametric.make_bound_program({"beta": 0.5}, strict=True)


def test_compound_condition():
    """Test parameters used in greater than conditional statements."""

    @aq.main
    def parametric(val: float):
        threshold = 0.9
        if val > threshold or val >= 1.2:
            x(0)
        measure(0)

    expected = """OPENQASM 3.0;
input float val;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = val > 0.9;
bool __bool_1__;
__bool_1__ = val >= 1.2;
bool __bool_2__;
__bool_2__ = __bool_0__ || __bool_1__;
if (__bool_2__) {
    x __qubits__[0];
}
bit __bit_3__;
__bit_3__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_lt_condition():
    """Test parameters used in less than conditional statements."""

    @aq.main
    def parametric(val: float):
        if val < 0.9:
            x(0)
        if val <= 0.9:
            h(0)
        measure(0)

    expected = """OPENQASM 3.0;
input float val;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = val < 0.9;
if (__bool_0__) {
    x __qubits__[0];
}
bool __bool_1__;
__bool_1__ = val <= 0.9;
if (__bool_1__) {
    h __qubits__[0];
}
bit __bit_2__;
__bit_2__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_parameter_in_predicate_in_subroutine():
    """Test parameters used in conditional statements."""

    @aq.subroutine
    def sub(val: float):
        threshold = 0.9
        if val > threshold:
            x(0)

    @aq.main
    def parametric(val: float):
        sub(val)
        measure(0)

    expected = """OPENQASM 3.0;
def sub(float val) {
    bool __bool_0__;
    __bool_0__ = val > 0.9;
    if (__bool_0__) {
        x __qubits__[0];
    }
}
input float val;
qubit[1] __qubits__;
sub(val);
bit __bit_1__;
__bit_1__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_eq_condition():
    """Test parameters used in conditional equals statements."""

    @aq.main
    def parametric(threshold: int):
        if threshold == 1:
            h(0)
        elif threshold == 2:
            x(0)
        else:
            pass
        measure(0)

    expected = """OPENQASM 3.0;
input int[32] threshold;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = threshold == 1;
if (__bool_0__) {
    h __qubits__[0];
} else {
    bool __bool_1__;
    __bool_1__ = threshold == 2;
    if (__bool_1__) {
        x __qubits__[0];
    }
}
bit __bit_2__;
__bit_2__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_sim_conditional_stmts():
    @aq.main
    def main(basis: int):
        if basis == 1:
            h(0)
        else:
            x(0)
        c = measure(0)  # noqa: F841

    measurements = _test_parametric_on_local_sim(main, {"basis": 0})
    assert all(val == 1 for val in measurements["c"])
    measurements = _test_parametric_on_local_sim(main, {"basis": 1})
    assert 1 in measurements["c"] and 0 in measurements["c"]


def test_sim_comparison_stmts():
    @aq.main
    def main(basis: float):
        if basis > 0.5:
            x(0)
        c = measure(0)  # noqa: F841

    measurements = _test_parametric_on_local_sim(main, {"basis": 0.5})
    assert all(val == 0 for val in measurements["c"])
    measurements = _test_parametric_on_local_sim(main, {"basis": 0.55})
    assert all(val == 1 for val in measurements["c"])


def test_param_neq():
    """Test parameters used in conditional not equals statements."""

    @aq.main
    def parametric(val: int):
        if val != 1:
            h(0)
        measure(0)

    expected = """OPENQASM 3.0;
input int[32] val;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = val != 1;
if (__bool_0__) {
    h __qubits__[0];
}
bit __bit_1__;
__bit_1__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_param_or():
    """Test parameters used in conditional `or` statements."""

    @aq.main
    def parametric(alpha: float, beta: float):
        if alpha or beta:
            rx(0, alpha)
            rx(0, beta)
        measure(0)

    expected = """OPENQASM 3.0;
input float alpha;
input float beta;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = alpha || beta;
if (__bool_0__) {
    rx(alpha) __qubits__[0];
    rx(beta) __qubits__[0];
}
bit __bit_1__;
__bit_1__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_param_and():
    """Test parameters used in conditional `and` statements."""

    @aq.main
    def parametric(alpha: float, beta: float):
        if alpha and beta:
            rx(0, alpha)
        measure(0)

    expected = """OPENQASM 3.0;
input float alpha;
input float beta;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = alpha && beta;
if (__bool_0__) {
    rx(alpha) __qubits__[0];
}
bit __bit_1__;
__bit_1__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_param_and_float():
    """Test parameters used in conditional `and` statements."""
    beta = 1.5

    @aq.main
    def parametric(alpha: float):
        if alpha and beta:
            rx(0, alpha)
        measure(0)

    expected = """OPENQASM 3.0;
input float alpha;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = alpha && 1.5;
if (__bool_0__) {
    rx(alpha) __qubits__[0];
}
bit __bit_1__;
__bit_1__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_param_not():
    """Test parameters used in conditional `not` statements."""

    @aq.main
    def parametric(val: int):
        if not val:
            h(0)
        measure(0)

    expected = """OPENQASM 3.0;
input int[32] val;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = !val;
if (__bool_0__) {
    h __qubits__[0];
}
bit __bit_1__;
__bit_1__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_parameter_binding_conditions():
    """Test that parameters can be used in conditions and then bound."""

    @aq.main
    def parametric(val: float):
        if val == 1:
            x(0)
        measure(0)

    template = """OPENQASM 3.0;
float val = {};
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = val == 1;
if (__bool_0__) {{
    x __qubits__[0];
}}
bit __bit_1__;
__bit_1__ = measure __qubits__[0];"""
    bound_prog = parametric.make_bound_program({"val": 0})
    assert bound_prog.to_ir() == template.format(0)
    bound_prog = parametric.make_bound_program({"val": 1})
    assert bound_prog.to_ir() == template.format(1)


def test_parameter_expressions():
    """Test expressions of free parameters with numeric literals."""

    @aq.main
    def parametric(theta):
        expr = 2 * theta
        gpi(0, expr)

    @aq.main
    def parametric_fp():
        expr = 2 * FreeParameter("theta")
        gpi(0, expr)

    expected = """OPENQASM 3.0;
input float theta;
qubit[1] __qubits__;
gpi(2.0 * theta) __qubits__[0];"""
    assert parametric.to_ir() == parametric_fp.to_ir() == expected


def test_sim_expressions():
    @aq.main
    def parametric(phi):
        rx(0, 2 * phi)
        measure(0)

    measurements = _test_parametric_on_local_sim(parametric, {"phi": np.pi / 2})
    assert 0 not in measurements["__bit_0__"]


def test_multi_parameter_expressions():
    """Test expressions of multiple free parameters."""

    @aq.main
    def parametric(alpha, theta):
        expr = alpha * theta
        gpi(0, expr)

    expected = """OPENQASM 3.0;
input float alpha;
input float theta;
qubit[1] __qubits__;
gpi(alpha * theta) __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_bound_parameter_expressions():
    """Test expressions of free parameters bound to specific values."""

    @aq.main
    def parametric(phi):
        rx(0, 2 * phi)

    expected = """OPENQASM 3.0;
float phi = 1.5707963267948966;
qubit[1] __qubits__;
rx(2.0 * phi) __qubits__[0];"""
    assert parametric.make_bound_program({"phi": np.pi / 2}).to_ir() == expected


def test_partially_bound_parameter_expressions():
    """Test expressions of free parameters partially bound to specific values."""

    @aq.main
    def parametric(prefactor, theta):
        expr = prefactor * theta
        gpi(0, expr)

    expected = """OPENQASM 3.0;
float prefactor = 3;
input float theta;
qubit[1] __qubits__;
gpi(prefactor * theta) __qubits__[0];"""
    assert parametric.make_bound_program({"prefactor": 3}).to_ir() == expected


def test_subroutine_parameter_expressions():
    """Test expressions of free parameters passed to subroutines."""

    @aq.subroutine
    def rotate(theta: float):
        rx(0, 3 * theta)

    @aq.main
    def parametric(alpha):
        rotate(2 * alpha)

    expected = """OPENQASM 3.0;
def rotate(float theta) {
    rx(3 * theta) __qubits__[0];
}
input float alpha;
qubit[1] __qubits__;
rotate(2.0 * alpha);"""
    assert parametric.to_ir() == expected


def test_gate_parameter_expressions():
    """Test expressions of free parameters passed to custom gates."""

    @aq.gate
    def rotate(q: aq.Qubit, theta: float):
        rx(q, 3 * theta)

    @aq.main
    def parametric(alpha):
        rotate(0, 2 * alpha)

    expected = """OPENQASM 3.0;
gate rotate(theta) q {
    rx(3 * theta) q;
}
input float alpha;
qubit[1] __qubits__;
rotate(2.0 * alpha) __qubits__[0];"""
    assert parametric.to_ir() == expected


def test_conditional_parameter_expressions():
    """Test expressions of free parameters contained in conditional statements."""

    @aq.main
    def parametric(phi):
        if 2 * phi > np.pi:
            h(0)
        measure(0)

    expected = """OPENQASM 3.0;
input float phi;
qubit[1] __qubits__;
float __float_0__ = 2.0 * phi;
bool __bool_1__;
__bool_1__ = __float_0__ > 3.141592653589793;
if (__bool_1__) {
    h __qubits__[0];
}
bit __bit_2__;
__bit_2__ = measure __qubits__[0];"""
    assert parametric.to_ir() == expected


@pytest.mark.xfail(
    reason="Regression: n is constructed as a FreeParameter api.py:L251, which passed as a FloatVar"
)
def test_parameter_expressions_range_index():
    """Test expressions of free parameters contained in a range index."""

    @aq.main
    def two_n_hs(n: int):
        for _ in aq.range(2 * n):
            h(0)
        measure(0)

    expected = """OPENQASM 3.0;
input int[32] n;
qubit[1] __qubits__;
for int _ in [0:2 * n - 1] {
    h __qubits__[0];
}
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""
    assert two_n_hs.to_ir() == expected
    _test_parametric_on_local_sim(two_n_hs, {"n": 3})
