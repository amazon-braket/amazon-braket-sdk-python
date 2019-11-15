# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import math
from typing import Iterable

import aqx.ir.jaqcd as ir
import numpy as np
from aqx.qdk.circuits import circuit
from aqx.qdk.circuits.angled_gate import AngledGate
from aqx.qdk.circuits.gate import Gate
from aqx.qdk.circuits.instruction import Instruction
from aqx.qdk.circuits.qubit import QubitInput
from aqx.qdk.circuits.qubit_set import QubitSet, QubitSetInput

# TODO: look into adding angle to diagrams

"""
To add a new gate:
    1. Implement the class and extend `Gate`
    2. Add a method with the `@circuit.subroutine(register=True)` decorator. Method name
       will be monkey patched into the Circuit class. This method will be the default way
       clients add this gate to a circuit.
    3. Register the class with the `Gate` class via `Gate.register_gate()`.
"""

# Single qubit gates #


class H(Gate):
    """Hadamard gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["H"])

    def to_ir(self, target: QubitSet):
        return ir.H(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return 1.0 / np.sqrt(2.0) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def h(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of H instructions.

        Examples:
            >>> circ = Circuit().h(0)
            >>> circ = Circuit().h([0, 1, 2])
        """
        return [Instruction(Gate.H(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(H)


class I(Gate):  # noqa: E742, E261
    """Identity gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["I"])

    def to_ir(self, target: QubitSet):
        return ir.I(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def i(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of I instructions.

        Examples:
            >>> circ = Circuit().i(0)
            >>> circ = Circuit().i([0, 1, 2])
        """
        return [Instruction(Gate.I(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(I)


class X(Gate):
    """Pauli-X gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["X"])

    def to_ir(self, target: QubitSet):
        return ir.X(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def x(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of X instructions.

        Examples:
            >>> circ = Circuit().x(0)
            >>> circ = Circuit().x([0, 1, 2])
        """
        return [Instruction(Gate.X(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(X)


class Y(Gate):
    """Pauli-Y gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["Y"])

    def to_ir(self, target: QubitSet):
        return ir.Y(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def y(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of Y instructions.

        Examples:
            >>> circ = Circuit().y(0)
            >>> circ = Circuit().y([0, 1, 2])
        """
        return [Instruction(Gate.Y(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Y)


class Z(Gate):
    """Pauli-Z gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["Z"])

    def to_ir(self, target: QubitSet):
        return ir.Z(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def z(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of Z instructions.

        Examples:
            >>> circ = Circuit().z(0)
            >>> circ = Circuit().z([0, 1, 2])
        """
        return [Instruction(Gate.Z(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Z)


class S(Gate):
    """S gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["S"])

    def to_ir(self, target: QubitSet):
        return ir.S(target=target[0])

    def to_matrix(self) -> np.ndarray:

        return np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def s(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of S instructions.

        Examples:
            >>> circ = Circuit().s(0)
            >>> circ = Circuit().s([0, 1, 2])
        """
        return [Instruction(Gate.S(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(S)


class Si(Gate):
    """Conjugate transpose of S gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["Si"])

    def to_ir(self, target: QubitSet):
        return ir.Si(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1, 0], [0, -1j]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def si(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of Si instructions.

        Examples:
            >>> circ = Circuit().si(0)
            >>> circ = Circuit().si([0, 1, 2])
        """
        return [Instruction(Gate.Si(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Si)


class T(Gate):
    """T gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["T"])

    def to_ir(self, target: QubitSet):
        return ir.T(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(1j * np.pi / 4)]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def t(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of T instructions.

        Examples:
            >>> circ = Circuit().t(0)
            >>> circ = Circuit().t([0, 1, 2])
        """
        return [Instruction(Gate.T(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(T)


class Ti(Gate):
    """Conjugate transpose of T gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["Ti"])

    def to_ir(self, target: QubitSet):
        return ir.Ti(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(-1j * np.pi / 4)]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def ti(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of Ti instructions.

        Examples:
            >>> circ = Circuit().ti(0)
            >>> circ = Circuit().ti([0, 1, 2])
        """
        return [Instruction(Gate.Ti(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Ti)


class V(Gate):
    """Square root of not gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["V"])

    def to_ir(self, target: QubitSet):
        return ir.V(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def v(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of V instructions.

        Examples:
            >>> circ = Circuit().v(0)
            >>> circ = Circuit().v([0, 1, 2])
        """
        return [Instruction(Gate.V(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(V)


class Vi(Gate):
    """Conjugate transpose of square root of not gate."""

    def __init__(self):
        super().__init__(qubit_count=1, ascii_symbols=["Vi"])

    def to_ir(self, target: QubitSet):
        return ir.Vi(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array(([[0.5 - 0.5j, 0.5 + 0.5j], [0.5 + 0.5j, 0.5 - 0.5j]]), dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def vi(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of Vi instructions.

        Examples:
            >>> circ = Circuit().vi(0)
            >>> circ = Circuit().vi([0, 1, 2])
        """
        return [Instruction(Gate.Vi(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Vi)


# Single qubit gates with rotation #


class Rx(AngledGate):
    """X-axis rotation gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=1, ascii_symbols=["Rx"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.Rx(target=target[0], angle=self.angle)

    def to_matrix(self):
        cos = np.cos(self.angle / 2)
        sin = np.sin(self.angle / 2)
        return np.array([[cos, -1j * sin], [-1j * sin, cos]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def rx(target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: Rx instruction.

        Examples:
            >>> circ = Circuit().rx(0, 0.15)
        """
        return [Instruction(Gate.Rx(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Rx)


class Ry(AngledGate):
    """Y-axis rotation gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=1, ascii_symbols=["Ry"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.Ry(target=target[0], angle=self.angle)

    def to_matrix(self):
        cos = np.cos(self.angle / 2)
        sin = np.sin(self.angle / 2)
        return np.array([[cos, -sin], [+sin, cos]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def ry(target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: Ry instruction.

        Examples:
            >>> circ = Circuit().ry(0, 0.15)
        """
        return [Instruction(Gate.Ry(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Ry)


class Rz(AngledGate):
    """Z-axis rotation gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=1, ascii_symbols=["Rz"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.Rz(target=target[0], angle=self.angle)

    def to_matrix(self):
        return np.array(
            [[np.exp(-1j * self.angle / 2), 0], [0, np.exp(1j * self.angle / 2)]], dtype=complex
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def rz(target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: Rz instruction.

        Examples:
            >>> circ = Circuit().rz(0, 0.15)
        """
        return [Instruction(Gate.Rz(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Rz)


class PhaseShift(AngledGate):
    """Phase shift gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=1, ascii_symbols=["PHASE"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.PhaseShift(target=target[0], angle=self.angle)

    def to_matrix(self):
        return np.array([[1.0, 0.0], [0.0, np.exp(1j * self.angle)]], dtype=complex)

    @staticmethod
    @circuit.subroutine(register=True)
    def phaseshift(target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: PhaseShift instruction.

        Examples:
            >>> circ = Circuit().phaseshift(0, 0.15)
        """
        return [Instruction(Gate.PhaseShift(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(PhaseShift)


# Two qubit gates #


class CNot(Gate):
    """Controlled NOT gate."""

    def __init__(self):
        super().__init__(qubit_count=2, ascii_symbols=["C", "X"])

    def to_ir(self, target: QubitSet):
        return ir.CNot(control=target[0], target=target[1])

    def to_matrix(self):
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def cnot(control: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index.
            target (Qubit or int): Target qubit index.

        Returns:
            Instruction: CNot instruction.

        Examples:
            >>> circ = Circuit().cnot(0, 1)
        """
        return Instruction(Gate.CNot(), target=[control, target])


Gate.register_gate(CNot)


class Swap(Gate):
    """Swap gate."""

    def __init__(self):
        super().__init__(qubit_count=2, ascii_symbols=["SWAP", "SWAP"])

    def to_ir(self, target: QubitSet):
        return ir.Swap(targets=[target[0], target[1]])

    def to_matrix(self):
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def swap(targets: QubitSet) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubit indices.

        Returns:
            Instruction: Swap instruction.

        Examples:
            >>> circ = Circuit().swap(0, 1)
        """
        return Instruction(Gate.Swap(), target=targets)


Gate.register_gate(Swap)


class ISwap(Gate):
    """ISwap gate."""

    def __init__(self):
        super().__init__(qubit_count=2, ascii_symbols=["ISWAP", "ISWAP"])

    def to_ir(self, target: QubitSet):
        return ir.ISwap(targets=[target[0], target[1]])

    def to_matrix(self):
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0j, 0.0],
                [0.0, 1.0j, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def iswap(targets: QubitSet) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubit indices.

        Returns:
            Instruction: ISwap instruction.

        Examples:
            >>> circ = Circuit().iswap(0, 1)
        """
        return Instruction(Gate.ISwap(), target=targets)


Gate.register_gate(ISwap)


class PSwap(AngledGate):
    """PSwap gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["PSWAP", "PSWAP"])

    def to_ir(self, target: QubitSet):
        return ir.PSwap(targets=[target[0], target[1]], angle=self.angle)

    def to_matrix(self):
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, np.exp(1j * self.angle), 0.0],
                [0.0, np.exp(1j * self.angle), 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def pswap(targets: QubitSet, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (Qubit or int): Target qubit indices.

        Returns:
            Instruction: PSwap instruction.

        Examples:
            >>> circ = Circuit().pswap(0, 1, 0.15)
        """
        return Instruction(Gate.PSwap(angle), target=targets)


Gate.register_gate(PSwap)


class CPhaseShift(AngledGate):
    """Controlled phase shift gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["C", "PHASE"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.CPhaseShift(control=target[0], target=target[1], angle=self.angle)

    def to_matrix(self):
        return np.diag([1.0, 1.0, 1.0, np.exp(1j * self.angle)])

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift(control: QubitInput, target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index.
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: CPhaseShift instruction.

        Examples:
            >>> circ = Circuit().cphaseshift(0, 1, 0.15)
        """
        return Instruction(Gate.CPhaseShift(angle), target=[control, target])


Gate.register_gate(CPhaseShift)


class CPhaseShift00(AngledGate):
    """Controlled phase shift gate for phasing the |00> state.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["C", "PHASE00"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.CPhaseShift00(control=target[0], target=target[1], angle=self.angle)

    def to_matrix(self):
        return np.diag([np.exp(1j * self.angle), 1.0, 1.0, 1.0])

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift00(control: QubitInput, target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index.
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: CPhaseShift00 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift00(0, 1, 0.15)
        """
        return Instruction(Gate.CPhaseShift00(angle), target=[control, target])


Gate.register_gate(CPhaseShift00)


class CPhaseShift01(AngledGate):
    """Controlled phase shift gate for phasing the |01> state.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["C", "PHASE01"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.CPhaseShift01(control=target[0], target=target[1], angle=self.angle)

    def to_matrix(self):
        return np.diag([1.0, np.exp(1j * self.angle), 1.0, 1.0])

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift01(control: QubitInput, target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index.
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: CPhaseShift01 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift01(0, 1, 0.15)
        """
        return Instruction(Gate.CPhaseShift01(angle), target=[control, target])


Gate.register_gate(CPhaseShift01)


class CPhaseShift10(AngledGate):
    """Controlled phase shift gate for phasing the |10> state.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["C", "PHASE10"])

    def to_ir(self, target: QubitSet) -> np.ndarray:
        return ir.CPhaseShift10(control=target[0], target=target[1], angle=self.angle)

    def to_matrix(self):
        return np.diag([1.0, 1.0, np.exp(1j * self.angle), 1.0])

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift10(control: QubitInput, target: QubitInput, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index.
            target (Qubit or int): Target qubit index.
            angle (float): Angle in radians.

        Returns:
            Instruction: CPhaseShift10 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift10(0, 1, 0.15)
        """
        return Instruction(Gate.CPhaseShift10(angle), target=[control, target])


Gate.register_gate(CPhaseShift10)


class CY(Gate):
    """Controlled Pauli-Y gate."""

    def __init__(self):
        super().__init__(qubit_count=2, ascii_symbols=["C", "Y"])

    def to_ir(self, target: QubitSet):
        return ir.CY(control=target[0], target=target[1])

    def to_matrix(self):
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, -1.0j],
                [0.0, 0.0, +1.0j, 0.0],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def cy(control: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index.
            target (Qubit or int): Target qubit index.

        Returns:
            Instruction: CY instruction.

        Examples:
            >>> circ = Circuit().cy(0, 1)
        """
        return Instruction(Gate.CY(), target=[control, target])


Gate.register_gate(CY)


class CZ(Gate):
    """Controlled Pauli-Z gate."""

    def __init__(self):
        super().__init__(qubit_count=2, ascii_symbols=["C", "Z"])

    def to_ir(self, target: QubitSet):
        return ir.CZ(control=target[0], target=target[1])

    def to_matrix(self):
        return np.diag([1.0, 1.0, 1.0, -1.0])

    @staticmethod
    @circuit.subroutine(register=True)
    def cz(control: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index.
            target (Qubit or int): Target qubit index.

        Returns:
            Instruction: CZ instruction.

        Examples:
            >>> circ = Circuit().cz(0, 1)
        """
        return Instruction(Gate.CZ(), target=[control, target])


Gate.register_gate(CZ)


class XX(AngledGate):
    """Ising XX coupling gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["XX", "XX"])

    def to_ir(self, target: QubitSet):
        return ir.XX(targets=[target[0], target[1]], angle=self.angle)

    def to_matrix(self):
        return (1 / math.sqrt(2)) * np.array(
            [
                [1.0, 0.0, 0.0, -1.0j * np.exp(1.0j * self.angle)],
                [0.0, 1.0, -1.0j, 0.0],
                [0.0, -1.0j, 1.0, 0.0],
                [-1.0j * np.exp(-1.0j * self.angle), 0.0, 0.0, 1.0],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def xx(targets: QubitSet, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (Qubit or int): Target qubit indices.
            angle (float): Angle in radians.

        Returns:
            Instruction: XX instruction.

        Examples:
            >>> circ = Circuit().xx(0, 1, 0.15)
        """
        return Instruction(Gate.XX(angle), target=targets)


Gate.register_gate(XX)


class YY(AngledGate):
    """Ising YY coupling gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["YY", "YY"])

    def to_ir(self, target: QubitSet):
        return ir.YY(targets=[target[0], target[1]], angle=self.angle)

    def to_matrix(self):
        cos = np.cos(self.angle)
        sin = np.sin(self.angle)
        return np.array(
            [
                [cos, 0.0, 0.0, 1.0j * sin],
                [0.0, cos, -1.0j * sin, 0.0],
                [0.0, -1.0j * sin, cos, 0.0],
                [1.0j * sin, 0.0, 0.0, cos],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def yy(targets: QubitSet, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (Qubit or int): Target qubit indices.
            angle (float): Angle in radians.

        Returns:
            Instruction: YY instruction.

        Examples:
            >>> circ = Circuit().yy(0, 1, 0.15)
        """
        return Instruction(Gate.YY(angle), target=targets)


Gate.register_gate(YY)


class ZZ(AngledGate):
    """Ising ZZ coupling gate.

    Args:
        angle (float): angle in radians.
    """

    def __init__(self, angle: float):
        super().__init__(angle=angle, qubit_count=2, ascii_symbols=["ZZ", "ZZ"])

    def to_ir(self, target: QubitSet):
        return ir.ZZ(targets=[target[0], target[1]], angle=self.angle)

    def to_matrix(self):
        return np.array(
            [
                [np.exp(1j * (self.angle / 2)), 0.0, 0.0, 0.0],
                [0.0, np.exp(-1j * (self.angle / 2)), 0.0, 0.0],
                [0.0, 0.0, np.exp(-1j * (self.angle / 2)), 0.0],
                [0.0, 0.0, 0.0, np.exp(1j * (self.angle / 2))],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def zz(targets: QubitSet, angle: float) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (Qubit or int): Target qubit indices.
            angle (float): Angle in radians.

        Returns:
            Instruction: ZZ instruction.

        Examples:
            >>> circ = Circuit().zz(0, 1, 0.15)
        """
        return Instruction(Gate.ZZ(angle), target=targets)


Gate.register_gate(ZZ)


# Three qubit gates #


class CCNot(Gate):
    """CCNOT gate or Toffoli gate."""

    def __init__(self):
        super().__init__(qubit_count=3, ascii_symbols=["C", "C", "X"])

    def to_ir(self, target: QubitSet):
        return ir.CCNot(controls=[target[0], target[1]], target=target[2])

    def to_matrix(self):
        return np.array(
            [
                [1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 1, 0],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def ccnot(controls: QubitSet, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            controls (QubitSet): Control qubit indices.
            target (Qubit or int): Target qubit index.

        Returns:
            Instruction: CCNot instruction.

        Examples:
            >>> circ = Circuit().ccnot(controls=[0, 1], target=2)
        """
        return Instruction(Gate.CCNot(), target=[controls[0], controls[1], target])


Gate.register_gate(CCNot)


class CSwap(Gate):
    """Controlled Swap gate."""

    def __init__(self):
        super().__init__(qubit_count=3, ascii_symbols=["C", "SWAP", "SWAP"])

    def to_ir(self, target: QubitSet):
        return ir.CSwap(control=target[0], targets=[target[1], target[2]])

    def to_matrix(self):
        return np.array(
            [
                [1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 1],
            ],
            dtype=complex,
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def cswap(control: QubitInput, targets: QubitSet) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (Qubit or int): Control qubit index
            targets (QubitSet): Target qubit indices.

        Returns:
            Instruction: CSwap instruction.

        Examples:
            >>> circ = Circuit().cswap(0, 1, 2)
        """
        return Instruction(Gate.CSwap(), target=[control, targets[0], targets[1]])


Gate.register_gate(CSwap)
