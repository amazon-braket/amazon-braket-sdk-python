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
from typing import Any

from braket.circuits import circuit
from braket.circuits.angled_gate import _multi_angled_ascii_characters
from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.instruction import Instruction
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.serialization import (
    IRType,
    SerializationProperties,
)

# from braket.experimental_capabilities.experimental_capability import ExperimentalCapability
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
    ExperimentalCapabilityContextError,
)

# from braket.experimental_capabilities.iqm.iqm_experimental_capabilities import (
#     IqmExperimentalCapabilities,
# )
from braket.registers.qubit_set import QubitSet, QubitSetInput

# EXPCAP_FLAG = IqmExperimentalCapabilities.classical_control.value


class ExperimentalQuantumOperator(QuantumOperator):
    def __init__(
        self,
        qubit_count: int,
        ascii_symbols: list[str],
    ) -> None:
        """Base class for experimental quantum operators.

        This class provides the foundation for quantum operators that are part of
        experimental capabilities and ensures that they can only be instantiated
        when the appropriate capability is enabled.

        Args:
            qubit_count: The number of qubits this operator acts on.
            ascii_symbols: ASCII string symbols for the operator.
        """
        self._validate_experimental_capabilities_enabled()

        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        self._parameters = None

    @property
    def _qasm_name(self) -> str:
        """Get the OpenQASM name for this operator.

        This property must be implemented by subclasses.

        Returns:
            str: The OpenQASM name for this operator.

        Raises:
            NotImplementedError: If the subclass does not implement this property.
        """
        raise NotImplementedError

    @property
    def ascii_symbols(self) -> tuple[str, ...]:
        """Get the ASCII symbols for this operator.

        Returns:
            tuple[str]: The ASCII symbols for this operator.
        """
        return self._ascii_symbols

    @property
    def parameters(self) -> list[FreeParameterExpression | float | int]:
        """Get the parameters associated with this operator.

        Returns:
            list[FreeParameterExpression | float | int]: The free parameters or fixed values
                associated with this operator.
        """
        return self._parameters

    def to_ir(
        self,
        target: QubitSet | None = None,
        ir_type: IRType = IRType.OPENQASM,
        serialization_properties: SerializationProperties | None = None,
        **kwargs: Any,
    ) -> Any:
        """Convert this operator to its IR representation.

        Args:
            target: Target qubit(s). Defaults to None.
            ir_type: The IR type to use. Defaults to IRType.OPENQASM.
            serialization_properties: Properties to use for serialization. Defaults to None.

        Returns:
            Any: The IR representation of this operator.
        """
        if ir_type != IRType.OPENQASM:
            raise ValueError(f"supplied ir_type {ir_type} is not supported for {self._qasm_name}.")

        target_qubits = [serialization_properties.format_target(int(qubit)) for qubit in target]
        parameters = f"({', '.join(map(str, self.parameters))})"
        return f"{self._qasm_name}{parameters} {target_qubits[0]};"

    def _validate_experimental_capabilities_enabled(self) -> None:
        """Check if the experimental capabilities are enabled."""
        if not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled:
            raise ExperimentalCapabilityContextError(
                f"{self.__class__.__name__} is an experimental capability. It can only be "
                "instantiated under EnableExperimentalCapability. For more information about "
                "experimental capabilities, view the Amazon Braket Developer Guide."
            )


class CCPRx(ExperimentalQuantumOperator):
    """Classically controlled Phased Rx gate.

    A rotation around the X-axis with a phase factor, where the rotation depends
    on the value of a classical feedback.

    Args:
        angle_1 (FreeParameterExpression | float): The first angle of the gate in radians or
            expression representation.
        angle_2 (FreeParameterExpression | float): The second angle of the gate in radians or
            expression representation.
        feedback_key (int): The integer feedback key that points to a measurement result.
    """

    def __init__(
        self,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        feedback_key: int,
    ):
        ascii_symbols = f"{feedback_key}→" + _multi_angled_ascii_characters(
            "CCPRx", angle_1, angle_2
        )
        super().__init__(qubit_count=1, ascii_symbols=[ascii_symbols])

        angles = [
            (angle if isinstance(angle, FreeParameterExpression) else float(angle))
            for angle in (angle_1, angle_2)
        ]
        self._parameters = [*angles, feedback_key]

    @property
    def _qasm_name(self) -> str:
        """Get the OpenQASM name for this operator.

        Returns:
            str: The OpenQASM name "cc_prx".
        """
        return "cc_prx"

    @staticmethod
    @circuit.subroutine(register=True)
    def cc_prx(
        target: QubitSetInput,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        feedback_key: int,
    ) -> Iterable[Instruction]:
        """Conditional PhaseRx gate.

        Applies a rotation around the X-axis with a phase factor, conditioned on
        the value in a classical feedback register.

        Args:
            target (QubitSetInput): Target qubit(s).
            angle_1 (FreeParameterExpression | float): First angle in radians.
            angle_2 (FreeParameterExpression | float): Second angle in radians.
            feedback_key (int): The integer feedback key that points to a measurement result.

        Returns:
            Iterable[Instruction]: CCPRx instruction.

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

    Performs a measurement. The result is associated with a feedback key that
    can be used later in conditional operations.

    Args:
        feedback_key (int): The integer feedback key that points to a measurement result.
    """

    def __init__(
        self,
        feedback_key: int,
    ) -> None:
        ascii_symbols = f"MFF→{feedback_key}"
        super().__init__(qubit_count=1, ascii_symbols=[ascii_symbols])
        self._parameters = [feedback_key]

    @property
    def _qasm_name(self) -> str:
        """Get the OpenQASM name for this operator.

        Returns:
            str: The OpenQASM name "measure_ff".
        """
        return "measure_ff"

    @staticmethod
    @circuit.subroutine(register=True)
    def measure_ff(
        target: QubitSetInput,
        feedback_key: int,
    ) -> Iterable[Instruction]:
        r"""Measure and store result for feed-forward operations.

        Performs a measurement on the target qubit and stores the result in a
        classical feedback register for later use in conditional operations.

        Args:
            target (QubitSetInput): Target qubit(s).
            feedback_key (int): The integer feedback key that points to a measurement result.

        Returns:
            Iterable[Instruction]: MeasureFF instruction.

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
