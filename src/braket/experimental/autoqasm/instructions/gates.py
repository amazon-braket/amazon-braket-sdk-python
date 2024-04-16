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


"""Quantum gates, unitary instructions, that apply to qubits."""

from typing import Union

import oqpy

from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.experimental.autoqasm.instructions.instructions import _qubit_instruction
from braket.experimental.autoqasm.types import QubitIdentifierType

GateParameterType = Union[float, FreeParameterExpression, oqpy._ClassicalVar]


def ccnot(
    control_0: QubitIdentifierType,
    control_1: QubitIdentifierType,
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """CCNOT gate or Toffoli gate.

    Args:
        control_0 (QubitIdentifierType): Control qubit 0.
        control_1 (QubitIdentifierType): Control qubit 1.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("ccnot", [control_0, control_1, target], **kwargs)


def cnot(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Controlled NOT gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cnot", [control, target], **kwargs)


def cphaseshift(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Controlled phase shift gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift", [control, target], angle, **kwargs)


def cphaseshift00(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Controlled phase shift gate for phasing the \\|00> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift00", [control, target], angle, **kwargs)


def cphaseshift01(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Controlled phase shift gate for phasing the \\|01> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift01", [control, target], angle, **kwargs)


def cphaseshift10(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Controlled phase shift gate for phasing the \\|10> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift10", [control, target], angle, **kwargs)


def cswap(
    control: QubitIdentifierType,
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    **kwargs,
) -> None:
    """Controlled Swap gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("cswap", [control, target_0, target_1], **kwargs)


def cv(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Controlled Sqrt of NOT gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cv", [control, target], **kwargs)


def cy(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Controlled Pauli-Y gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cy", [control, target], **kwargs)


def cz(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Controlled Pauli-Z gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cz", [control, target], **kwargs)


def ecr(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    **kwargs,
) -> None:
    """An echoed RZX(pi/2) gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("ecr", [target_0, target_1], **kwargs)


def gphase(
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Global phase gate.

    Args:
        angle (GateParameterType): Global phase in radians.

    """
    _qubit_instruction("gphase", [], angle, **kwargs)


def gpi(
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """IonQ GPi gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("gpi", [target], angle, **kwargs)


def gpi2(
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """IonQ GPi2 gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("gpi2", [target], angle, **kwargs)


def h(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Hadamard gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("h", [target], **kwargs)


def i(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Identity gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("i", [target], **kwargs)


def iswap(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    **kwargs,
) -> None:
    """ISwap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("iswap", [target_0, target_1], **kwargs)


def ms(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle_0: GateParameterType,
    angle_1: GateParameterType,
    angle_2: GateParameterType,
    **kwargs,
) -> None:
    """IonQ Mølmer-Sørenson gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle_0 (GateParameterType): Rotation angle 0 in radians.
        angle_1 (GateParameterType): Rotation angle 1 in radians.
        angle_2 (GateParameterType): Rotation angle 2 in radians.

    """
    _qubit_instruction("ms", [target_0, target_1], angle_0, angle_1, angle_2, **kwargs)


def phaseshift(
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Phase shift gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("phaseshift", [target], angle, **kwargs)


def pswap(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """PSwap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("pswap", [target_0, target_1], angle, **kwargs)


def rx(
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """X-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("rx", [target], angle, **kwargs)


def ry(
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Y-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("ry", [target], angle, **kwargs)


def rz(
    target: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Z-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("rz", [target], angle, **kwargs)


def s(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """S gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("s", [target], **kwargs)


def si(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Conjugate transpose of S gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("si", [target], **kwargs)


def swap(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    **kwargs,
) -> None:
    """Swap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("swap", [target_0, target_1], **kwargs)


def t(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """T gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("t", [target], **kwargs)


def ti(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Conjugate transpose of T gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("ti", [target], **kwargs)


def u(
    target: QubitIdentifierType,
    angle_0: GateParameterType,
    angle_1: GateParameterType,
    angle_2: GateParameterType,
    **kwargs,
) -> None:
    """Generalized single-qubit rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle_0 (GateParameterType): Rotation angle theta in radians.
        angle_1 (GateParameterType): Rotation angle phi in radians.
        angle_2 (GateParameterType): Rotation angle lambda in radians.

    """
    _qubit_instruction("u", [target], angle_0, angle_1, angle_2, **kwargs)


def v(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Square root of not gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("v", [target], **kwargs)


def vi(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Conjugate transpose of square root of not gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("vi", [target], **kwargs)


def x(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Pauli-X gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("x", [target], **kwargs)


def xx(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Ising XX coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("xx", [target_0, target_1], angle, **kwargs)


def xy(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """XY gates

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("xy", [target_0, target_1], angle, **kwargs)


def y(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Pauli-Y gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("y", [target], **kwargs)


def yy(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Ising YY coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("yy", [target_0, target_1], angle, **kwargs)


def z(
    target: QubitIdentifierType,
    **kwargs,
) -> None:
    """Pauli-Z gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("z", [target], **kwargs)


def zz(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: GateParameterType,
    **kwargs,
) -> None:
    """Ising ZZ coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (GateParameterType): Rotation angle in radians.

    """
    _qubit_instruction("zz", [target_0, target_1], angle, **kwargs)
