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

from typing import Any

from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    SerializationProperties,
)
from braket.registers.qubit_set import QubitSet


class Measure(QuantumOperator):
    """Class `Measure` represents a measure operation on targeted qubits"""

    def __init__(self, **kwargs):
        """Inits a `Measure`.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`
        """
        super().__init__(qubit_count=1, ascii_symbols=["M"])
        self._target_index = kwargs.get("index")

    @property
    def ascii_symbols(self) -> tuple[str]:
        """tuple[str]: Returns the ascii symbols for the measure."""
        return self._ascii_symbols

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
        if ir_type == IRType.JAQCD:
            return self._to_jaqcd()
        if ir_type == IRType.OPENQASM:
            return self._to_openqasm(
                target, serialization_properties or OpenQASMSerializationProperties() ** kwargs
            )
        raise ValueError(f"supplied ir_type {ir_type} is not supported.")

    def _to_jaqcd(self) -> Any:
        """Returns the JAQCD representation of the measure."""
        raise NotImplementedError("measure instructions are not supported with JAQCD.")

    def _to_openqasm(
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties
    ) -> str:
        """Returns the openqasm string representation of the measure."""
        target_qubits = [serialization_properties.format_target(int(qubit)) for qubit in target]
        instructions = []
        for idx, qubit in enumerate(target_qubits):
            bit_index = (
                self._target_index if self._target_index and len(target_qubits) == 1 else idx
            )
            instructions.append(f"b[{bit_index}] = measure {qubit};")

        return "\n".join(instructions)

    def __eq__(self, other: Measure):
        return isinstance(other, Measure)

    def __repr__(self):
        return self.name
