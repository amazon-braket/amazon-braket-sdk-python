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

from typing import Any, Sequence, Tuple

from braket.circuits.operator import Operator
from braket.circuits.qubit_set import QubitSet
from braket.circuits.serialization import IRType


class CompilerDirective(Operator):
    """A directive specifying how the compiler should process a part of the circuit.

    For example, a directive may tell the compiler not to modify some gates in the circuit.
    """

    def __init__(self, ascii_symbols: Sequence[str]):
        """
        Args:
            ascii_symbols (Sequence[str]): ASCII string symbols for the compiler directiver.
                These are used when printing a diagram of circuits.
        """
        if ascii_symbols is None:
            raise ValueError("ascii_symbols must not be None")
        self._ascii_symbols = tuple(ascii_symbols)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def ascii_symbols(self) -> Tuple[str, ...]:
        """Tuple[str, ...]: Returns the ascii symbols for the compiler directive."""
        return self._ascii_symbols

    def to_ir(
        self,
        target: QubitSet = None,
        ir_type: IRType = IRType.JAQCD,
        qubit_reference_format: str = "${}",
        **kwargs,
    ):
        """Returns IR object of the compiler directive.

        Args:
            target (QubitSet): target qubit(s). Defaults to None
            ir_type(IRType) : The IRType to use for converting the compiler directive object to its
                IR representation. Defaults to IRType.JAQCD.
            qubit_reference_format (str): The string format to use for referencing the qubits
                within the gate. Defaults to "${}" for referencing qubits physically.
            **kwargs: Keyword arguments

        Returns:
            IR object of the compiler directive.

        Raises:
            ValueError: If the supplied `ir_type` is not supported.
        """
        if ir_type == IRType.JAQCD:
            return self.to_jaqcd()
        elif ir_type == IRType.OPENQASM:
            return self.to_openqasm()
        else:
            raise ValueError(f"Supplied ir_type {ir_type} is not supported.")

    def to_jaqcd(self) -> Any:
        """Returns the JAQCD representation of the compiler directive."""
        raise NotImplementedError("to_jaqcd has not been implemented yet.")

    def to_openqasm(self) -> str:
        """Returns the openqasm string representation of the compiler directive."""
        raise NotImplementedError("to_openqasm has not been implemented yet.")

    def __eq__(self, other):
        return isinstance(other, CompilerDirective) and self.name == other.name

    def __repr__(self):
        return self.name
