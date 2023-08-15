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
from braket.experimental.autoqasm import program

from .qubits import _qubit


def ccnot(control_0: int, control_1: int, target: int) -> None:
    """CCNOT gate or Toffoli gate.

    Args:
        control_0 (QubitIdentifierType): Control qubit 0.
        control_1 (QubitIdentifierType): Control qubit 1.
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(control_0), _qubit(control_1), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "ccnot")


def cnot(control: int, target: int) -> None:
    """Controlled NOT gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cnot")


def cphaseshift(control: int, target: int, angle: float) -> None:
    """Controlled phase shift gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cphaseshift", angle)


def cphaseshift00(control: int, target: int, angle: float) -> None:
    """Controlled phase shift gate for phasing the \\|00> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cphaseshift00", angle)


def cphaseshift01(control: int, target: int, angle: float) -> None:
    """Controlled phase shift gate for phasing the \\|01> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cphaseshift01", angle)


def cphaseshift10(control: int, target: int, angle: float) -> None:
    """Controlled phase shift gate for phasing the \\|10> state.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cphaseshift10", angle)


def cswap(control: int, target_0: int, target_1: int) -> None:
    """Controlled Swap gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
    """
    qubits = [_qubit(control), _qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cswap")


def cv(control: int, target: int) -> None:
    """Controlled Sqrt of NOT gate.

    Args:
        control_0 (QubitIdentifierType): Control qubit 0.
        target_0 (QubitIdentifierType): Target qubit 0.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cv")


def cy(control: int, target: int) -> None:
    """Controlled Pauli-Y gate.

    Args:
        control (QubitIdentifierType): Control qubit.
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cy")


def cz(control: int, target: int) -> None:
    """Controlled Pauli-Z gate.

    Args:
        control_0 (QubitIdentifierType): Control qubit.
        target_0 (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(control), _qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "cz")


def ecr(target_0: int, target_1: int) -> None:
    """An echoed RZX(pi/2) gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "ecr")


def gpi(target: int, angle: float) -> None:
    """IonQ GPi gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "gpi", angle)


def gpi2(target: int, angle: float) -> None:
    """IonQ GPi2 gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "gpi2", angle)


def h(target: int) -> None:
    """Hadamard gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "h")


def i(target: int) -> None:
    """Identity gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "i")


def iswap(target_0: int, target_1: int) -> None:
    """ISwap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "iswap")


def ms(target_0: int, target_1: int, angle_0: float, angle_1: float, angle_2: float) -> None:
    """IonQ Mølmer-Sørenson gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle_0 (float): Rotation angle 0 in radians.
        angle_1 (float): Rotation angle 1 in radians.
        angle_2 (float): Rotation angle 2 in radians.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    angles = [angle_0, angle_1, angle_2]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "ms", *angles)


def phaseshift(target: int, angle: float) -> None:
    """Phase shift gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "phaseshift", angle)


def pswap(target_0: int, target_1: int, angle: float) -> None:
    """PSwap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    angles = [angle]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "pswap", *angles)


def rx(target: int, angle: float) -> None:
    """X-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "rx", angle)


def ry(target: int, angle: float) -> None:
    """Y-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "ry", angle)


def rz(target: int, angle: float) -> None:
    """Z-axis rotation gate.

    Args:
        target (QubitIdentifierType): Target qubit.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "rz", angle)


def s(target: int) -> None:
    """S gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "s")


def si(target: int) -> None:
    """Conjugate transpose of S gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "si")


def swap(target_0: int, target_1: int) -> None:
    """Swap gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "swap")


def t(target: int) -> None:
    """T gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "t")


def ti(target: int) -> None:
    """Conjugate transpose of T gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "ti")


def v(target: int) -> None:
    """Square root of not gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "v")


def vi(target: int) -> None:
    """Conjugate transpose of square root of not gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "vi")


def x(target: int) -> None:
    """Pauli-X gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "x")


def xx(target_0: int, target_1: int, angle: float) -> None:
    """Ising XX coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "xx", angle)


def xy(target_0: int, target_1: int, angle: float) -> None:
    """XY gates

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "xy", angle)


def y(target: int) -> None:
    """Pauli-Y gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "y")


def yy(target_0: int, target_1: int, angle: float) -> None:
    """Ising YY coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "yy", angle)


def z(target: int) -> None:
    """Pauli-Z gate.

    Args:
        target (QubitIdentifierType): Target qubit.
    """
    qubits = [_qubit(target)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "z")


def zz(target_0: int, target_1: int, angle: float) -> None:
    """Ising ZZ coupling gate.

    Args:
        target_0 (QubitIdentifierType): Target qubit 0.
        target_1 (QubitIdentifierType): Target qubit 1.
        angle (float): Rotation angle in radians.
    """
    qubits = [_qubit(target_0), _qubit(target_1)]
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(qubits, "zz", angle)
