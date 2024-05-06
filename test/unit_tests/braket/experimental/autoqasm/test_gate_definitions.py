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

"""Tests for the gates module."""

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import (
    ccnot,
    cnot,
    cphaseshift,
    cphaseshift00,
    cphaseshift01,
    cphaseshift10,
    cswap,
    cv,
    cy,
    cz,
    ecr,
    gphase,
    gpi,
    gpi2,
    h,
    i,
    iswap,
    measure,
    ms,
    phaseshift,
    prx,
    pswap,
    reset,
    rx,
    ry,
    rz,
    s,
    si,
    swap,
    t,
    ti,
    u,
    v,
    vi,
    x,
    xx,
    xy,
    y,
    yy,
    z,
    zz,
)


def test_bell_state_prep(bell_state_program) -> None:
    """Tests Bell state generation without measurement."""
    expected = """OPENQASM 3.0;
qubit[2] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];"""
    actual_result = bell_state_program.build().to_ir()
    assert actual_result == expected


def test_physical_q_bell_state_prep(physical_bell_program) -> None:
    """Tests Bell state generation without measurement on particular qubits."""
    expected = """OPENQASM 3.0;
h $0;
cnot $0, $5;"""
    actual_result = physical_bell_program.build().to_ir()
    assert actual_result == expected


def test_bell_with_measure() -> None:
    """Tests Bell state with measurement result stored in an undeclared variable."""
    with aq.build_program() as program_conversion_context:
        reset(0)
        h(0)
        cnot(0, 1)
        measure(0)
    expected = """OPENQASM 3.0;
reset __qubits__[0];
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];"""

    qasm = program_conversion_context.make_program().to_ir()
    assert qasm == expected.strip()


@pytest.mark.parametrize(
    "gate,qubits,params,expected_qasm",
    [
        (ccnot, [0, 1, 2], [], "\nccnot __qubits__[0], __qubits__[1], __qubits__[2];"),
        (cnot, [0, 1], [], "\ncnot __qubits__[0], __qubits__[1];"),
        (cphaseshift, [0, 1], [0.1], "\ncphaseshift(0.1) __qubits__[0], __qubits__[1];"),
        (cphaseshift00, [0, 1], [0.1], "\ncphaseshift00(0.1) __qubits__[0], __qubits__[1];"),
        (cphaseshift01, [0, 1], [0.1], "\ncphaseshift01(0.1) __qubits__[0], __qubits__[1];"),
        (cphaseshift10, [0, 1], [0.1], "\ncphaseshift10(0.1) __qubits__[0], __qubits__[1];"),
        (cswap, [0, 1, 2], [], "\ncswap __qubits__[0], __qubits__[1], __qubits__[2];"),
        (cv, [0, 1], [], "\ncv __qubits__[0], __qubits__[1];"),
        (cy, [0, 1], [], "\ncy __qubits__[0], __qubits__[1];"),
        (cz, [0, 1], [], "\ncz __qubits__[0], __qubits__[1];"),
        (ecr, [0, 1], [], "\necr __qubits__[0], __qubits__[1];"),
        (gphase, [], [0.1], "\ngphase(0.1) ;"),
        (gpi, [0], [0.1], "\ngpi(0.1) __qubits__[0];"),
        (gpi2, [0], [0.1], "\ngpi2(0.1) __qubits__[0];"),
        (h, [0], [], "\nh __qubits__[0];"),
        (i, [0], [], "\ni __qubits__[0];"),
        (iswap, [0, 1], [], "\niswap __qubits__[0], __qubits__[1];"),
        (ms, [0, 1], [0.1, 0.2, 0.3], "\nms(0.1, 0.2, 0.3) __qubits__[0], __qubits__[1];"),
        (phaseshift, [0], [0.1], "\nphaseshift(0.1) __qubits__[0];"),
        (prx, [0], [0.1, 0.2], "\nprx(0.1, 0.2) __qubits__[0];"),
        (pswap, [0, 1], [0.1], "\npswap(0.1) __qubits__[0], __qubits__[1];"),
        (rx, [0], [0.1], "\nrx(0.1) __qubits__[0];"),
        (ry, [0], [0.1], "\nry(0.1) __qubits__[0];"),
        (rz, [0], [0.1], "\nrz(0.1) __qubits__[0];"),
        (s, [0], [], "\ns __qubits__[0];"),
        (si, [0], [], "\nsi __qubits__[0];"),
        (swap, [0, 1], [], "\nswap __qubits__[0], __qubits__[1];"),
        (t, [0], [], "\nt __qubits__[0];"),
        (ti, [0], [], "\nti __qubits__[0];"),
        (u, [0], [0.1, 0.2, 0.3], "\nu(0.1, 0.2, 0.3) __qubits__[0];"),
        (v, [0], [], "\nv __qubits__[0];"),
        (vi, [0], [], "\nvi __qubits__[0];"),
        (x, [0], [], "\nx __qubits__[0];"),
        (xx, [0, 1], [0.1], "\nxx(0.1) __qubits__[0], __qubits__[1];"),
        (xy, [0, 1], [0.1], "\nxy(0.1) __qubits__[0], __qubits__[1];"),
        (y, [0], [], "\ny __qubits__[0];"),
        (yy, [0, 1], [0.1], "\nyy(0.1) __qubits__[0], __qubits__[1];"),
        (z, [0], [], "\nz __qubits__[0];"),
        (zz, [0, 1], [0.1], "\nzz(0.1) __qubits__[0], __qubits__[1];"),
    ],
)
def test_gates(gate, qubits, params, expected_qasm) -> None:
    """Tests quantum gates."""
    with aq.build_program() as program_conversion_context:
        gate(*qubits, *params)

    assert expected_qasm in program_conversion_context.make_program().to_ir()


@pytest.mark.parametrize(
    "control,control_state,expected_qasm",
    [
        (0, None, "\nctrl @ x __qubits__[0], __qubits__[1];"),
        ([0], None, "\nctrl @ x __qubits__[0], __qubits__[1];"),
        (0, "1", "\nctrl @ x __qubits__[0], __qubits__[1];"),
        ([0], "0", "\nnegctrl @ x __qubits__[0], __qubits__[1];"),
        ([0], 0, "\nnegctrl @ x __qubits__[0], __qubits__[1];"),
        ([0], [0], "\nnegctrl @ x __qubits__[0], __qubits__[1];"),
    ],
)
def test_gate_modifiers_single_control(control, control_state, expected_qasm) -> None:
    """Tests quantum gate modifiers to create a singly-controlled X gate."""
    with aq.build_program() as program_conversion_context:
        x(1, control=control, control_state=control_state)

    assert expected_qasm in program_conversion_context.make_program().to_ir()


@pytest.mark.parametrize(
    "control,control_state,expected_qasm",
    [
        ([0, 1], "11", "\nctrl(2) @ x __qubits__[0], __qubits__[1], __qubits__[2];"),
        ([0, 1], [1, 1], "\nctrl(2) @ x __qubits__[0], __qubits__[1], __qubits__[2];"),
        ([0, 1], 3, "\nctrl(2) @ x __qubits__[0], __qubits__[1], __qubits__[2];"),
        ([0, 1], "10", "\nctrl @ negctrl @ x __qubits__[0], __qubits__[1], __qubits__[2];"),
    ],
)
def test_gate_modifiers_multi_control(control, control_state, expected_qasm) -> None:
    """Tests quantum gate modifiers to create a multiply-controlled X gate."""
    with aq.build_program() as program_conversion_context:
        x(2, control=control, control_state=control_state)

    assert expected_qasm in program_conversion_context.make_program().to_ir()


@pytest.mark.parametrize(
    "control,control_state,power,expected_qasm",
    [
        (None, None, -2.0, "\npow(-2.0) @ x __qubits__[1];"),
        ([0], "1", 0.5, "\nctrl @ pow(0.5) @ x __qubits__[0], __qubits__[1];"),
    ],
)
def test_gate_modifiers_power(control, control_state, power, expected_qasm) -> None:
    """Tests quantum gate modifiers to create gates raised to powers."""
    with aq.build_program() as program_conversion_context:
        x(1, control=control, control_state=control_state, power=power)

    assert expected_qasm in program_conversion_context.make_program().to_ir()


def test_gate_modifiers_physical_qubits() -> None:
    with aq.build_program() as program_conversion_context:
        x("$1", control="$0")

    assert "\nctrl @ x $0, $1;" in program_conversion_context.make_program().to_ir()


def test_invalid_gate_modifiers() -> None:
    """Tests invalid quantum gate modifiers."""
    with aq.build_program() as _:
        with pytest.raises(ValueError, match="length greater than the specified number of qubits"):
            x(1, control=None, control_state="00")
        with pytest.raises(ValueError, match="length greater than the specified number of qubits"):
            x(1, control=0, control_state="00")
        with pytest.raises(ValueError, match="length greater than the specified number of qubits"):
            x(1, control=0, control_state=3)
