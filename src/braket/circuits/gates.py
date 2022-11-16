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

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, List, Union

import numpy as np
from oqpy import Program
from sympy import Float

import braket.ir.jaqcd as ir
from braket.circuits import circuit
from braket.circuits.angled_gate import AngledGate, DoubleAngledGate
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.parameterizable import Parameterizable
from braket.circuits.quantum_operator_helpers import (
    is_unitary,
    verify_quantum_operator_matrix_dimensions,
)
from braket.circuits.qubit import QubitInput
from braket.circuits.qubit_set import QubitSet, QubitSetInput
from braket.circuits.serialization import OpenQASMSerializationProperties
from braket.pulse.ast.qasm_parser import ast_to_qasm
from braket.pulse.pulse_sequence import PulseSequence

"""
To add a new gate:
    1. Implement the class and extend `Gate`
    2. Add a method with the `@circuit.subroutine(register=True)` decorator. Method name
       will be added into the `Circuit` class. This method is the default way
       clients add this gate to a circuit.
    3. Register the class with the `Gate` class via `Gate.register_gate()`.
"""


# Single qubit gates #


class H(Gate):
    """Hadamard gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["H"])

    def adjoint(self) -> List[Gate]:
        return [H()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.H.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"h {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return 1.0 / np.sqrt(2.0) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def h(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of H instructions.

        Examples:
            >>> circ = Circuit().h(0)
            >>> circ = Circuit().h([0, 1, 2])
        """
        return [Instruction(H(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(H)


class I(Gate):  # noqa: E742, E261
    """Identity gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["I"])

    def adjoint(self) -> List[Gate]:
        return [I()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.I.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"i {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.eye(2, dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def i(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of I instructions.

        Examples:
            >>> circ = Circuit().i(0)
            >>> circ = Circuit().i([0, 1, 2])
        """
        return [Instruction(I(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(I)


class X(Gate):
    """Pauli-X gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["X"])

    def adjoint(self) -> List[Gate]:
        return [X()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.X.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"x {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def x(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of X instructions.

        Examples:
            >>> circ = Circuit().x(0)
            >>> circ = Circuit().x([0, 1, 2])
        """
        return [Instruction(X(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(X)


class Y(Gate):
    """Pauli-Y gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Y"])

    def adjoint(self) -> List[Gate]:
        return [Y()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Y.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"y {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def y(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of Y instructions.

        Examples:
            >>> circ = Circuit().y(0)
            >>> circ = Circuit().y([0, 1, 2])
        """
        return [Instruction(Y(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Y)


class Z(Gate):
    """Pauli-Z gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Z"])

    def adjoint(self) -> List[Gate]:
        return [Z()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Z.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"z {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def z(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of Z instructions.

        Examples:
            >>> circ = Circuit().z(0)
            >>> circ = Circuit().z([0, 1, 2])
        """
        return [Instruction(Z(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Z)


class S(Gate):
    """S gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["S"])

    def adjoint(self) -> List[Gate]:
        return [Si()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.S.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"s {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def s(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of S instructions.

        Examples:
            >>> circ = Circuit().s(0)
            >>> circ = Circuit().s([0, 1, 2])
        """
        return [Instruction(S(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(S)


class Si(Gate):
    """Conjugate transpose of S gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Si"])

    def adjoint(self) -> List[Gate]:
        return [S()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Si.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"si {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[1, 0], [0, -1j]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def si(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: Iterable of Si instructions.

        Examples:
            >>> circ = Circuit().si(0)
            >>> circ = Circuit().si([0, 1, 2])
        """
        return [Instruction(Si(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Si)


class T(Gate):
    """T gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["T"])

    def adjoint(self) -> List[Gate]:
        return [Ti()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.T.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"t {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(1j * np.pi / 4)]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def t(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of T instructions.

        Examples:
            >>> circ = Circuit().t(0)
            >>> circ = Circuit().t([0, 1, 2])
        """
        return [Instruction(T(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(T)


class Ti(Gate):
    """Conjugate transpose of T gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Ti"])

    def adjoint(self) -> List[Gate]:
        return [T()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Ti.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"ti {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(-1j * np.pi / 4)]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def ti(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of Ti instructions.

        Examples:
            >>> circ = Circuit().ti(0)
            >>> circ = Circuit().ti([0, 1, 2])
        """
        return [Instruction(Ti(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Ti)


class V(Gate):
    """Square root of not gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["V"])

    def adjoint(self) -> List[Gate]:
        return [Vi()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.V.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"v {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def v(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of V instructions.

        Examples:
            >>> circ = Circuit().v(0)
            >>> circ = Circuit().v([0, 1, 2])
        """
        return [Instruction(V(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(V)


class Vi(Gate):
    """Conjugate transpose of square root of not gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Vi"])

    def adjoint(self) -> List[Gate]:
        return [V()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Vi.construct(target=target[0])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"vi {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array(([[0.5 - 0.5j, 0.5 + 0.5j], [0.5 + 0.5j, 0.5 - 0.5j]]), dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def vi(target: QubitSetInput) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput): Target qubit(s)

        Returns:
            Iterable[Instruction]: `Iterable` of Vi instructions.

        Examples:
            >>> circ = Circuit().vi(0)
            >>> circ = Circuit().vi([0, 1, 2])
        """
        return [Instruction(Vi(), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Vi)


# Single qubit gates with rotation #


class Rx(AngledGate):
    """X-axis rotation gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("Rx", angle)],
        )

    def _to_jaqcd(self, target: QubitSet, **kwargs) -> Any:
        return ir.Rx.construct(target=target[0], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"rx({self.angle}) {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        """Returns a matrix representation of this gate.
        Returns:
            ndarray: The matrix representation of this gate.
        """
        cos = np.cos(self.angle / 2)
        sin = np.sin(self.angle / 2)
        return np.array([[cos, -1j * sin], [-1j * sin, cos]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def rx(
        target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): Angle in radians.

        Returns:
            Iterable[Instruction]: Rx instruction.

        Examples:
            >>> circ = Circuit().rx(0, 0.15)
        """
        return [Instruction(Rx(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Rx)


class Ry(AngledGate):
    """Y-axis rotation gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("Ry", angle)],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Ry.construct(target=target[0], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"ry({self.angle}) {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        """Returns a matrix representation of this gate.
        Returns:
            ndarray: The matrix representation of this gate.
        """
        cos = np.cos(self.angle / 2)
        sin = np.sin(self.angle / 2)
        return np.array([[cos, -sin], [+sin, cos]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def ry(
        target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): Angle in radians.

        Returns:
            Iterable[Instruction]: Ry instruction.

        Examples:
            >>> circ = Circuit().ry(0, 0.15)
        """
        return [Instruction(Ry(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Ry)


class Rz(AngledGate):
    """Z-axis rotation gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("Rz", angle)],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Rz.construct(target=target[0], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"rz({self.angle}) {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array(
            [[np.exp(-1j * self.angle / 2), 0], [0, np.exp(1j * self.angle / 2)]], dtype=complex
        )

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def rz(
        target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Iterable[Instruction]: Rz instruction.

        Examples:
            >>> circ = Circuit().rz(0, 0.15)
        """
        return [Instruction(Rz(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(Rz)


class PhaseShift(AngledGate):
    """Phase shift gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("PHASE", angle)],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.PhaseShift.construct(target=target[0], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        # alternatively, "ctrl @ phase({self.angle}) {target_qubit};"
        return f"phaseshift({self.angle}) {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(1j * self.angle)]], dtype=complex)

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def phaseshift(
        target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Iterable[Instruction]: PhaseShift instruction.

        Examples:
            >>> circ = Circuit().phaseshift(0, 0.15)
        """
        return [Instruction(PhaseShift(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(PhaseShift)


# Two qubit gates #


class CNot(Gate):
    """Controlled NOT gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "X"])

    def adjoint(self) -> List[Gate]:
        return [CNot()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CNot.construct(control=target[0], target=target[1])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit = serialization_properties.format_target(int(target[0]))
        target_qubit = serialization_properties.format_target(int(target[1]))
        return f"cnot {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
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
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cnot(control: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.

        Returns:
            Instruction: CNot instruction.

        Examples:
            >>> circ = Circuit().cnot(0, 1)
        """
        return Instruction(CNot(), target=[control, target])


Gate.register_gate(CNot)


class Swap(Gate):
    """Swap gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["SWAP", "SWAP"])

    def adjoint(self) -> List[Gate]:
        return [Swap()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Swap.construct(targets=[target[0], target[1]])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_0 = serialization_properties.format_target(int(target[0]))
        target_qubit_1 = serialization_properties.format_target(int(target[1]))
        return f"swap {target_qubit_0}, {target_qubit_1};"

    def to_matrix(self) -> np.ndarray:
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
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def swap(target1: QubitInput, target2: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.

        Returns:
            Instruction: Swap instruction.

        Examples:
            >>> circ = Circuit().swap(0, 1)
        """
        return Instruction(Swap(), target=[target1, target2])


Gate.register_gate(Swap)


class ISwap(Gate):
    """ISwap gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["ISWAP", "ISWAP"])

    def adjoint(self) -> List[Gate]:
        return [self, self, self]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.ISwap.construct(targets=[target[0], target[1]])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_0 = serialization_properties.format_target(int(target[0]))
        target_qubit_1 = serialization_properties.format_target(int(target[1]))
        return f"iswap {target_qubit_0}, {target_qubit_1};"

    def to_matrix(self) -> np.ndarray:
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
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def iswap(target1: QubitInput, target2: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.

        Returns:
            Instruction: ISwap instruction.

        Examples:
            >>> circ = Circuit().iswap(0, 1)
        """
        return Instruction(ISwap(), target=[target1, target2])


Gate.register_gate(ISwap)


class PSwap(AngledGate):
    """PSwap gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("PSWAP", angle),
                angled_ascii_characters("PSWAP", angle),
            ],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.PSwap.construct(targets=[target[0], target[1]], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_0 = serialization_properties.format_target(int(target[0]))
        target_qubit_1 = serialization_properties.format_target(int(target[1]))
        return f"pswap({self.angle}) {target_qubit_0}, {target_qubit_1};"

    def to_matrix(self) -> np.ndarray:
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, np.exp(1j * self.angle), 0.0],
                [0.0, np.exp(1j * self.angle), 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=complex,
        )

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def pswap(
        target1: QubitInput, target2: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: PSwap instruction.

        Examples:
            >>> circ = Circuit().pswap(0, 1, 0.15)
        """
        return Instruction(PSwap(angle), target=[target1, target2])


Gate.register_gate(PSwap)


class XY(AngledGate):
    """XY gate.

    Reference: https://arxiv.org/abs/1912.04424v1

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("XY", angle),
                angled_ascii_characters("XY", angle),
            ],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.XY.construct(targets=[target[0], target[1]], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_1 = serialization_properties.format_target(int(target[0]))
        target_qubit_2 = serialization_properties.format_target(int(target[1]))
        return f"xy({self.angle}) {target_qubit_1}, {target_qubit_2};"

    def to_matrix(self) -> np.ndarray:
        """Returns a matrix representation of this gate.
        Returns:
            ndarray: The matrix representation of this gate.
        """
        cos = np.cos(self.angle / 2)
        sin = np.sin(self.angle / 2)
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, cos, 1.0j * sin, 0.0],
                [0.0, 1.0j * sin, cos, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=complex,
        )

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def xy(
        target1: QubitInput, target2: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: XY instruction.

        Examples:
            >>> circ = Circuit().xy(0, 1, 0.15)
        """
        return Instruction(XY(angle), target=[target1, target2])


Gate.register_gate(XY)


class CPhaseShift(AngledGate):
    """Controlled phase shift gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE", angle)],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift.construct(control=target[0], target=target[1], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit = serialization_properties.format_target(int(target[0]))
        target_qubit = serialization_properties.format_target(int(target[1]))
        return f"cphaseshift({self.angle}) {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.diag([1.0, 1.0, 1.0, np.exp(1j * self.angle)])

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift(
        control: QubitInput, target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: CPhaseShift instruction.

        Examples:
            >>> circ = Circuit().cphaseshift(0, 1, 0.15)
        """
        return Instruction(CPhaseShift(angle), target=[control, target])


Gate.register_gate(CPhaseShift)


class CPhaseShift00(AngledGate):
    """Controlled phase shift gate for phasing the \\|00> state.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE00", angle)],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift00.construct(control=target[0], target=target[1], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit = serialization_properties.format_target(int(target[0]))
        target_qubit = serialization_properties.format_target(int(target[1]))
        return f"cphaseshift00({self.angle}) {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.diag([np.exp(1j * self.angle), 1.0, 1.0, 1.0])

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift00(
        control: QubitInput, target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: CPhaseShift00 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift00(0, 1, 0.15)
        """
        return Instruction(CPhaseShift00(angle), target=[control, target])


Gate.register_gate(CPhaseShift00)


class CPhaseShift01(AngledGate):
    """Controlled phase shift gate for phasing the \\|01> state.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE01", angle)],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift01.construct(control=target[0], target=target[1], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit = serialization_properties.format_target(int(target[0]))
        target_qubit = serialization_properties.format_target(int(target[1]))
        return f"cphaseshift01({self.angle}) {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.diag([1.0, np.exp(1j * self.angle), 1.0, 1.0])

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift01(
        control: QubitInput, target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: CPhaseShift01 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift01(0, 1, 0.15)
        """
        return Instruction(CPhaseShift01(angle), target=[control, target])


Gate.register_gate(CPhaseShift01)


class CPhaseShift10(AngledGate):
    """Controlled phase shift gate for phasing the \\|10> state.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE10", angle)],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift10.construct(control=target[0], target=target[1], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit = serialization_properties.format_target(int(target[0]))
        target_qubit = serialization_properties.format_target(int(target[1]))
        return f"cphaseshift10({self.angle}) {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.diag([1.0, 1.0, np.exp(1j * self.angle), 1.0])

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cphaseshift10(
        control: QubitInput, target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: CPhaseShift10 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift10(0, 1, 0.15)
        """
        return Instruction(CPhaseShift10(angle), target=[control, target])


Gate.register_gate(CPhaseShift10)


class CV(Gate):
    """Controlled Sqrt of NOT gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "V"])

    def adjoint(self) -> List[Gate]:
        return [self, self, self]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CV.construct(control=target[0], target=target[1])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit = serialization_properties.format_target(int(target[0]))
        target_qubit = serialization_properties.format_target(int(target[1]))
        return f"cv {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.5 + 0.5j, 0.5 - 0.5j],  # if the control bit, then apply the V gate
                [0.0, 0.0, 0.5 - 0.5j, 0.5 + 0.5j],  # which is the sqrt(NOT) gate.
            ],
            dtype=complex,
        )

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cv(control: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.

        Returns:
            Instruction: CV instruction.

        Examples:
            >>> circ = Circuit().cv(0, 1)
        """
        return Instruction(CV(), target=[control, target])


Gate.register_gate(CV)


class CY(Gate):
    """Controlled Pauli-Y gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "Y"])

    def adjoint(self) -> List[Gate]:
        return [CY()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CY.construct(control=target[0], target=target[1])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[1]))
        control_qubit = serialization_properties.format_target(int(target[0]))
        return f"cy {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
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
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cy(control: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.

        Returns:
            Instruction: CY instruction.

        Examples:
            >>> circ = Circuit().cy(0, 1)
        """
        return Instruction(CY(), target=[control, target])


Gate.register_gate(CY)


class CZ(Gate):
    """Controlled Pauli-Z gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "Z"])

    def adjoint(self) -> List[Gate]:
        return [CZ()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CZ.construct(control=target[0], target=target[1])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[1]))
        control_qubit = serialization_properties.format_target(int(target[0]))
        return f"cz {control_qubit}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.diag([complex(1.0), 1.0, 1.0, -1.0])

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cz(control: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index.
            target (QubitInput): Target qubit index.

        Returns:
            Instruction: CZ instruction.

        Examples:
            >>> circ = Circuit().cz(0, 1)
        """
        return Instruction(CZ(), target=[control, target])


Gate.register_gate(CZ)


class ECR(Gate):
    """An echoed RZX(pi/2) gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["ECR", "ECR"])

    def adjoint(self) -> List[Gate]:
        return [ECR()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.ECR.construct(targets=[target[0], target[1]])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_0 = serialization_properties.format_target(int(target[0]))
        target_qubit_1 = serialization_properties.format_target(int(target[1]))
        return f"ecr {target_qubit_0}, {target_qubit_1};"

    def to_matrix(self) -> np.ndarray:
        return (
            1
            / np.sqrt(2)
            * np.array(
                [[0, 0, 1, 1.0j], [0, 0, 1.0j, 1], [1, -1.0j, 0, 0], [-1.0j, 1, 0, 0]],
                dtype=complex,
            )
        )

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def ecr(target1: QubitInput, target2: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.

        Returns:
            Instruction: ECR instruction.

        Examples:
            >>> circ = Circuit().ecr(0, 1)
        """
        return Instruction(ECR(), target=[target1, target2])


Gate.register_gate(ECR)


class XX(AngledGate):
    """Ising XX coupling gate.

    Reference: https://arxiv.org/abs/1707.06356

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("XX", angle),
                angled_ascii_characters("XX", angle),
            ],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.XX.construct(targets=[target[0], target[1]], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_1 = serialization_properties.format_target(int(target[0]))
        target_qubit_2 = serialization_properties.format_target(int(target[1]))
        return f"xx({self.angle}) {target_qubit_1}, {target_qubit_2};"

    def to_matrix(self) -> np.ndarray:
        """Returns a matrix representation of this gate.
        Returns:
            ndarray: The matrix representation of this gate.
        """
        cos = np.cos(self.angle / 2)
        isin = 1.0j * np.sin(self.angle / 2)
        return np.array(
            [
                [cos, 0.0, 0.0, -isin],
                [0.0, cos, -isin, 0.0],
                [0.0, -isin, cos, 0.0],
                [-isin, 0.0, 0.0, cos],
            ],
            dtype=complex,
        )

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def xx(
        target1: QubitInput, target2: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: XX instruction.

        Examples:
            >>> circ = Circuit().xx(0, 1, 0.15)
        """
        return Instruction(XX(angle), target=[target1, target2])


Gate.register_gate(XX)


class YY(AngledGate):
    """Ising YY coupling gate.

    Reference: https://arxiv.org/abs/1707.06356

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("YY", angle),
                angled_ascii_characters("YY", angle),
            ],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.YY.construct(targets=[target[0], target[1]], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_1 = serialization_properties.format_target(int(target[0]))
        target_qubit_2 = serialization_properties.format_target(int(target[1]))
        return f"yy({self.angle}) {target_qubit_1}, {target_qubit_2};"

    def to_matrix(self) -> np.ndarray:
        """Returns a matrix representation of this gate.
        Returns:
            ndarray: The matrix representation of this gate.
        """
        cos = np.cos(self.angle / 2)
        isin = 1.0j * np.sin(self.angle / 2)
        return np.array(
            [
                [cos, 0.0, 0.0, isin],
                [0.0, cos, -isin, 0.0],
                [0.0, -isin, cos, 0.0],
                [isin, 0.0, 0.0, cos],
            ],
            dtype=complex,
        )

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def yy(
        target1: QubitInput, target2: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: YY instruction.

        Examples:
            >>> circ = Circuit().yy(0, 1, 0.15)
        """
        return Instruction(YY(angle), target=[target1, target2])


Gate.register_gate(YY)


class ZZ(AngledGate):
    """Ising ZZ coupling gate.

    Reference: https://arxiv.org/abs/1707.06356

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("ZZ", angle),
                angled_ascii_characters("ZZ", angle),
            ],
        )

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.ZZ.construct(targets=[target[0], target[1]], angle=self.angle)

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_1 = serialization_properties.format_target(int(target[0]))
        target_qubit_2 = serialization_properties.format_target(int(target[1]))
        return f"zz({self.angle}) {target_qubit_1}, {target_qubit_2};"

    def to_matrix(self) -> np.ndarray:
        return np.array(
            [
                [np.exp(-1j * (self.angle / 2)), 0.0, 0.0, 0.0],
                [0.0, np.exp(1j * (self.angle / 2)), 0.0, 0.0],
                [0.0, 0.0, np.exp(1j * (self.angle / 2)), 0.0],
                [0.0, 0.0, 0.0, np.exp(-1j * (self.angle / 2))],
            ],
            dtype=complex,
        )

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def zz(
        target1: QubitInput, target2: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Instruction: ZZ instruction.

        Examples:
            >>> circ = Circuit().zz(0, 1, 0.15)
        """
        return Instruction(ZZ(angle), target=[target1, target2])


Gate.register_gate(ZZ)


# Three qubit gates #


class CCNot(Gate):
    """CCNOT gate or Toffoli gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "C", "X"])

    def adjoint(self) -> List[Gate]:
        return [CCNot()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CCNot.construct(controls=[target[0], target[1]], target=target[2])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit_0 = serialization_properties.format_target(int(target[0]))
        control_qubit_1 = serialization_properties.format_target(int(target[1]))
        target_qubit = serialization_properties.format_target(int(target[2]))
        return f"ccnot {control_qubit_0}, {control_qubit_1}, {target_qubit};"

    def to_matrix(self) -> np.ndarray:
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
    def fixed_qubit_count() -> int:
        return 3

    @staticmethod
    @circuit.subroutine(register=True)
    def ccnot(control1: QubitInput, control2: QubitInput, target: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control1 (QubitInput): Control qubit 1 index.
            control2 (QubitInput): Control qubit 2 index.
            target (QubitInput): Target qubit index.

        Returns:
            Instruction: CCNot instruction.

        Examples:
            >>> circ = Circuit().ccnot(0, 1, 2)
        """
        return Instruction(CCNot(), target=[control1, control2, target])


Gate.register_gate(CCNot)


class CSwap(Gate):
    """Controlled Swap gate."""

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "SWAP", "SWAP"])

    def adjoint(self) -> List[Gate]:
        return [CSwap()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CSwap.construct(control=target[0], targets=[target[1], target[2]])

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        control_qubit = serialization_properties.format_target(int(target[0]))
        target_qubit_0 = serialization_properties.format_target(int(target[1]))
        target_qubit_1 = serialization_properties.format_target(int(target[2]))

        return f"cswap {control_qubit}, {target_qubit_0}, {target_qubit_1};"

    def to_matrix(self) -> np.ndarray:
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
    def fixed_qubit_count() -> int:
        return 3

    @staticmethod
    @circuit.subroutine(register=True)
    def cswap(control: QubitInput, target1: QubitInput, target2: QubitInput) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            control (QubitInput): Control qubit index
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.

        Returns:
            Instruction: CSwap instruction.

        Examples:
            >>> circ = Circuit().cswap(0, 1, 2)
        """
        return Instruction(CSwap(), target=[control, target1, target2])


Gate.register_gate(CSwap)


class GPi(AngledGate):
    """IonQ GPi gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("GPi", angle)],
        )

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"gpi({self.angle}) {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array(
            [
                [0, np.exp(-1j * self.angle)],
                [np.exp(1j * self.angle), 0],
            ]
        )

    def adjoint(self) -> List[Gate]:
        return [GPi(self.angle)]

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> GPi:
        return get_angle(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def gpi(
        target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): Angle in radians.

        Returns:
            Iterable[Instruction]: GPi instruction.

        Examples:
            >>> circ = Circuit().gpi(0, 0.15)
        """
        return [Instruction(GPi(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(GPi)


class GPi2(AngledGate):
    """IonQ GPi2 gate.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: Union[FreeParameterExpression, float]):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("GPi2", angle)],
        )

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit = serialization_properties.format_target(int(target[0]))
        return f"gpi2({self.angle}) {target_qubit};"

    def to_matrix(self) -> np.ndarray:
        return np.array(
            [
                [1, -1j * np.exp(-1j * self.angle)],
                [-1j * np.exp(1j * self.angle), 1],
            ]
        ) / np.sqrt(2)

    def adjoint(self) -> List[Gate]:
        return [GPi2(self.angle + np.pi)]

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> GPi2:
        return get_angle(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def gpi2(
        target: QubitInput, angle: Union[FreeParameterExpression, float]
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): Angle in radians.

        Returns:
            Iterable[Instruction]: GPi2 instruction.

        Examples:
            >>> circ = Circuit().gpi2(0, 0.15)
        """
        return [Instruction(GPi2(angle), target=qubit) for qubit in QubitSet(target)]


Gate.register_gate(GPi2)


class MS(DoubleAngledGate):
    """IonQ Mølmer-Sørenson gate.

    Args:
        angle_1 (Union[FreeParameterExpression, float]): angle in radians.
        angle_2 (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(
        self,
        angle_1: Union[FreeParameterExpression, float],
        angle_2: Union[FreeParameterExpression, float],
    ):
        super().__init__(
            angle_1=angle_1,
            angle_2=angle_2,
            qubit_count=None,
            ascii_symbols=[_double_angled_ascii_characters("MS", angle_1, angle_2)] * 2,
        )

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        target_qubit_1 = serialization_properties.format_target(int(target[0]))
        target_qubit_2 = serialization_properties.format_target(int(target[1]))
        return f"ms({self.angle_1}, {self.angle_2}) {target_qubit_1}, {target_qubit_2};"

    def to_matrix(self) -> np.ndarray:
        return np.array(
            [
                [1, 0, 0, -1j * np.exp(-1j * (self.angle_1 + self.angle_2))],
                [0, 1, -1j * np.exp(-1j * (self.angle_1 - self.angle_2)), 0],
                [0, -1j * np.exp(1j * (self.angle_1 - self.angle_2)), 1, 0],
                [-1j * np.exp(1j * (self.angle_1 + self.angle_2)), 0, 0, 1],
            ]
        ) / np.sqrt(2)

    def adjoint(self) -> List[Gate]:
        return [MS(self.angle_1 + np.pi, self.angle_2)]

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    def bind_values(self, **kwargs) -> MS:
        return _get_angles(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def ms(
        target1: QubitInput,
        target2: QubitInput,
        angle_1: Union[FreeParameterExpression, float],
        angle_2: Union[FreeParameterExpression, float],
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle_1 (Union[FreeParameterExpression, float]): angle in radians.
            angle_2 (Union[FreeParameterExpression, float]): angle in radians.

        Returns:
            Iterable[Instruction]: MS instruction.

        Examples:
            >>> circ = Circuit().ms(0, 1, 0.15, 0.34)
        """
        return [Instruction(MS(angle_1, angle_2), target=[target1, target2])]


Gate.register_gate(MS)


class Unitary(Gate):
    """Arbitrary unitary gate

    Args:
        matrix (numpy.ndarray): Unitary matrix which defines the gate.
        display_name (str): Name to be used for an instance of this unitary gate
            for circuit diagrams. Defaults to `U`.

    Raises:
        ValueError: If `matrix` is not a two-dimensional square matrix,
            or has a dimension length that is not a positive power of 2,
            or is not unitary.
    """

    def __init__(self, matrix: np.ndarray, display_name: str = "U"):
        verify_quantum_operator_matrix_dimensions(matrix)
        self._matrix = np.array(matrix, dtype=complex)
        qubit_count = int(np.log2(self._matrix.shape[0]))

        if not is_unitary(self._matrix):
            raise ValueError(f"{self._matrix} is not unitary")

        super().__init__(qubit_count=qubit_count, ascii_symbols=[display_name] * qubit_count)

    def to_matrix(self) -> np.ndarray:
        return np.array(self._matrix)

    def adjoint(self) -> List[Gate]:
        return [Unitary(self._matrix.conj().T, display_name=f"({self.ascii_symbols})^†")]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Unitary.construct(
            targets=[qubit for qubit in target],
            matrix=Unitary._transform_matrix_to_ir(self._matrix),
        )

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        qubits = [serialization_properties.format_target(int(qubit)) for qubit in target]
        formatted_matrix = np.array2string(
            self._matrix,
            separator=", ",
            formatter={"all": lambda x: format_complex(x)},
            threshold=float("inf"),
        ).replace("\n", "")

        return f"#pragma braket unitary({formatted_matrix}) {', '.join(qubits)}"

    def __eq__(self, other):
        if isinstance(other, Unitary):
            return self.matrix_equivalence(other)
        return False

    @staticmethod
    def _transform_matrix_to_ir(matrix: np.ndarray) -> List:
        return [[[element.real, element.imag] for element in row] for row in matrix.tolist()]

    @staticmethod
    @circuit.subroutine(register=True)
    def unitary(targets: QubitSet, matrix: np.ndarray, display_name: str = "U") -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubits.
            matrix (numpy.ndarray): Unitary matrix which defines the gate. Matrix should be
                compatible with the supplied targets, with `2 ** len(targets) == matrix.shape[0]`.
            display_name (str): Name to be used for an instance of this unitary gate
                for circuit diagrams. Defaults to `U`.

        Returns:
            Instruction: Unitary instruction.

        Raises:
            ValueError: If `matrix` is not a two-dimensional square matrix,
                or has a dimension length that is not compatible with the `targets`,
                or is not unitary,

        Examples:
            >>> circ = Circuit().unitary(matrix=np.array([[0, 1],[1, 0]]), targets=[0])
        """
        if 2 ** len(targets) != matrix.shape[0]:
            raise ValueError("Dimensions of the supplied unitary are incompatible with the targets")

        return Instruction(Unitary(matrix, display_name), target=targets)


Gate.register_gate(Unitary)


class PulseGate(Gate, Parameterizable):
    """Arbitrary pulse gate which provides the ability to embed custom pulse sequences
       within circuits.

    Args:
        pulse_sequence (PulseSequence): PulseSequence to embed within the circuit.
        qubit_count (int): The number of qubits this pulse gate operates on.
        display_name (str): Name to be used for an instance of this pulse gate
            for circuit diagrams. Defaults to `PG`.
    """

    def __init__(self, pulse_sequence: PulseSequence, qubit_count: int, display_name: str = "PG"):
        if pulse_sequence._capture_v0_count > 0:
            raise ValueError(
                "The supplied pulse sequence contains capture instructions which "
                "can not be embedded in a PulseGate."
            )
        self._pulse_sequence = deepcopy(pulse_sequence)
        super().__init__(qubit_count=qubit_count, ascii_symbols=[display_name] * qubit_count)

    @property
    def pulse_sequence(self) -> PulseSequence:
        """PulseSequence: The underlying PulseSequence of this gate."""
        return self._pulse_sequence

    @property
    def parameters(self) -> List[FreeParameter]:
        """Returns the list of `FreeParameter`s associated with the gate."""
        return list(self._pulse_sequence.parameters)

    def bind_values(self, **kwargs) -> PulseGate:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Returns:
            PulseGate: A copy of this gate with the requested parameters bound.
        """
        new_pulse_sequence = self._pulse_sequence.make_bound_pulse_sequence(kwargs)
        return PulseGate(new_pulse_sequence, self.qubit_count, self.ascii_symbols[0])

    def to_matrix(self) -> np.ndarray:
        raise NotImplementedError("PulseGate does not support conversion to a matrix.")

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        new_program = Program(None)
        new_program += self._pulse_sequence._program
        # Suppress declaration of frame and waveform vars as they have already been declared
        for v in list(new_program.undeclared_vars.values()):
            new_program._mark_var_declared(v)
        return ast_to_qasm(new_program.to_ast(include_externs=False, encal=True))

    @staticmethod
    @circuit.subroutine(register=True)
    def pulse_gate(
        targets: QubitSet, pulse_sequence: PulseSequence, display_name: str = "PG"
    ) -> Instruction:
        """Arbitrary pulse gate which provides the ability to embed custom pulse sequences
           within circuits.

        Args:
            targets (QubitSet): Target qubits. Note: These are only for representational purposes.
                The actual targets are determined by the frames used in the pulse sequence.
            pulse_sequence (PulseSequence): PulseSequence to embed within the circuit.
            display_name (str): Name to be used for an instance of this pulse gate
                for circuit diagrams. Defaults to `PG`.

        Returns:
            Instruction: Pulse gate instruction.

        Examples:
            >>> pulse_seq = PulseSequence().set_frequency(frame, frequency)....
            >>> circ = Circuit().pulse_gate(pulse_sequence=pulse_seq, targets=[0])
        """
        return Instruction(
            PulseGate(pulse_sequence, len(QubitSet(targets)), display_name), target=targets
        )


Gate.register_gate(PulseGate)


def angled_ascii_characters(gate: str, angle: Union[FreeParameterExpression, float]) -> str:
    """
    Generates a formatted ascii representation of an angled gate.

    Args:
        gate (str): The name of the gate.
        angle (Union[FreeParameterExpression, float]): The angle for the gate.

    Returns:
        str: Returns the ascii representation for an angled gate.

    """
    return f'{gate}({angle:{".2f" if isinstance(angle, (float, Float)) else ""}})'


def _double_angled_ascii_characters(
    gate: str,
    angle_1: Union[FreeParameterExpression, float],
    angle_2: Union[FreeParameterExpression, float],
) -> str:
    """
    Generates a formatted ascii representation of an angled gate.

    Args:
        gate (str): The name of the gate.
        angle_1 (Union[FreeParameterExpression, float]): angle in radians.
        angle_2 (Union[FreeParameterExpression, float]): angle in radians.

    Returns:
        str: Returns the ascii representation for an angled gate.

    """
    return (
        f"{gate}("
        f'{angle_1:{".2f" if isinstance(angle_1, (float, Float)) else ""}}, '
        f'{angle_2:{".2f" if isinstance(angle_2, (float, Float)) else ""}})'
    )


def get_angle(gate: AngledGate, **kwargs) -> AngledGate:
    """
    Gets the angle with all values substituted in that are requested.

    Args:
        gate (AngledGate): The subclass of AngledGate for which the angle is being obtained.

    Returns:
        AngledGate: A new gate of the type of the AngledGate originally used with all
        angles updated.
    """
    new_angle = (
        gate.angle.subs(kwargs) if isinstance(gate.angle, FreeParameterExpression) else gate.angle
    )
    return type(gate)(angle=new_angle)


def _get_angles(gate: DoubleAngledGate, **kwargs) -> DoubleAngledGate:
    """
    Gets the angle with all values substituted in that are requested.

    Args:
        gate (DoubleAngledGate): The subclass of DoubleAngledGate for which the angle is being
            obtained.
        **kwargs: The named parameters that are being filled for a particular gate.

    Returns:
        DoubleAngledGate: A new gate of the type of the AngledGate originally used with all angles
        updated.
    """
    new_angles = [
        (
            getattr(gate, angle).subs(kwargs)
            if isinstance(getattr(gate, angle), FreeParameterExpression)
            else getattr(gate, angle)
        )
        for angle in ("angle_1", "angle_2")
    ]
    return type(gate)(angle_1=new_angles[0], angle_2=new_angles[1])


def format_complex(number: complex) -> str:
    """
    Format a complex number into <a> + <b>im to be consumed by the braket unitary pragma

    Args:
        number (complex): A complex number.

    Returns:
        str: The formatted string.
    """
    if number.real:
        if number.imag:
            imag_sign = "+" if number.imag > 0 else "-"
            return f"{number.real} {imag_sign} {abs(number.imag)}im"
        else:
            return f"{number.real}"
    else:
        if number.imag:
            return f"{number.imag}im"
        else:
            return "0"
