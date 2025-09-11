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

from typing import Any

import braket.ir.jaqcd as ir

from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.serialization import IRType, SerializationProperties
from braket.registers.qubit_set import QubitSet


class StartVerbatimBox(CompilerDirective):
    """Prevents the compiler from modifying any ensuing instructions
    until the appearance of a corresponding ``EndVerbatimBox``.
    """

    def __init__(self):
        super().__init__(["StartVerbatim"])

    def counterpart(self) -> CompilerDirective:
        return EndVerbatimBox()

    @property
    def requires_physical_qubits(self) -> bool:
        return True

    def _to_jaqcd(self, *args, **kwargs) -> Any:
        return ir.StartVerbatimBox.construct()

    def _to_openqasm(self) -> str:
        return "#pragma braket verbatim\nbox{"


class EndVerbatimBox(CompilerDirective):
    """Marks the end of a portion of code following a StartVerbatimBox that prevents the enclosed
    instructions from being modified by the compiler.
    """

    def __init__(self):
        super().__init__(["EndVerbatim"])

    def counterpart(self) -> CompilerDirective:
        return StartVerbatimBox()

    @property
    def requires_physical_qubits(self) -> bool:
        return True

    def _to_jaqcd(self, *args, **kwargs) -> Any:
        return ir.EndVerbatimBox.construct()

    def _to_openqasm(self) -> str:
        return "}"


class Barrier(CompilerDirective):
    """Barrier compiler directive."""

    def __init__(self, qubit_indices: list[int]):
        super().__init__(["||"])
        self._qubit_indices = qubit_indices

    @property
    def qubit_indices(self) -> list[int]:
        return self._qubit_indices

    @property
    def qubit_count(self) -> int:
        return len(self._qubit_indices)

    def _to_jaqcd(self) -> Any:
        raise NotImplementedError("Barrier is not supported in JAQCD")

    def to_ir(
        self,
        target: QubitSet | None,
        ir_type: IRType,
        serialization_properties: SerializationProperties | None = None,
        **kwargs,
    ) -> Any:
        if ir_type.name == "OPENQASM":
            if target:
                qubits = ", ".join(serialization_properties.format_target(int(q)) for q in target)
                return f"barrier {qubits};"
            return "barrier;"
        return super().to_ir(target, ir_type, serialization_properties, **kwargs)
