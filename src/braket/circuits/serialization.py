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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class IRType(str, Enum):
    """Defines the available IRTypes for circuit serialization."""

    OPENQASM = "OPENQASM"
    JAQCD = "JAQCD"


class QubitReferenceType(str, Enum):
    """Defines how qubits should be referenced in the generated OpenQASM string.
    See https://qiskit.github.io/openqasm/language/types.html#quantum-types
    for details.
    """

    VIRTUAL = "VIRTUAL"
    PHYSICAL = "PHYSICAL"


class SerializableProgram(ABC):
    @abstractmethod
    def to_ir(
        self,
        ir_type: IRType = IRType.OPENQASM,
    ) -> str:
        """Serializes the program into an intermediate representation.

        Args:
            ir_type (IRType): The IRType to use for converting the program to its
                IR representation. Defaults to IRType.OPENQASM.

        Raises:
            ValueError: Raised if the supplied `ir_type` is not supported.

        Returns:
            str: A representation of the program in the `ir_type` format.
        """


@dataclass
class OpenQASMSerializationProperties:
    """Properties for serializing a circuit to OpenQASM.

    qubit_reference_type (QubitReferenceType): determines whether to use
        logical qubits or physical qubits (q[i] vs $i).
    """

    qubit_reference_type: QubitReferenceType = QubitReferenceType.VIRTUAL

    def format_target(self, target: int) -> str:
        """Format a target qubit to the appropriate OpenQASM representation.

        Args:
            target (int): The target qubit.

        Returns:
            str: The OpenQASM representation of the target qubit.
        """
        qubit_reference_format = (
            "q[{}]" if self.qubit_reference_type == QubitReferenceType.VIRTUAL else "${}"
        )
        return qubit_reference_format.format(target)


# Type alias to refer to possible serialization properties. Can be expanded once
# new properties are added.
SerializationProperties = OpenQASMSerializationProperties
