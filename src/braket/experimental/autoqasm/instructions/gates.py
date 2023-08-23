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


"""Quantum gates, unitary instructions, that apply to qubits.
"""

from .instructions import _qubit_instruction
from .qubits import QubitIdentifierType


def ccnot(
    control_0: QubitIdentifierType,
    control_1: QubitIdentifierType,
    target: QubitIdentifierType,
) -> None:
    """CCNOT gate or Toffoli gate.

    Args:
        control_0 (QubitIdentifierType): Control qubit 0.
        control_1 (QubitIdentifierType): Control qubit 1.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("ccnot", [control_0, control_1, target])


def cnot(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
) -> None:
    """Controlled NOT gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cnot", [control, target])


def cphaseshift(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """Controlled phase shift gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift", [control, target], angle)


def cphaseshift00(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """Controlled phase shift gate for phasing the \\|00> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift00", [control, target], angle)


def cphaseshift01(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """Controlled phase shift gate for phasing the \\|01> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift01", [control, target], angle)


def cphaseshift10(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """Controlled phase shift gate for phasing the \\|10> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("cphaseshift10", [control, target], angle)


def cswap(
    control: QubitIdentifierType,
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
) -> None:
    """Controlled Swap gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("cswap", [control, target_0, target_1])


def cv(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
) -> None:
    """Controlled Sqrt of NOT gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cv", [control, target])


def cy(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
) -> None:
    """Controlled Pauli-Y gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cy", [control, target])


def cz(
    control: QubitIdentifierType,
    target: QubitIdentifierType,
) -> None:
    """Controlled Pauli-Z gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("cz", [control, target])


def ecr(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
) -> None:
    """An echoed RZX(pi/2) gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("ecr", [target_0, target_1])


def gpi(
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """IonQ GPi gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("gpi", [target], angle)


def gpi2(
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """IonQ GPi2 gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("gpi2", [target], angle)


def h(
    target: QubitIdentifierType,
) -> None:
    """Hadamard gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("h", [target])


def i(
    target: QubitIdentifierType,
) -> None:
    """Identity gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("i", [target])


def iswap(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
) -> None:
    """ISwap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("iswap", [target_0, target_1])


def ms(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle_0: float,
    angle_1: float,
    angle_2: float,
) -> None:
    """IonQ Mølmer-Sørenson gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle_0 (float): Rotation angle 0 in radians.
        angle_1 (float): Rotation angle 1 in radians.
        angle_2 (float): Rotation angle 2 in radians.

    """
    _qubit_instruction("ms", [target_0, target_1], angle_0, angle_1, angle_2)


def phaseshift(
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """Phase shift gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("phaseshift", [target], angle)


def pswap(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: float,
) -> None:
    """PSwap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("pswap", [target_0, target_1], angle)


def rx(
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """X-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("rx", [target], angle)


def ry(
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """Y-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("ry", [target], angle)


def rz(
    target: QubitIdentifierType,
    angle: float,
) -> None:
    """Z-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("rz", [target], angle)


def s(
    target: QubitIdentifierType,
) -> None:
    """S gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("s", [target])


def si(
    target: QubitIdentifierType,
) -> None:
    """Conjugate transpose of S gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("si", [target])


def swap(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
) -> None:
    """Swap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.

    """
    _qubit_instruction("swap", [target_0, target_1])


def t(
    target: QubitIdentifierType,
) -> None:
    """T gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("t", [target])


def ti(
    target: QubitIdentifierType,
) -> None:
    """Conjugate transpose of T gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("ti", [target])


def v(
    target: QubitIdentifierType,
) -> None:
    """Square root of not gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("v", [target])


def vi(
    target: QubitIdentifierType,
) -> None:
    """Conjugate transpose of square root of not gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("vi", [target])


def x(
    target: QubitIdentifierType,
) -> None:
    """Pauli-X gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("x", [target])


def xx(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: float,
) -> None:
    """Ising XX coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("xx", [target_0, target_1], angle)


def xy(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: float,
) -> None:
    """XY gates

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("xy", [target_0, target_1], angle)


def y(
    target: QubitIdentifierType,
) -> None:
    """Pauli-Y gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("y", [target])


def yy(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: float,
) -> None:
    """Ising YY coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("yy", [target_0, target_1], angle)


def z(
    target: QubitIdentifierType,
) -> None:
    """Pauli-Z gate.

    Args:
        target (QubitIdentifierType): Target qubit.

    """
    _qubit_instruction("z", [target])


def zz(
    target_0: QubitIdentifierType,
    target_1: QubitIdentifierType,
    angle: float,
) -> None:
    """Ising ZZ coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.

    """
    _qubit_instruction("zz", [target_0, target_1], angle)
