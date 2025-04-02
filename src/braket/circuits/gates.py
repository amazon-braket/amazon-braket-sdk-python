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

from collections.abc import Iterable
from copy import deepcopy
from typing import Any

import numpy as np
from oqpy import Program

import braket.ir.jaqcd as ir
from braket.circuits import circuit
from braket.circuits.angled_gate import (
    AngledGate,
    DoubleAngledGate,
    TripleAngledGate,
    _get_angles,
    _multi_angled_ascii_characters,
    angled_ascii_characters,
    get_angle,
)
from braket.circuits.basis_state import BasisState, BasisStateInput
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.parameterizable import Parameterizable
from braket.circuits.quantum_operator_helpers import (
    is_unitary,
    verify_quantum_operator_matrix_dimensions,
)
from braket.circuits.serialization import OpenQASMSerializationProperties
from braket.pulse.ast.qasm_parser import ast_to_qasm
from braket.pulse.pulse_sequence import PulseSequence
from braket.registers.qubit import QubitInput
from braket.registers.qubit_set import QubitSet, QubitSetInput

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
    r"""Hadamard gate.

    Unitary matrix:

        .. math:: \mathtt{H} = \frac{1}{\sqrt{2}} \begin{bmatrix}
                1 & 1 \\
                1 & -1 \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["H"])

    @property
    def _qasm_name(self) -> str:
        return "h"

    def adjoint(self) -> list[Gate]:
        return [H()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.H.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return 1.0 / np.sqrt(2.0) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def h(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Hadamard gate.

        Unitary matrix:

            .. math:: \mathtt{H} = \frac{1}{\sqrt{2}} \begin{bmatrix}
                    1 & 1 \\
                    1 & -1 \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of H instructions.

        Examples:
            >>> circ = Circuit().h(0)
            >>> circ = Circuit().h([0, 1, 2])
        """
        return [
            Instruction(
                H(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(H)


class I(Gate):  # noqa: E742
    r"""Identity gate.

    Unitary matrix:

        .. math:: \mathtt{I} = \begin{bmatrix}
                1 & 0 \\
                0 & 1 \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["I"])

    @property
    def _qasm_name(self) -> str:
        return "i"

    def adjoint(self) -> list[Gate]:
        return [I()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.I.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.eye(2, dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def i(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Identity gate.

        Unitary matrix:

            .. math:: \mathtt{I} = \begin{bmatrix}
                    1 & 0 \\
                    0 & 1 \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of I instructions.

        Examples:
            >>> circ = Circuit().i(0)
            >>> circ = Circuit().i([0, 1, 2])
        """
        return [
            Instruction(
                I(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(I)


class GPhase(AngledGate):
    r"""Global phase gate.

    Unitary matrix:

        .. math:: \mathtt{gphase}(\gamma) = e^{i \gamma} I_1 = \begin{bmatrix}
                    e^{i \gamma} \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.

    Raises:
        ValueError: If `angle` is not present
    """

    def __init__(self, angle: FreeParameterExpression | float):
        # Avoid parent constructor because _qubit_count must be zero
        self._qubit_count = self.fixed_qubit_count()
        self._ascii_symbols = []

        if angle is None:
            raise ValueError("angle must not be None")
        if isinstance(angle, FreeParameterExpression):
            self._parameters = [angle]
        else:
            self._parameters = [float(angle)]  # explicit casting in case angle is e.g. np.float32

    @property
    def _qasm_name(self) -> str:
        return "gphase"

    def adjoint(self) -> list[Gate]:
        return [GPhase(-self.angle)]

    def to_matrix(self) -> np.ndarray:
        return np.exp(1j * self.angle) * np.eye(1, dtype=complex)

    def bind_values(self, **kwargs) -> AngledGate:
        return get_angle(self, **kwargs)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 0

    @staticmethod
    @circuit.subroutine(register=True)
    def gphase(
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction | Iterable[Instruction]:
        r"""Global phase gate.

        If the gate is applied with control/negative control modifiers, it is translated in an
        equivalent gate using the following definition: `phaseshift(λ) = ctrl @ gphase(λ)`.
        The rightmost control qubit is used for the translation. If the polarity of the rightmost
        control modifier is negative, the following identity is used:
        `negctrl @ gphase(λ) q = x q; ctrl @ gphase(λ) q; x q`.

        Unitary matrix:

            .. math:: \mathtt{gphase}(\gamma) = e^{i \gamma} I_1 = \begin{bmatrix}
                        e^{i \gamma} \end{bmatrix}.

        Args:
            angle (Union[FreeParameterExpression, float]): Phase in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction | Iterable[Instruction]: GPhase instruction.

        Examples:
            >>> circ = Circuit().gphase(0.45)
        """
        if control is not None:
            control_qubits = QubitSet(control)

            control_state = (
                control_state if control_state is not None else (1,) * len(control_qubits)
            )
            control_basis_state = BasisState(control_state, len(control_qubits))

            phaseshift_target = control_qubits[-1]
            phaseshift_instruction = PhaseShift.phaseshift(
                phaseshift_target,
                angle,
                control=control_qubits[:-1],
                control_state=control_basis_state[:-1],
                power=power,
            )
            return (
                phaseshift_instruction
                if control_basis_state[-1]
                else [
                    X.x(phaseshift_target),
                    phaseshift_instruction,
                    X.x(phaseshift_target),
                ]
            )

        return Instruction(GPhase(angle), power=power)


Gate.register_gate(GPhase)


class X(Gate):
    r"""Pauli-X gate.

    Unitary matrix:

        .. math:: \mathtt{X} = \begin{bmatrix}
                0 & 1 \\
                1 & 0
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["X"])

    @property
    def _qasm_name(self) -> str:
        return "x"

    def adjoint(self) -> list[Gate]:
        return [X()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.X.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def x(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Pauli-X gate.

        Unitary matrix:

            .. math:: \mathtt{X} = \begin{bmatrix}
                    0 & 1 \\
                    1 & 0
                    \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of X instructions.

        Examples:
            >>> circ = Circuit().x(0)
            >>> circ = Circuit().x([0, 1, 2])
        """
        return [
            Instruction(
                X(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(X)


class Y(Gate):
    r"""Pauli-Y gate.

    Unitary matrix:

        .. math:: \mathtt{Y} = \begin{bmatrix}
                0 & -i \\
                i & 0
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Y"])

    @property
    def _qasm_name(self) -> str:
        return "y"

    def adjoint(self) -> list[Gate]:
        return [Y()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Y.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def y(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Pauli-Y gate.

        Unitary matrix:

            .. math:: \mathtt{Y} = \begin{bmatrix}
                    0 & -i \\
                    i & 0
                    \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of Y instructions.

        Examples:
            >>> circ = Circuit().y(0)
            >>> circ = Circuit().y([0, 1, 2])
        """
        return [
            Instruction(
                Y(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Y)


class Z(Gate):
    r"""Pauli-Z gate.

    Unitary matrix:

        .. math:: \mathtt{Z} = \begin{bmatrix}
                1 & 0 \\
                0 & -1
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Z"])

    @property
    def _qasm_name(self) -> str:
        return "z"

    def adjoint(self) -> list[Gate]:
        return [Z()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Z.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def z(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Pauli-Z gate.

        .. math:: \mathtt{Z} = \begin{bmatrix}
                1 & 0 \\
                0 & -1
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of Z instructions.

        Examples:
            >>> circ = Circuit().z(0)
            >>> circ = Circuit().z([0, 1, 2])
        """
        return [
            Instruction(
                Z(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Z)


class S(Gate):
    r"""S gate.

    Unitary matrix:

        .. math:: \mathtt{S} = \begin{bmatrix}
                1 & 0 \\
                0 & i
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["S"])

    @property
    def _qasm_name(self) -> str:
        return "s"

    def adjoint(self) -> list[Gate]:
        return [Si()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.S.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def s(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""S gate.

        .. math:: \mathtt{S} = \begin{bmatrix}
                1 & 0 \\
                0 & i
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of S instructions.

        Examples:
            >>> circ = Circuit().s(0)
            >>> circ = Circuit().s([0, 1, 2])
        """
        return [
            Instruction(
                S(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(S)


class Si(Gate):
    r"""Conjugate transpose of S gate.

    Unitary matrix:

        .. math:: \mathtt{S}^\dagger = \begin{bmatrix}
                1 & 0 \\
                0 & -i
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Si"])

    @property
    def _qasm_name(self) -> str:
        return "si"

    def adjoint(self) -> list[Gate]:
        return [S()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Si.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1, 0], [0, -1j]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def si(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Conjugate transpose of S gate.

        .. math:: \mathtt{S}^\dagger = \begin{bmatrix}
                1 & 0 \\
                0 & -i
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: Iterable of Si instructions.

        Examples:
            >>> circ = Circuit().si(0)
            >>> circ = Circuit().si([0, 1, 2])
        """
        return [
            Instruction(
                Si(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Si)


class T(Gate):
    r"""T gate.

    Unitary matrix:

        .. math:: \mathtt{T} = \begin{bmatrix}
                1 & 0 \\
                0 & e^{i \pi/4}
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["T"])

    @property
    def _qasm_name(self) -> str:
        return "t"

    def adjoint(self) -> list[Gate]:
        return [Ti()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.T.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(1j * np.pi / 4)]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def t(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""T gate.

        .. math:: \mathtt{T} = \begin{bmatrix}
                1 & 0 \\
                0 & e^{i \pi/4}
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of T instructions.

        Examples:
            >>> circ = Circuit().t(0)
            >>> circ = Circuit().t([0, 1, 2])
        """
        return [
            Instruction(
                T(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(T)


class Ti(Gate):
    r"""Conjugate transpose of T gate.

    Unitary matrix:

        .. math:: \mathtt{T}^\dagger = \begin{bmatrix}
                1 & 0 \\
                0 & e^{-i \pi/4}
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Ti"])

    @property
    def _qasm_name(self) -> str:
        return "ti"

    def adjoint(self) -> list[Gate]:
        return [T()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Ti.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(-1j * np.pi / 4)]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def ti(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Conjugate transpose of T gate.

        .. math:: \mathtt{T}^\dagger = \begin{bmatrix}
                1 & 0 \\
                0 & e^{-i \pi/4}
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of Ti instructions.

        Examples:
            >>> circ = Circuit().ti(0)
            >>> circ = Circuit().ti([0, 1, 2])
        """
        return [
            Instruction(
                Ti(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Ti)


class V(Gate):
    r"""Square root of X gate (V gate).

    Unitary matrix:

        .. math:: \mathtt{V} = \frac{1}{2}\begin{bmatrix}
                1+i & 1-i \\
                1-i & 1+i
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["V"])

    @property
    def _qasm_name(self) -> str:
        return "v"

    def adjoint(self) -> list[Gate]:
        return [Vi()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.V.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array([[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]], dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def v(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Square root of X gate (V gate).

        .. math:: \mathtt{V} = \frac{1}{2}\begin{bmatrix}
                1+i & 1-i \\
                1-i & 1+i
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of V instructions.

        Examples:
            >>> circ = Circuit().v(0)
            >>> circ = Circuit().v([0, 1, 2])
        """
        return [
            Instruction(
                V(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(V)


class Vi(Gate):
    r"""Conjugate transpose of square root of X gate (conjugate transpose of V).

    Unitary matrix:

        .. math:: \mathtt{V}^\dagger = \frac{1}{2}\begin{bmatrix}
                1-i & 1+i \\
                1+i & 1-i
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["Vi"])

    @property
    def _qasm_name(self) -> str:
        return "vi"

    def adjoint(self) -> list[Gate]:
        return [V()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Vi.construct(target=target[0])

    def to_matrix(self) -> np.ndarray:
        return np.array(([[0.5 - 0.5j, 0.5 + 0.5j], [0.5 + 0.5j, 0.5 - 0.5j]]), dtype=complex)

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    @staticmethod
    @circuit.subroutine(register=True)
    def vi(
        target: QubitSetInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Conjugate transpose of square root of X gate (conjugate transpose of V).

        .. math:: \mathtt{V}^\dagger = \frac{1}{2}\begin{bmatrix}
                1-i & 1+i \\
                1+i & 1-i
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: `Iterable` of Vi instructions.

        Examples:
            >>> circ = Circuit().vi(0)
            >>> circ = Circuit().vi([0, 1, 2])
        """
        return [
            Instruction(
                Vi(), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Vi)


# Single qubit gates with rotation #


class Rx(AngledGate):
    r"""X-axis rotation gate.

    Unitary matrix:

        .. math:: \mathtt{R_x}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & -i \sin{(\phi/2)} \\
                -i \sin{(\phi/2)} & \cos{(\phi/2)}
                \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("Rx", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "rx"

    def _to_jaqcd(self, target: QubitSet, **kwargs) -> Any:
        return ir.Rx.construct(target=target[0], angle=self.angle)

    def to_matrix(self) -> np.ndarray:
        r"""Returns a matrix representation of this gate.

        Returns:
            np.ndarray: The matrix representation of this gate.
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
        target: QubitSetInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""X-axis rotation gate.

        .. math:: \mathtt{R_x}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & -i \sin{(\phi/2)} \\
                -i \sin{(\phi/2)} & \cos{(\phi/2)}
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s).
            angle (Union[FreeParameterExpression, float]): Angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: Rx instruction.

        Examples:
            >>> circ = Circuit().rx(0, 0.15)
        """
        return [
            Instruction(
                Rx(angle), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Rx)


class Ry(AngledGate):
    r"""Y-axis rotation gate.

    Unitary matrix:

        .. math:: \mathtt{R_y}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & -\sin{(\phi/2)} \\
                \sin{(\phi/2)} & \cos{(\phi/2)}
                \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("Ry", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "ry"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Ry.construct(target=target[0], angle=self.angle)

    def to_matrix(self) -> np.ndarray:
        r"""Returns a matrix representation of this gate.

        Returns:
            np.ndarray: The matrix representation of this gate.
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
        target: QubitSetInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Y-axis rotation gate.

        .. math:: \mathtt{R_y}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & -\sin{(\phi/2)} \\
                \sin{(\phi/2)} & \cos{(\phi/2)}
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s).
            angle (Union[FreeParameterExpression, float]): Angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: Rx instruction.


        Examples:
            >>> circ = Circuit().ry(0, 0.15)
        """
        return [
            Instruction(
                Ry(angle), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Ry)


class Rz(AngledGate):
    r"""Z-axis rotation gate.

    Unitary matrix:

        .. math:: \mathtt{R_z}(\phi) = \begin{bmatrix}
                e^{-i \phi/2} & 0 \\
                0 & e^{i \phi/2}
                \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("Rz", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "rz"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Rz.construct(target=target[0], angle=self.angle)

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
        target: QubitSetInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Z-axis rotation gate.

        .. math:: \mathtt{R_z}(\phi) = \begin{bmatrix}
                e^{-i \phi/2} & 0 \\
                0 & e^{i \phi/2}
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s).
            angle (Union[FreeParameterExpression, float]): Angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: Rx instruction.

        Examples:
            >>> circ = Circuit().rz(0, 0.15)
        """
        return [
            Instruction(
                Rz(angle), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(Rz)


class PhaseShift(AngledGate):
    r"""Phase shift gate.

    Unitary matrix:

        .. math:: \mathtt{PhaseShift}(\phi) = \begin{bmatrix}
                1 & 0 \\
                0 & e^{i \phi}
                \end{bmatrix}

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("PHASE", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "phaseshift"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.PhaseShift.construct(target=target[0], angle=self.angle)

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
        target: QubitSetInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Phase shift gate.

        .. math:: \mathtt{PhaseShift}(\phi) = \begin{bmatrix}
                1 & 0 \\
                0 & e^{i \phi}
                \end{bmatrix}

        Args:
            target (QubitSetInput): Target qubit(s).
            angle (Union[FreeParameterExpression, float]): angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: PhaseShift instruction.

        Examples:
            >>> circ = Circuit().phaseshift(0, 0.15)
        """
        return [
            Instruction(
                PhaseShift(angle),
                target=qubit,
                control=control,
                control_state=control_state,
                power=power,
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(PhaseShift)


class U(TripleAngledGate):
    r"""Generalized single-qubit rotation gate.

    Unitary matrix:

        .. math:: \mathtt{U}(\theta, \phi, \lambda) = \begin{bmatrix}
                \cos{(\theta/2)} & -e^{i \lambda} \sin{(\theta/2)} \\
                e^{i \phi} \sin{(\theta/2)} & -e^{i (\phi + \lambda)} \cos{(\theta/2)}
                \end{bmatrix}.

    Args:
        angle_1 (Union[FreeParameterExpression, float]): theta angle in radians.
        angle_2 (Union[FreeParameterExpression, float]): phi angle in radians.
        angle_3 (Union[FreeParameterExpression, float]): lambda angle in radians.
    """

    def __init__(
        self,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        angle_3: FreeParameterExpression | float,
    ):
        super().__init__(
            angle_1=angle_1,
            angle_2=angle_2,
            angle_3=angle_3,
            qubit_count=None,
            ascii_symbols=[_multi_angled_ascii_characters("U", angle_1, angle_2, angle_3)],
        )

    @property
    def _qasm_name(self) -> str:
        return "U"

    def to_matrix(self) -> np.ndarray:
        r"""Returns a matrix representation of this gate.

        Returns:
            np.ndarray: The matrix representation of this gate.
        """
        theta_ = self.angle_1
        phi_ = self.angle_2
        lambda_ = self.angle_3
        return np.array([
            [
                np.cos(theta_ / 2),
                -np.exp(1j * lambda_) * np.sin(theta_ / 2),
            ],
            [
                np.exp(1j * phi_) * np.sin(theta_ / 2),
                np.exp(1j * (phi_ + lambda_)) * np.cos(theta_ / 2),
            ],
        ])

    def adjoint(self) -> list[Gate]:
        return [U(-self.angle_1, -self.angle_3, -self.angle_2)]

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> TripleAngledGate:
        return _get_angles(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def u(
        target: QubitSetInput,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        angle_3: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""Generalized single-qubit rotation gate.

        Unitary matrix:

            .. math:: \mathtt{U}(\theta, \phi, \lambda) = \begin{bmatrix}
                    \cos{(\theta/2)} & -e^{i \lambda} \sin{(\theta/2)} \\
                    e^{i \phi} \sin{(\theta/2)} & -e^{i (\phi + \lambda)} \cos{(\theta/2)}
                    \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s)
            angle_1 (Union[FreeParameterExpression, float]): theta angle in radians.
            angle_2 (Union[FreeParameterExpression, float]): phi angle in radians.
            angle_3 (Union[FreeParameterExpression, float]): lambda angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: U instruction.

        Examples:
            >>> circ = Circuit().u(0, 0.15, 0.34, 0.52)
        """
        return [
            Instruction(
                U(angle_1, angle_2, angle_3),
                target=qubit,
                control=control,
                control_state=control_state,
                power=power,
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(U)


# Two qubit gates #


class CNot(Gate):
    r"""Controlled NOT gate.

    Unitary matrix:

        .. math:: \mathtt{CNOT} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                0 & 0 & 1 & 0 \\
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "X"])

    @property
    def _qasm_name(self) -> str:
        return "cnot"

    def adjoint(self) -> list[Gate]:
        return [CNot()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CNot.construct(control=target[0], target=target[1])

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
    def cnot(control: QubitSetInput, target: QubitInput, power: float = 1) -> Instruction:
        r"""Controlled NOT gate.

        .. math:: \mathtt{CNOT} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                0 & 0 & 1 & 0 \\
                \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CNot instruction.

        Examples:
            >>> circ = Circuit().cnot(0, 1)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CNot(), target=[absorbed_control, target], control=control_qubits, power=power
        )


Gate.register_gate(CNot)


class Swap(Gate):
    r"""Swap gate.

    Unitary matrix:

        .. math:: \mathtt{SWAP} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["SWAP", "SWAP"])

    @property
    def _qasm_name(self) -> str:
        return "swap"

    def adjoint(self) -> list[Gate]:
        return [Swap()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Swap.construct(targets=[target[0], target[1]])

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
    def swap(
        target1: QubitInput,
        target2: QubitInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""Swap gate.

        .. math:: \mathtt{SWAP} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: Swap instruction.

        Examples:
            >>> circ = Circuit().swap(0, 1)
        """
        return Instruction(
            Swap(),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(Swap)


class ISwap(Gate):
    r"""ISwap gate.

    Unitary matrix:

        .. math:: \mathtt{iSWAP} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 0 & i & 0 \\
                0 & i & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["ISWAP", "ISWAP"])

    @property
    def _qasm_name(self) -> str:
        return "iswap"

    def adjoint(self) -> list[Gate]:
        return [self, self, self]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.ISwap.construct(targets=[target[0], target[1]])

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
    def iswap(
        target1: QubitInput,
        target2: QubitInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""ISwap gate.

        .. math:: \mathtt{iSWAP} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 0 & i & 0 \\
                0 & i & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: ISwap instruction.

        Examples:
            >>> circ = Circuit().iswap(0, 1)
        """
        return Instruction(
            ISwap(),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(ISwap)


class PSwap(AngledGate):
    r"""PSwap gate.

    Unitary matrix:

        .. math:: \mathtt{PSWAP}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 0 & e^{i \phi} & 0 \\
                0 & e^{i \phi} & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("PSWAP", angle),
                angled_ascii_characters("PSWAP", angle),
            ],
        )

    @property
    def _qasm_name(self) -> str:
        return "pswap"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.PSwap.construct(targets=[target[0], target[1]], angle=self.angle)

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
        target1: QubitInput,
        target2: QubitInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""PSwap gate.

        .. math:: \mathtt{PSWAP}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 0 & e^{i \phi} & 0 \\
                0 & e^{i \phi} & 0 & 0 \\
                0 & 0 & 0 & 1 \\
                \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: PSwap instruction.

        Examples:
            >>> circ = Circuit().pswap(0, 1, 0.15)
        """
        return Instruction(
            PSwap(angle),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(PSwap)


class XY(AngledGate):
    r"""XY gate.

    Unitary matrix:

        .. math:: \mathtt{XY}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & \cos{(\phi/2)} & i\sin{(\phi/2)} & 0 \\
                0 & i\sin{(\phi/2)} & \cos{(\phi/2)} & 0 \\
                0 & 0 & 0 & 1 \\
            \end{bmatrix}.

    Reference: https://arxiv.org/abs/1912.04424v1


    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("XY", angle),
                angled_ascii_characters("XY", angle),
            ],
        )

    @property
    def _qasm_name(self) -> str:
        return "xy"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.XY.construct(targets=[target[0], target[1]], angle=self.angle)

    def to_matrix(self) -> np.ndarray:
        r"""Returns a matrix representation of this gate.

        Returns:
            np.ndarray: The matrix representation of this gate.
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
        target1: QubitInput,
        target2: QubitInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""XY gate.

        .. math:: \mathtt{XY}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & \cos{(\phi/2)} & i\sin{(\phi/2)} & 0 \\
                0 & i\sin{(\phi/2)} & \cos{(\phi/2)} & 0 \\
                0 & 0 & 0 & 1 \\
            \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: XY instruction.

        Examples:
            >>> circ = Circuit().xy(0, 1, 0.15)
        """
        return Instruction(
            XY(angle),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(XY)


class CPhaseShift(AngledGate):
    r"""Controlled phase shift gate.

    Unitary matrix:

        .. math:: \mathtt{CPhaseShift}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & e^{i \phi}
            \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "cphaseshift"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift.construct(control=target[0], target=target[1], angle=self.angle)

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
        control: QubitSetInput,
        target: QubitInput,
        angle: FreeParameterExpression | float,
        power: float = 1,
    ) -> Instruction:
        r"""Controlled phase shift gate.

        .. math:: \mathtt{CPhaseShift}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & e^{i \phi}
            \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CPhaseShift instruction.

        Examples:
            >>> circ = Circuit().cphaseshift(0, 1, 0.15)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CPhaseShift(angle),
            target=[absorbed_control, target],
            control=control_qubits,
            power=power,
        )


Gate.register_gate(CPhaseShift)


class CPhaseShift00(AngledGate):
    r"""Controlled phase shift gate for phasing the \|00> state.

    Unitary matrix:

        .. math:: \mathtt{CPhaseShift00}(\phi) = \begin{bmatrix}
                e^{i \phi} & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & 1
                \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE00", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "cphaseshift00"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift00.construct(control=target[0], target=target[1], angle=self.angle)

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
        control: QubitSetInput,
        target: QubitInput,
        angle: FreeParameterExpression | float,
        power: float = 1,
    ) -> Instruction:
        r"""Controlled phase shift gate for phasing the \|00> state.

        .. math:: \mathtt{CPhaseShift00}(\phi) = \begin{bmatrix}
                e^{i \phi} & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & 1
                \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CPhaseShift00 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift00(0, 1, 0.15)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CPhaseShift00(angle),
            target=[absorbed_control, target],
            control=control_qubits,
            power=power,
        )


Gate.register_gate(CPhaseShift00)


class CPhaseShift01(AngledGate):
    r"""Controlled phase shift gate for phasing the \|01> state.

    Unitary matrix:

        .. math:: \mathtt{CPhaseShift01}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & e^{i \phi} & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & 1
            \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE01", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "cphaseshift01"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift01.construct(control=target[0], target=target[1], angle=self.angle)

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
        control: QubitSetInput,
        target: QubitInput,
        angle: FreeParameterExpression | float,
        power: float = 1,
    ) -> Instruction:
        r"""Controlled phase shift gate for phasing the \|01> state.

        .. math:: \mathtt{CPhaseShift01}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & e^{i \phi} & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & 1
            \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CPhaseShift01 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift01(0, 1, 0.15)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CPhaseShift01(angle),
            target=[absorbed_control, target],
            control=control_qubits,
            power=power,
        )


Gate.register_gate(CPhaseShift01)


class CPhaseShift10(AngledGate):
    r"""Controlled phase shift gate for phasing the \\|10> state.

    Unitary matrix:

        .. math:: \mathtt{CPhaseShift10}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & e^{i \phi} & 0 \\
                0 & 0 & 0 & 1
                \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=["C", angled_ascii_characters("PHASE10", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "cphaseshift10"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CPhaseShift10.construct(control=target[0], target=target[1], angle=self.angle)

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
        control: QubitSetInput,
        target: QubitInput,
        angle: FreeParameterExpression | float,
        power: float = 1,
    ) -> Instruction:
        r"""Controlled phase shift gate for phasing the \\|10> state.

        .. math:: \mathtt{CPhaseShift10}(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & e^{i \phi} & 0 \\
                0 & 0 & 0 & 1
                \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CPhaseShift10 instruction.

        Examples:
            >>> circ = Circuit().cphaseshift10(0, 1, 0.15)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CPhaseShift10(angle),
            target=[absorbed_control, target],
            control=control_qubits,
            power=power,
        )


Gate.register_gate(CPhaseShift10)


class CV(Gate):
    r"""Controlled Sqrt of X gate.

    Unitary matrix:

        .. math:: \mathtt{CV} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0.5+0.5i & 0.5-0.5i \\
                0 & 0 & 0.5-0.5i & 0.5+0.5i
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "V"])

    @property
    def _qasm_name(self) -> str:
        return "cv"

    def adjoint(self) -> list[Gate]:
        return [self, self, self]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CV.construct(control=target[0], target=target[1])

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
    def cv(control: QubitSetInput, target: QubitInput, power: float = 1) -> Instruction:
        r"""Controlled Sqrt of X gate.

        .. math:: \mathtt{CV} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0.5+0.5i & 0.5-0.5i \\
                0 & 0 & 0.5-0.5i & 0.5+0.5i
                \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CV instruction.

        Examples:
            >>> circ = Circuit().cv(0, 1)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CV(), target=[absorbed_control, target], control=control_qubits, power=power
        )


Gate.register_gate(CV)


class CY(Gate):
    r"""Controlled Pauli-Y gate.

    Unitary matrix:

        .. math:: \mathtt{CY} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0 & -i \\
                0 & 0 & i & 0
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "Y"])

    @property
    def _qasm_name(self) -> str:
        return "cy"

    def adjoint(self) -> list[Gate]:
        return [CY()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CY.construct(control=target[0], target=target[1])

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
    def cy(control: QubitSetInput, target: QubitInput, power: float = 1) -> Instruction:
        r"""Controlled Pauli-Y gate.

        .. math:: \mathtt{CY} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 0 & -i \\
                0 & 0 & i & 0
                \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CY instruction.

        Examples:
            >>> circ = Circuit().cy(0, 1)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CY(), target=[absorbed_control, target], control=control_qubits, power=power
        )


Gate.register_gate(CY)


class CZ(Gate):
    r"""Controlled Pauli-Z gate.

    Unitary matrix:

        .. math:: \mathtt{CZ} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & -1
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "Z"])

    @property
    def _qasm_name(self) -> str:
        return "cz"

    def adjoint(self) -> list[Gate]:
        return [CZ()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CZ.construct(control=target[0], target=target[1])

    def to_matrix(self) -> np.ndarray:
        return np.diag([complex(1.0), 1.0, 1.0, -1.0])

    @staticmethod
    def fixed_qubit_count() -> int:
        return 2

    @staticmethod
    @circuit.subroutine(register=True)
    def cz(control: QubitSetInput, target: QubitInput, power: float = 1) -> Instruction:
        r"""Controlled Pauli-Z gate.

        .. math:: \mathtt{CZ} = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & -1
                \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target (QubitInput): Target qubit index.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CZ instruction.

        Examples:
            >>> circ = Circuit().cz(0, 1)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CZ(), target=[absorbed_control, target], control=control_qubits, power=power
        )


Gate.register_gate(CZ)


class ECR(Gate):
    r"""An echoed RZX(pi/2) gate (ECR gate).

    Unitary matrix:

        .. math:: \mathtt{ECR} = \begin{bmatrix}
                0 & 0 & 1 & i \\
                0 & 0 & i & 1 \\
                1 & -i & 0 & 0 \\
                -i & 1 & 0 & 0
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["ECR", "ECR"])

    @property
    def _qasm_name(self) -> str:
        return "ecr"

    def adjoint(self) -> list[Gate]:
        return [ECR()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.ECR.construct(targets=[target[0], target[1]])

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
    def ecr(
        target1: QubitInput,
        target2: QubitInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""An echoed RZX(pi/2) gate (ECR gate).

        .. math:: \mathtt{ECR} = \begin{bmatrix}
                0 & 0 & 1 & i \\
                0 & 0 & i & 1 \\
                1 & -i & 0 & 0 \\
                -i & 1 & 0 & 0
                \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: ECR instruction.

        Examples:
            >>> circ = Circuit().ecr(0, 1)
        """
        return Instruction(
            ECR(),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(ECR)


class XX(AngledGate):
    r"""Ising XX coupling gate.

    Unitary matrix:

        .. math:: \mathtt{XX}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & 0 & 0 & -i \sin{(\phi/2)} \\
                0 & \cos{(\phi/2)} & -i \sin{(\phi/2)} & 0 \\
                0 & -i \sin{(\phi/2)} & \cos{(\phi/2)} & 0 \\
                -i \sin{(\phi/2)} & 0 & 0 & \cos{(\phi/2)}
                \end{bmatrix}.

    Reference: https://arxiv.org/abs/1707.06356

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("XX", angle),
                angled_ascii_characters("XX", angle),
            ],
        )

    @property
    def _qasm_name(self) -> str:
        return "xx"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.XX.construct(targets=[target[0], target[1]], angle=self.angle)

    def to_matrix(self) -> np.ndarray:
        r"""Returns a matrix representation of this gate.

        Returns:
            np.ndarray: The matrix representation of this gate.
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
        target1: QubitInput,
        target2: QubitInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""Ising XX coupling gate.

        .. math:: \mathtt{XX}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & 0 & 0 & -i \sin{(\phi/2)} \\
                0 & \cos{(\phi/2)} & -i \sin{(\phi/2)} & 0 \\
                0 & -i \sin{(\phi/2)} & \cos{(\phi/2)} & 0 \\
                -i \sin{(\phi/2)} & 0 & 0 & \cos{(\phi/2)}
                \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: XX instruction.

        Examples:
            >>> circ = Circuit().xx(0, 1, 0.15)
        """
        return Instruction(
            XX(angle),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(XX)


class YY(AngledGate):
    r"""Ising YY coupling gate.

    Unitary matrix:

        .. math:: \mathtt{YY}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & 0 & 0 & i \sin{(\phi/2)} \\
                0 & \cos{(\phi/2)} & -i \sin{(\phi/2)} & 0 \\
                0 & -i \sin{(\phi/2)} & \cos{(\phi/2)} & 0 \\
                i \sin{(\phi/2)} & 0 & 0 & \cos{(\phi/2)}
                \end{bmatrix}.

    Reference: https://arxiv.org/abs/1707.06356

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("YY", angle),
                angled_ascii_characters("YY", angle),
            ],
        )

    @property
    def _qasm_name(self) -> str:
        return "yy"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.YY.construct(targets=[target[0], target[1]], angle=self.angle)

    def to_matrix(self) -> np.ndarray:
        r"""Returns a matrix representation of this gate.

        Returns:
            np.ndarray: The matrix representation of this gate.
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
        target1: QubitInput,
        target2: QubitInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""Ising YY coupling gate.

        .. math:: \mathtt{YY}(\phi) = \begin{bmatrix}
                \cos{(\phi/2)} & 0 & 0 & i \sin{(\phi/2)} \\
                0 & \cos{(\phi/2)} & -i \sin{(\phi/2)} & 0 \\
                0 & -i \sin{(\phi/2)} & \cos{(\phi/2)} & 0 \\
                i \sin{(\phi/2)} & 0 & 0 & \cos{(\phi/2)}
                \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: YY instruction.

        Examples:
            >>> circ = Circuit().yy(0, 1, 0.15)
        """
        return Instruction(
            YY(angle),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(YY)


class ZZ(AngledGate):
    r"""Ising ZZ coupling gate.

    Unitary matrix:

        .. math:: \mathtt{ZZ}(\phi) = \begin{bmatrix}
                e^{-i\phi/2} & 0 & 0 & 0 \\
                0 & e^{i\phi/2} & 0 & 0 \\
                0 & 0 & e^{i\phi/2} & 0 \\
                0 & 0 & 0 & e^{-i\phi/2}
            \end{bmatrix}.

    Reference: https://arxiv.org/abs/1707.06356

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[
                angled_ascii_characters("ZZ", angle),
                angled_ascii_characters("ZZ", angle),
            ],
        )

    @property
    def _qasm_name(self) -> str:
        return "zz"

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.ZZ.construct(targets=[target[0], target[1]], angle=self.angle)

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
        target1: QubitInput,
        target2: QubitInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""Ising ZZ coupling gate.

        .. math:: \mathtt{ZZ}(\phi) = \begin{bmatrix}
                e^{-i\phi/2} & 0 & 0 & 0 \\
                0 & e^{i\phi/2} & 0 & 0 \\
                0 & 0 & e^{i\phi/2} & 0 \\
                0 & 0 & 0 & e^{-i\phi/2}
            \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle (Union[FreeParameterExpression, float]): angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: ZZ instruction.

        Examples:
            >>> circ = Circuit().zz(0, 1, 0.15)
        """
        return Instruction(
            ZZ(angle),
            target=[target1, target2],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(ZZ)


# Three qubit gates #


class CCNot(Gate):
    r"""CCNOT gate or Toffoli gate.

    Unitary matrix:

        .. math:: \mathtt{CCNOT} = \begin{bmatrix}
                1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 & 0 & 0 & 0 & 0  \\
                0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\
                0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 \\
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "C", "X"])

    @property
    def _qasm_name(self) -> str:
        return "ccnot"

    def adjoint(self) -> list[Gate]:
        return [CCNot()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CCNot.construct(controls=[target[0], target[1]], target=target[2])

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
    def ccnot(
        control1: QubitInput,
        control2: QubitInput,
        target: QubitInput,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""CCNOT gate or Toffoli gate.

        .. math:: \mathtt{CCNOT} = \begin{bmatrix}
                1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 & 0 & 0 & 0 & 0  \\
                0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\
                0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 \\
                \end{bmatrix}.

        Args:
            control1 (QubitInput): Control qubit 1 index.
            control2 (QubitInput): Control qubit 2 index.
            target (QubitInput): Target qubit index.
            control (Optional[QubitSetInput]): Control qubit(s), in addition to
                control1 and control2. Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Control state only applies to control qubits specified with
                the control argument, not control1 and control2. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CCNot instruction.

        Examples:
            >>> circ = Circuit().ccnot(0, 1, 2)
        """
        return Instruction(
            CCNot(),
            target=[control1, control2, target],
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(CCNot)


class CSwap(Gate):
    r"""Controlled Swap gate.

    Unitary matrix:

        .. math:: \mathtt{CSWAP} = \begin{bmatrix}
                1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 & 0 & 0 & 0 & 0  \\
                0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 \\
                0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\
                \end{bmatrix}.
    """

    def __init__(self):
        super().__init__(qubit_count=None, ascii_symbols=["C", "SWAP", "SWAP"])

    @property
    def _qasm_name(self) -> str:
        return "cswap"

    def adjoint(self) -> list[Gate]:
        return [CSwap()]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.CSwap.construct(control=target[0], targets=[target[1], target[2]])

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
    def cswap(
        control: QubitSetInput,
        target1: QubitInput,
        target2: QubitInput,
        power: float = 1,
    ) -> Instruction:
        r"""Controlled Swap gate.

        .. math:: \mathtt{CSWAP} = \begin{bmatrix}
                1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 & 0 & 0 & 0 & 0  \\
                0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 \\
                0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\
                \end{bmatrix}.

        Args:
            control (QubitSetInput): Control qubit(s). The last control qubit
                is absorbed into the target of the instruction.
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: CSwap instruction.

        Examples:
            >>> circ = Circuit().cswap(0, 1, 2)
        """
        control_qubits = QubitSet(control)
        absorbed_control = control_qubits.pop()
        return Instruction(
            CSwap(),
            target=[absorbed_control, target1, target2],
            control=control_qubits,
            power=power,
        )


Gate.register_gate(CSwap)


class GPi(AngledGate):
    r"""IonQ GPi gate.

    Unitary matrix:

        .. math:: \mathtt{GPi}(\phi) = \begin{bmatrix}
                0 & e^{-i \phi} \\
                e^{i \phi} & 0
                \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("GPi", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "gpi"

    def to_matrix(self) -> np.ndarray:
        return np.array([
            [0, np.exp(-1j * self.angle)],
            [np.exp(1j * self.angle), 0],
        ])

    def adjoint(self) -> list[Gate]:
        return [GPi(self.angle)]

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> GPi:
        return get_angle(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def gpi(
        target: QubitSetInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""IonQ GPi gate.

        .. math:: \mathtt{GPi}(\phi) = \begin{bmatrix}
                0 & e^{-i \phi} \\
                e^{i \phi} & 0
                \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s).
            angle (Union[FreeParameterExpression, float]): Angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: GPi instruction.

        Examples:
            >>> circ = Circuit().gpi(0, 0.15)
        """
        return [
            Instruction(
                GPi(angle), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(GPi)


class PRx(DoubleAngledGate):
    r"""Phase Rx gate.

    Unitary matrix:

        .. math:: \mathtt{PRx}(\theta,\phi) = \begin{bmatrix}
                \cos{(\theta / 2)} & -i e^{-i \phi} \sin{(\theta / 2)} \\
                -i e^{i \phi} \sin{(\theta / 2)} & \cos{(\theta / 2)}
            \end{bmatrix}.

    Args:
        angle_1 (Union[FreeParameterExpression, float]): The first angle of the gate in
            radians or expression representation.
        angle_2 (Union[FreeParameterExpression, float]): The second angle of the gate in
            radians or expression representation.
    """

    def __init__(
        self,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
    ):
        super().__init__(
            angle_1=angle_1,
            angle_2=angle_2,
            qubit_count=None,
            ascii_symbols=[_multi_angled_ascii_characters("PRx", angle_1, angle_2)],
        )

    @property
    def _qasm_name(self) -> str:
        return "prx"

    def to_matrix(self) -> np.ndarray:
        """Returns a matrix representation of this gate.

        Returns:
            np.ndarray: The matrix representation of this gate.
        """
        theta = self.angle_1
        phi = self.angle_2
        return np.array([
            [
                np.cos(theta / 2),
                -1j * np.exp(-1j * phi) * np.sin(theta / 2),
            ],
            [
                -1j * np.exp(1j * phi) * np.sin(theta / 2),
                np.cos(theta / 2),
            ],
        ])

    def adjoint(self) -> list[Gate]:
        return [PRx(-self.angle_1, self.angle_2)]

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> PRx:
        return _get_angles(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def prx(
        target: QubitSetInput,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""PhaseRx gate.

        .. math:: \mathtt{PRx}(\theta,\phi) = \begin{bmatrix}
                \cos{(\theta / 2)} & -i e^{-i \phi} \sin{(\theta / 2)} \\
                -i e^{i \phi} \sin{(\theta / 2)} & \cos{(\theta / 2)}
            \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s).
            angle_1 (Union[FreeParameterExpression, float]): First angle in radians.
            angle_2 (Union[FreeParameterExpression, float]): Second angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: PhaseRx instruction.

        Examples:
            >>> circ = Circuit().prx(0, 0.15, 0.25)
        """
        return [
            Instruction(
                PRx(angle_1, angle_2),
                target=qubit,
                control=control,
                control_state=control_state,
                power=power,
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(PRx)


class GPi2(AngledGate):
    r"""IonQ GPi2 gate.

    Unitary matrix:

        .. math:: \mathtt{GPi2}(\phi) = \frac{1}{\sqrt{2}} \begin{bmatrix}
                1 & -i e^{-i \phi} \\
                -i e^{i \phi} & 1
            \end{bmatrix}.

    Args:
        angle (Union[FreeParameterExpression, float]): angle in radians.
    """

    def __init__(self, angle: FreeParameterExpression | float):
        super().__init__(
            angle=angle,
            qubit_count=None,
            ascii_symbols=[angled_ascii_characters("GPi2", angle)],
        )

    @property
    def _qasm_name(self) -> str:
        return "gpi2"

    def to_matrix(self) -> np.ndarray:
        return np.array([
            [1, -1j * np.exp(-1j * self.angle)],
            [-1j * np.exp(1j * self.angle), 1],
        ]) / np.sqrt(2)

    def adjoint(self) -> list[Gate]:
        return [GPi2(self.angle + np.pi)]

    @staticmethod
    def fixed_qubit_count() -> int:
        return 1

    def bind_values(self, **kwargs) -> GPi2:
        return get_angle(self, **kwargs)

    @staticmethod
    @circuit.subroutine(register=True)
    def gpi2(
        target: QubitSetInput,
        angle: FreeParameterExpression | float,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""IonQ GPi2 gate.

        .. math:: \mathtt{GPi2}(\phi) = \frac{1}{\sqrt{2}}  \begin{bmatrix}
                1 & -i e^{-i \phi} \\
                -i e^{i \phi} & 1
            \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s).
            angle (Union[FreeParameterExpression, float]): Angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: GPi2 instruction.

        Examples:
            >>> circ = Circuit().gpi2(0, 0.15)
        """
        return [
            Instruction(
                GPi2(angle), target=qubit, control=control, control_state=control_state, power=power
            )
            for qubit in QubitSet(target)
        ]


Gate.register_gate(GPi2)


class MS(TripleAngledGate):
    r"""IonQ Mølmer-Sørensen gate.

    Unitary matrix:

            .. math:: &\mathtt{MS}(\phi_0, \phi_1, \theta) =\\ &\begin{bmatrix}
                    \cos{\frac{\theta}{2}} & 0 &
                    0 & -ie^{-i (\phi_0 + \phi_1)}\sin{\frac{\theta}{2}} \\
                    0 & \cos{\frac{\theta}{2}} &
                    -ie^{-i (\phi_0 - \phi_1)}\sin{\frac{\theta}{2}} & 0 \\
                    0 & -ie^{i (\phi_0 - \phi_1)}\sin{\frac{\theta}{2}} &
                    \cos{\frac{\theta}{2}} & 0 \\
                    -ie^{i (\phi_0 + \phi_1)}\sin{\frac{\theta}{2}} & 0
                    & 0 & \cos{\frac{\theta}{2}}
                    \end{bmatrix}.

    Args:
        angle_1 (Union[FreeParameterExpression, float]): angle in radians.
        angle_2 (Union[FreeParameterExpression, float]): angle in radians.
        angle_3 (Union[FreeParameterExpression, float]): angle in radians.
            Default value is angle_3=pi/2.
    """

    def __init__(
        self,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        angle_3: FreeParameterExpression | float = np.pi / 2,
    ):
        super().__init__(
            angle_1=angle_1,
            angle_2=angle_2,
            angle_3=angle_3,
            qubit_count=None,
            ascii_symbols=[_multi_angled_ascii_characters("MS", angle_1, angle_2, angle_3)] * 2,
        )

    @property
    def _qasm_name(self) -> str:
        return "ms"

    def to_matrix(self) -> np.ndarray:
        return np.array([
            [
                np.cos(self.angle_3 / 2),
                0,
                0,
                -1j * np.exp(-1j * (self.angle_1 + self.angle_2)) * np.sin(self.angle_3 / 2),
            ],
            [
                0,
                np.cos(self.angle_3 / 2),
                -1j * np.exp(-1j * (self.angle_1 - self.angle_2)) * np.sin(self.angle_3 / 2),
                0,
            ],
            [
                0,
                -1j * np.exp(1j * (self.angle_1 - self.angle_2)) * np.sin(self.angle_3 / 2),
                np.cos(self.angle_3 / 2),
                0,
            ],
            [
                -1j * np.exp(1j * (self.angle_1 + self.angle_2)) * np.sin(self.angle_3 / 2),
                0,
                0,
                np.cos(self.angle_3 / 2),
            ],
        ])

    def adjoint(self) -> list[Gate]:
        return [MS(self.angle_1 + np.pi, self.angle_2, self.angle_3)]

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
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        angle_3: FreeParameterExpression | float = np.pi / 2,
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Iterable[Instruction]:
        r"""IonQ Mølmer-Sørensen gate.

        .. math:: &\mathtt{MS}(\phi_0, \phi_1, \theta) =\\ &\begin{bmatrix}
                    \cos{\frac{\theta}{2}} & 0 &
                    0 & -ie^{-i (\phi_0 + \phi_1)}\sin{\frac{\theta}{2}} \\
                    0 & \cos{\frac{\theta}{2}} &
                    -ie^{-i (\phi_0 - \phi_1)}\sin{\frac{\theta}{2}} & 0 \\
                    0 & -ie^{i (\phi_0 - \phi_1)}\sin{\frac{\theta}{2}} &
                    \cos{\frac{\theta}{2}} & 0 \\
                    -ie^{i (\phi_0 + \phi_1)}\sin{\frac{\theta}{2}} & 0
                    & 0 & \cos{\frac{\theta}{2}}
                    \end{bmatrix}.

        Args:
            target1 (QubitInput): Target qubit 1 index.
            target2 (QubitInput): Target qubit 2 index.
            angle_1 (Union[FreeParameterExpression, float]): angle in radians.
            angle_2 (Union[FreeParameterExpression, float]): angle in radians.
            angle_3 (Union[FreeParameterExpression, float]): angle in radians.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Iterable[Instruction]: MS instruction.

        Examples:
            >>> circ = Circuit().ms(0, 1, 0.15, 0.34)
        """
        return [
            Instruction(
                MS(angle_1, angle_2, angle_3),
                target=[target1, target2],
                control=control,
                control_state=control_state,
                power=power,
            )
        ]


Gate.register_gate(MS)


class Unitary(Gate):
    """Arbitrary unitary gate.

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

    def adjoint(self) -> list[Gate]:
        return [Unitary(self._matrix.conj().T, display_name=f"({self.ascii_symbols})^†")]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Unitary.construct(
            targets=list(target),
            matrix=Unitary._transform_matrix_to_ir(self._matrix),
        )

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        qubits = [serialization_properties.format_target(int(qubit)) for qubit in target]
        formatted_matrix = np.array2string(
            self._matrix,
            separator=", ",
            formatter={"all": format_complex},
            threshold=float("inf"),
        ).replace("\n", "")

        return f"#pragma braket unitary({formatted_matrix}) {', '.join(qubits)}"

    def __eq__(self, other: Unitary):
        return self.matrix_equivalence(other) if isinstance(other, Unitary) else False

    def __hash__(self):
        return hash((self.name, str(self._matrix), self.qubit_count))

    @staticmethod
    def _transform_matrix_to_ir(matrix: np.ndarray) -> list:
        return [[[element.real, element.imag] for element in row] for row in matrix.tolist()]

    @staticmethod
    @circuit.subroutine(register=True)
    def unitary(targets: QubitSet, matrix: np.ndarray, display_name: str = "U") -> Instruction:
        r"""Arbitrary unitary gate.

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
            >>> circ = Circuit().unitary(matrix=np.array([[0, 1], [1, 0]]), targets=[0])
        """
        # TODO: handle controlled unitary
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
    def parameters(self) -> list[FreeParameter]:
        r"""Returns the list of `FreeParameter` s associated with the gate."""
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
        targets: QubitSet,
        pulse_sequence: PulseSequence,
        display_name: str = "PG",
        *,
        control: QubitSetInput | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Instruction:
        r"""Arbitrary pulse gate which provides the ability to embed custom pulse sequences
           within circuits.

        Args:
            targets (QubitSet): Target qubits. Note: These are only for representational purposes.
                The actual targets are determined by the frames used in the pulse sequence.
            pulse_sequence (PulseSequence): PulseSequence to embed within the circuit.
            display_name (str): Name to be used for an instance of this pulse gate
                for circuit diagrams. Defaults to `PG`.
            control (Optional[QubitSetInput]): Control qubit(s). Default None.
            control_state (Optional[BasisStateInput]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control`. Will be ignored if `control` is not present. May be represented as a
                string, list, or int. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state. Default "1" * len(control).
            power (float): Integer or fractional power to raise the gate to. Negative
                powers will be split into an inverse, accompanied by the positive power.
                Default 1.

        Returns:
            Instruction: Pulse gate instruction.

        Examples:
            >>> pulse_seq = PulseSequence().set_frequency(frame, frequency)....
            >>> circ = Circuit().pulse_gate(pulse_sequence=pulse_seq, targets=[0])
        """
        return Instruction(
            PulseGate(pulse_sequence, len(QubitSet(targets)), display_name),
            target=targets,
            control=control,
            control_state=control_state,
            power=power,
        )


Gate.register_gate(PulseGate)


def format_complex(number: complex) -> str:
    """Format a complex number into <a> + <b>im to be consumed by the braket unitary pragma

    Args:
        number (complex): A complex number.

    Returns:
        str: The formatted string.
    """
    if number.real:
        if not number.imag:
            return f"{number.real}"
        imag_sign = "+" if number.imag > 0 else "-"
        return f"{number.real} {imag_sign} {abs(number.imag)}im"
    if number.imag:
        return f"{number.imag}im"
    return "0"
