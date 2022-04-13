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

from dataclasses import dataclass
from enum import Enum


class IRType(str, Enum):
    """Defines the available IRTypes for circuit serialization."""

    OPENQASM = "OPENQASM"
    JAQCD = "JAQCD"


class QubitReferenceType(str, Enum):
    """
    Defines how qubits should be referenced in the generated OpenQASM string.
    See https://qiskit.github.io/openqasm/language/types.html#quantum-types
    for details.
    """

    VIRTUAL = "VIRTUAL"
    PHYSICAL = "PHYSICAL"


@dataclass
class OpenQASMSerializationProperties:
    qubit_reference_type: QubitReferenceType = QubitReferenceType.VIRTUAL
    # Defines the format for addressing the qubits. This assumes that a qubit register named
    # q has been pre-defined in the OpenQASMProgram.
    qubit_reference_format: str = "q[{}]"


# Type alias to refer to possible serialization properties. Can be expanded once
# new properties are added.
SerializationProperties = OpenQASMSerializationProperties
