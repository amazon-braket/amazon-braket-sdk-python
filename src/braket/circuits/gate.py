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

from collections.abc import Sequence
from itertools import groupby
from typing import Any

from braket.circuits.basis_state import BasisState, BasisStateInput
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    SerializationProperties,
)
from braket.registers.qubit_set import QubitSet


class Gate(QuantumOperator):
    """Class `Gate` represents a quantum gate that operates on N qubits. Gates are considered the
    building blocks of quantum circuits. This class is considered the gate definition containing
    the metadata that defines what a gate is and what it does.
    """

    def __init__(self, qubit_count: int | None, ascii_symbols: Sequence[str]):
        """Initializes a `Gate`.

        Args:
            qubit_count (Optional[int]): Number of qubits this gate interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the gate. These are used when
                printing a diagram of circuits. Length must be the same as `qubit_count`, and
                index ordering is expected to correlate with target ordering on the instruction.
                For instance, if CNOT instruction has the control qubit on the first index and
                target qubit on the second index. Then ASCII symbols would have ["C", "X"] to
                correlate a symbol with that index.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`
        """
        # TODO: implement ascii symbols for control modifier
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    @property
    def _qasm_name(self) -> NotImplementedError:
        raise NotImplementedError

    def adjoint(self) -> list[Gate]:
        """Returns a list of gates that implement the adjoint of this gate.

        This is a list because some gates do not have an inverse defined by a single existing gate.

        Returns:
            list[Gate]: The gates comprising the adjoint of this gate.
        """
        raise NotImplementedError(f"Gate {self.name} does not have adjoint implemented")

    def to_ir(
        self,
        target: QubitSet,
        ir_type: IRType = IRType.JAQCD,
        serialization_properties: SerializationProperties | None = None,
        *,
        control: QubitSet | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> Any:
        r"""Returns IR object of quantum operator and target

        Args:
            target (QubitSet): target qubit(s).
            ir_type(IRType) : The IRType to use for converting the gate object to its
                IR representation. Defaults to IRType.JAQCD.
            serialization_properties (Optional[SerializationProperties]): The serialization
                properties to use while serializing the object to the IR representation. The
                serialization properties supplied must correspond to the supplied `ir_type`.
                Defaults to None.
            control (Optional[QubitSet]): Control qubit(s). Only supported for OpenQASM.
                Default None.
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
            Any: IR object of the quantum operator and target

        Raises:
            ValueError: If the supplied `ir_type` is not supported, or if the supplied serialization
            properties don't correspond to the `ir_type`.
            ValueError: If gate modifiers are supplied with `ir_type` Jaqcd.
        """
        if ir_type == IRType.JAQCD:
            if control or power != 1:
                raise ValueError("Gate modifiers are not supported with Jaqcd.")
            return self._to_jaqcd(target)
        if ir_type == IRType.OPENQASM:
            if serialization_properties and not isinstance(
                serialization_properties, OpenQASMSerializationProperties
            ):
                raise ValueError(
                    "serialization_properties must be of type OpenQASMSerializationProperties "
                    "for IRType.OPENQASM."
                )
            return self._to_openqasm(
                target,
                serialization_properties or OpenQASMSerializationProperties(),
                control=control,
                control_state=control_state,
                power=power,
            )
        raise ValueError(f"Supplied ir_type {ir_type} is not supported.")

    def _to_jaqcd(self, target: QubitSet) -> Any:
        """Returns the JAQCD representation of the gate.

        Args:
            target (QubitSet): target qubit(s).

        Returns:
            Any: JAQCD object representing the gate.
        """
        raise NotImplementedError("to_jaqcd is not implemented.")

    def _to_openqasm(
        self,
        target: QubitSet,
        serialization_properties: OpenQASMSerializationProperties,
        *,
        control: QubitSet | None = None,
        control_state: BasisStateInput | None = None,
        power: float = 1,
    ) -> str:
        """Returns the OpenQASM string representation of the gate.

        Args:
            target (QubitSet): target qubit(s).
            serialization_properties (OpenQASMSerializationProperties): The serialization properties
                to use while serializing the object to the IR representation.
            control (Optional[QubitSet]): Control qubit(s). Default None.
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
            str: Representing the openqasm representation of the gate.
        """
        target_qubits = [serialization_properties.format_target(int(qubit)) for qubit in target]
        if control:
            control_qubits = [
                serialization_properties.format_target(int(qubit)) for qubit in control
            ]
            control_state = (1,) * len(control) if control_state is None else control_state
            control_basis_state = BasisState(control_state, len(control))
            control_modifiers = []
            for state, group in groupby(control_basis_state.as_tuple):
                modifier_name = "neg" * (not state) + "ctrl"
                control_modifiers += [
                    (
                        f"{modifier_name}"
                        if (num_control := len(list(group))) == 1
                        else f"{modifier_name}({num_control})"
                    )
                ]
            control_modifiers.append("")
            qubits = control_qubits + target_qubits
            control_prefix = " @ ".join(control_modifiers)
        else:
            qubits = target_qubits
            control_prefix = ""
        inv_prefix = "inv @ " if power and power < 0 else ""
        power_prefix = f"pow({abs_power}) @ " if (abs_power := abs(power)) != 1 else ""
        param_string = (
            f"({', '.join(map(str, self.parameters))})" if hasattr(self, "parameters") else ""
        )

        return (
            f"{inv_prefix}{power_prefix}{control_prefix}"
            f"{self._qasm_name}{param_string}{','.join([f' {qubit}' for qubit in qubits])};"
        )

    @property
    def ascii_symbols(self) -> tuple[str, ...]:
        """tuple[str, ...]: Returns the ascii symbols for the quantum operator."""
        return self._ascii_symbols

    def __eq__(self, other: Gate):
        return isinstance(other, Gate) and self.name == other.name

    def __repr__(self):
        return f"{self.name}('qubit_count': {self._qubit_count})"

    def __hash__(self):
        return hash((self.name, self.qubit_count))

    @classmethod
    def register_gate(cls, gate: type[Gate]) -> None:
        """Register a gate implementation by adding it into the Gate class.

        Args:
            gate (type[Gate]): Gate class to register.
        """
        setattr(cls, gate.__name__, gate)
