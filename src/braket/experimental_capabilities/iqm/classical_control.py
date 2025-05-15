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

from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    SerializationProperties,
)

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
from braket.registers.qubit import QubitInput
from braket.registers.qubit_set import QubitSet, QubitSetInput
from braket.circuits.quantum_operator import QuantumOperator

from braket.experimental_capabilities.experimental_capability import ExperimentalCapability
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
    ExperimentalCapabilityContextError,
)
from braket.experimental_capabilities.iqm.iqm_experimental_capabilities import (
    IqmExperimentalCapabilities,
)


EXPCAP_FLAG = IqmExperimentalCapabilities.classical_control.value


class ExperimentalQuantumOperator(QuantumOperator):
    r"""Phase Rx gate.

    Args:
        angle_1 (Union[FreeParameterExpression, float]): The first angle of the gate in
            radians or expression representation.
        angle_2 (Union[FreeParameterExpression, float]): The second angle of the gate in
            radians or expression representation.
    """

    def __init__(
        self,
        expcap_flag: ExperimentalCapability,
        qubit_count: int,
        ascii_symbols: list[str],
    ):
        if not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(expcap_flag):
            raise ExperimentalCapabilityContextError(
                f"{self.name} can only be instantiated when {expcap_flag.extended_name} is enabled in EnableExperimentalCapability."
            )

        super().__init__(qubit_count=1, ascii_symbols=["C"])
        self._parameters = None

    @property
    def _qasm_name(self) -> str:
        raise NotImplementedError

    @property
    def ascii_symbols(self) -> tuple[str]:
        """tuple[str]: Returns the ascii symbols for the measure."""
        return self._ascii_symbols

    @property
    def parameters(self) -> list[FreeParameterExpression | float]:
        """Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            list[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    def to_ir(
        self,
        target: QubitSet | None = None,
        ir_type: IRType = IRType.OPENQASM,
        serialization_properties: SerializationProperties | None = None,
        **kwargs,
    ) -> Any:
        """Returns IR object of the measure operator.

        Args:
            target (QubitSet | None): target qubit(s). Defaults to None
            ir_type(IRType) : The IRType to use for converting the measure object to its
                IR representation. Defaults to IRType.OpenQASM.
            serialization_properties (SerializationProperties | None): The serialization properties
                to use while serializing the object to the IR representation. The serialization
                properties supplied must correspond to the supplied `ir_type`. Defaults to None.

        Returns:
            Any: IR object of the measure operator.

        Raises:
            ValueError: If the supplied `ir_type` is not supported.
        """
        if ir_type != IRType.OPENQASM:
            raise ValueError(f"supplied ir_type {ir_type} is not supported for {self._qasm_name}.")

        target_qubits = [serialization_properties.format_target(int(qubit)) for qubit in target]
        parameters = f"({', '.join(map(str, self.parameters))})"
        return f"{self._qasm_name}{parameters} {target_qubits[0]};"


class CCPRx(ExperimentalQuantumOperator):
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
        feedback_key: int,
    ):
        super().__init__(expcap_flag=EXPCAP_FLAG, qubit_count=1, ascii_symbols=["C"])
        angles = [
            (
                angle
                if isinstance(angle, FreeParameterExpression)
                else float(angle)  # explicit casting in case angle is e.g. np.float32
            )
            for angle in (angle_1, angle_2)
        ]
        self._parameters = angles + [feedback_key]

    @property
    def _qasm_name(self) -> str:
        return "cc_prx"

    @staticmethod
    @circuit.subroutine(register=True)
    def cc_prx(
        target: QubitSetInput,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        feedback_key: int,
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

        Returns:
            Iterable[Instruction]: PhaseRx instruction.

        Examples:
            >>> circ = Circuit().cc_prx(0, 0.15, 0.25, 0)
        """
        return [
            Instruction(
                CCPRx(angle_1, angle_2, feedback_key),
                target=qubit,
            )
            for qubit in QubitSet(target)
        ]


class MeasureFF(ExperimentalQuantumOperator):
    r"""Measurement for Feed Forward control.

    Args:
        feedback_key (int):
    """

    def __init__(
        self,
        feedback_key: int,
    ):
        super().__init__(expcap_flag=EXPCAP_FLAG, qubit_count=1, ascii_symbols=["MFF"])
        self._parameters = [feedback_key]

    @property
    def _qasm_name(self) -> str:
        return "measure_ff"

    @staticmethod
    @circuit.subroutine(register=True)
    def measure_ff(
        target: QubitSetInput,
        feedback_key: int,
    ) -> Iterable[Instruction]:
        r"""PhaseRx gate.

        .. math:: \mathtt{PRx}(\theta,\phi) = \begin{bmatrix}
                \cos{(\theta / 2)} & -i e^{-i \phi} \sin{(\theta / 2)} \\
                -i e^{i \phi} \sin{(\theta / 2)} & \cos{(\theta / 2)}
            \end{bmatrix}.

        Args:
            target (QubitSetInput): Target qubit(s).
            feedback_key (int): 

        Returns:
            Iterable[Instruction]: PhaseRx instruction.

        Examples:
            >>> circ = Circuit().measure_ff(0, 0)
        """
        return [
            Instruction(
                MeasureFF(feedback_key),
                target=qubit,
            )
            for qubit in QubitSet(target)
        ]
