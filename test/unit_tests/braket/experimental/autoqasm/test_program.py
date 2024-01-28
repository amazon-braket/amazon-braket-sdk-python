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

"""Tests for the program module."""

import itertools
from multiprocessing.pool import ThreadPool
from unittest.mock import patch

import oqpy.base
import pytest

import braket.experimental.autoqasm as aq
from braket.circuits import FreeParameter
from braket.circuits.serialization import IRType
from braket.experimental.autoqasm.instructions import cnot, measure, rx


def test_program_conversion_context() -> None:
    """Tests the ProgramConversionContext class."""
    prog = aq.program.ProgramConversionContext()
    initial_oqpy_program = prog.get_oqpy_program()
    assert len(prog._oqpy_program_stack) == 1

    new_oqpy_program = oqpy.Program()
    with prog.push_oqpy_program(new_oqpy_program):
        assert len(prog._oqpy_program_stack) == 2
        assert prog.get_oqpy_program() == new_oqpy_program

    assert prog.get_oqpy_program() == initial_oqpy_program
    assert len(prog._oqpy_program_stack) == 1


def test_get_expression_var_invalid_name():
    """Tests the get_expression_var function."""
    prog = aq.program.ProgramConversionContext()
    prog.register_parameter("alpha")
    with pytest.raises(aq.errors.ParameterNotFoundError):
        prog.get_expression_var(FreeParameter("not_a_parameter"))
    with pytest.raises(aq.errors.ParameterNotFoundError):
        prog.get_expression_var(3 * FreeParameter("also_not_a_parameter"))


def test_build_program() -> None:
    """Tests the aq.build_program function."""
    with pytest.raises(AssertionError):
        aq.program.get_program_conversion_context()

    with aq.build_program() as program_conversion_context:
        assert aq.program.get_program_conversion_context() == program_conversion_context
        with aq.build_program() as inner_context:
            assert inner_context is program_conversion_context
            assert aq.program.get_program_conversion_context() == inner_context

    with pytest.raises(AssertionError):
        aq.program.get_program_conversion_context()


def test_to_ir() -> None:
    """Tests that an appropriate error is raised for unsupported ir_types."""
    with aq.build_program() as program_conversion_context:
        aq.instructions.h(0)
    prog = program_conversion_context.make_program()
    # No error for OpenQASM
    prog.to_ir(IRType.OPENQASM)

    with pytest.raises(ValueError):
        prog.to_ir(IRType.JAQCD)


def test_multiprocessing() -> None:
    """Tests multiprocessing with the aq.Program object."""

    @aq.subroutine
    def circuit(angle: float):
        rx(0, angle)
        cnot(0, 1)

    def build_zne(scale: int, angle: float):
        @aq.main
        def zne() -> aq.BitVar:
            for i in aq.range(scale):
                circuit(angle)
            return measure(1)

        return zne

    scales = [2, 4, 6]
    angles = [0.1, 0.2, 0.3]
    with ThreadPool(processes=5) as executor:
        programs = executor.map(
            lambda args: build_zne(*args),
            [(scale, angle) for scale, angle in itertools.product(scales, angles)],
        )

    def expected(scale, angle):
        return (
            """OPENQASM 3.0;
def circuit(float[64] angle) {
    rx(angle) __qubits__[0];
    cnot __qubits__[0], __qubits__[1];
}
output bit retval_;
qubit[2] __qubits__;
for int i in [0:"""
            + str(scale)
            + """ - 1] {
    circuit("""
            + str(angle)
            + """);
}
bit __bit_0__;
__bit_0__ = measure __qubits__[1];
retval_ = __bit_0__;"""
        )

    for i, (scale, angle) in enumerate(itertools.product(scales, angles)):
        assert programs[i].to_ir() == expected(scale, angle)


@patch("builtins.print")
def test_to_ir_highlighted(mock_print):
    @aq.subroutine
    def sub(q0: int):
        if aq.instructions.measure(q0):
            aq.instructions.x(1)

    @aq.main(num_qubits=3)
    def teleportation(theta):
        sub(0)
        aq.instructions.rx(1, theta)

    expected = (
        b"\x1b[36mOPENQASM\x1b[39;49;00m\x1b[37m \x1b[39;49;00m3.0;\x1b[37m\x1b[39;49;00m\n"
        b"\x1b[34mdef\x1b[39;49;00m\x1b[37m \x1b[39;49;00m\x1b[32msub\x1b[39;49;00m(\x1b[36mint"
        b"\x1b[39;49;00m[\x1b[34m32\x1b[39;49;00m]\x1b[37m \x1b[39;49;00mq0)\x1b[37m "
        b"\x1b[39;49;00m{\x1b[37m\x1b[39;49;00m\n\x1b[37m    \x1b[39;49;00m\x1b[36mbit"
        b"\x1b[39;49;00m\x1b[37m \x1b[39;49;00m__bit_0__;\x1b[37m\x1b[39;49;00m\n\x1b[37m"
        b"    \x1b[39;49;00m__bit_0__\x1b[37m \x1b[39;49;00m=\x1b[37m \x1b[39;49;00m"
        b"\x1b[35mmeasure\x1b[39;49;00m\x1b[37m \x1b[39;49;00m__qubits__[q0];\x1b[37m"
        b"\x1b[39;49;00m\n\x1b[37m    \x1b[39;49;00m\x1b[34mif\x1b[39;49;00m\x1b[37m "
        b"\x1b[39;49;00m(__bit_0__)\x1b[37m \x1b[39;49;00m{\x1b[37m\x1b[39;49;00m\n\x1b[37m"
        b"        \x1b[39;49;00m\x1b[32mx\x1b[39;49;00m\x1b[37m \x1b[39;49;00m__qubits__["
        b"\x1b[34m1\x1b[39;49;00m];\x1b[37m\x1b[39;49;00m\n\x1b[37m    \x1b[39;49;00m}"
        b"\x1b[37m\x1b[39;49;00m\n}\x1b[37m\x1b[39;49;00m\n\x1b[36minput\x1b[39;49;00m\x1b[37m "
        b"\x1b[39;49;00m\x1b[36mfloat\x1b[39;49;00m[\x1b[34m64\x1b[39;49;00m]\x1b[37m "
        b"\x1b[39;49;00mtheta;\x1b[37m\x1b[39;49;00m\n\x1b[36mqubit\x1b[39;49;00m["
        b"\x1b[34m3\x1b[39;49;00m]\x1b[37m \x1b[39;49;00m__qubits__;\x1b[37m\x1b[39;49;00m\n"
        b"\x1b[32msub\x1b[39;49;00m(\x1b[34m0\x1b[39;49;00m);\x1b[37m\x1b[39;49;00m\n\x1b[32mrx"
        b"\x1b[39;49;00m(theta)\x1b[37m \x1b[39;49;00m__qubits__[\x1b[34m1\x1b[39;49;00m];"
        b"\x1b[37m\x1b[39;49;00m\n"
    ).decode("utf-8")
    teleportation.display()
    mock_print.assert_called_with(expected)
