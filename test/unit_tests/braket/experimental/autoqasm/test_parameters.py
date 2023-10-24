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
from braket.experimental.autoqasm.instructions import cnot, h, measure, rx
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
    """TODO"""

    @aq.main
    def parametric():
        rx(0, FreeParameter("alpha"))
        rx(1, FreeParameter("theta"))
        c = measure([0, 1])

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
    """TODO"""

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
    pass


def test_captured_parameter():
    """Test that a parameter declared in a larger scope is captured
    and functions correctly.
    """
    pass


def test_parameter_expressions():
    pass


def test_parameter_in_args():
    """TODO"""

    @aq.main
    def parametric(theta: float):
        rx(0, theta)

    parametric(FreeParameter("theta"))
    # TODO


def test_parameters_passed_as_args():
    """Test that parameters work when passed as input values."""


def test_multi_angle_gates():
    """Test that FreeParameters work with gates that take multiple inputs."""
    pass


# TODO
# - test parameter declared in subroutine input arg
# - tests on local simulator
# - other input types? local sim doesn't seem to support angle input types
    # - integer inputs:
        # input int basis; // 0 = X basis, 1 = Y basis, 2 = Z basis
        # output bit result;
        # qubit q;

        # // Some complicated circuit...

        # if (basis == 0) h q;
        # else if (basis == 1) rx(π/2) q;
        # result = measure q;
