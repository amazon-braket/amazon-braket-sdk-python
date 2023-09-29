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

"""Tests for the pulse control module."""

import textwrap

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm import errors, pulse
from braket.experimental.autoqasm.instructions import h, rx


def test_gate_calibrations_fixed_args():
    """test gate calibrations with fixed args"""

    @aq.gate_calibration(implements=h, target="$0")
    def cal_1():
        pulse.barrier("$0")

    @aq.gate_calibration(implements=rx, target="$1", angle=1.789)
    def cal_2():
        pulse.delay("$1", 0.123)

    @aq.main
    def my_program():
        h("$0")
        rx("$1", 1.0)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        defcal h $0 {
            barrier $0;
        }
        defcal rx(1.789) $1 {
            delay[123.0ms] $1;
        }
        h $0;
        rx(1.0) $1;
        """
    ).strip()
    qasm = my_program().with_calibrations([cal_1, cal_2]).to_ir()
    assert qasm == expected


def test_gate_calibrations_variable_args():
    """test gate calibrations with variable args"""

    @aq.gate_calibration(implements=rx, target="$1")
    def cal_1(angle: float):
        pulse.delay("$1", angle)

    @aq.main
    def my_program():
        rx("$1", 1.0)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        defcal rx(angle[32] angle) $1 {
            delay[(angle) * 1s] $1;
        }
        rx(1.0) $1;
        """
    ).strip()
    qasm = my_program().with_calibrations(cal_1).to_ir()
    assert qasm == expected


def test_gate_calibrations_invalid_args():
    """test gate calibrations with invalid args name"""

    @aq.gate_calibration(implements=rx, target="$1", foo=0)
    def cal_1(angle: float):
        pulse.delay("$1", angle)

    @aq.main
    def my_program():
        rx("$1", 1.0)

    with pytest.raises(errors.InvalidCalibrationDefinition):
        _ = my_program().with_calibrations(cal_1)


def test_gate_calibrations_invalid_type():
    """test gate calibrations with invalid args type"""

    @aq.gate_calibration(implements=rx, target=0.123)
    def cal_1(angle: float):
        pulse.delay("$1", angle)

    @aq.gate_calibration(implements=rx, target={"foo": "bar"})
    def cal_2(angle: float):
        pulse.delay("$1", angle)

    @aq.gate_calibration(implements=rx, target=0, angle="$0")
    def cal_3():
        pulse.delay("$1", 0.123)

    @aq.gate_calibration(implements=rx, target=0)
    def cal_4(angle: aq.Qubit):
        pulse.delay("$1", angle)

    @aq.gate_calibration(implements=rx)
    def cal_5(target: float, angle: aq.Qubit):
        pulse.delay("$0", angle)

    @aq.main
    def my_program():
        rx("$1", 1.0)

    for cal in [cal_1, cal_2, cal_3, cal_4, cal_5]:
        with pytest.raises(errors.ParameterTypeError):
            _ = my_program().with_calibrations(cal)


def test_gate_calibrations_insufficient_args():
    """test gate calibrations with insufficient args"""

    @aq.gate_calibration(implements=rx, target="$1")
    def cal_1():
        pulse.delay("$1", 0.123)

    @aq.gate_calibration(implements=rx)
    def cal_2(angle: float):
        pulse.delay("$1", angle)

    @aq.main
    def my_program():
        rx("$1", 1.0)

    with pytest.raises(errors.InvalidCalibrationDefinition):
        _ = my_program().with_calibrations(cal_1)

    with pytest.raises(errors.InvalidCalibrationDefinition):
        _ = my_program().with_calibrations(cal_2)


def test_gate_calibrations_duplicated_args():
    """test gate calibrations with duplicated args"""

    @aq.gate_calibration(implements=rx, target="$1", angle=0.123)
    def cal_1(angle: float):
        pulse.delay("$1", angle)

    @aq.main
    def my_program():
        rx("$1", 1.0)

    with pytest.raises(errors.InvalidCalibrationDefinition):
        _ = my_program().with_calibrations(cal_1)


def test_gate_calibrations_invalid_instructions():
    """test gate calibrations with invalid instructions that are not pulse"""

    @aq.gate_calibration(implements=rx, target="$1")
    def cal_1(angle: float):
        h(0)
        pulse.delay("$1", angle)

    @aq.main
    def my_program():
        rx("$1", 1.0)

    with pytest.raises(errors.InvalidCalibrationDefinition):
        _ = my_program().with_calibrations(cal_1)


def test_gate_calibrations_bind_calibrations_not_inplace():
    """test that bind_calibrations does not modify the original program"""

    @aq.gate_calibration(implements=rx, target="$1")
    def cal_1(angle: float):
        pulse.delay("$1", angle)

    @aq.main
    def my_program():
        rx("$1", 1.0)

    program_1 = my_program()
    _ = program_1.with_calibrations(cal_1)

    program_2 = my_program()

    assert program_1.to_ir() == program_2.to_ir()


def test_gate_calibrations_with_gate_definition():
    """test gate calibrations on gate defined by aq.gate"""

    @aq.gate
    def my_gate(q: aq.Qubit, a: float):
        h(q)

    @aq.gate_calibration(implements=my_gate, q="$0")
    def cal_1(a: float):
        pulse.barrier("$0")
        pulse.delay("$0", a)

    @aq.main
    def my_program():
        my_gate(2, 0.123)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        gate my_gate(a) q {
            h q;
        }
        defcal my_gate(angle[32] a) $0 {
            barrier $0;
            delay[(a) * 1s] $0;
        }
        qubit[3] __qubits__;
        my_gate(0.123) __qubits__[2];
        """
    ).strip()
    qasm = my_program().with_calibrations(cal_1).to_ir()
    assert qasm == expected
