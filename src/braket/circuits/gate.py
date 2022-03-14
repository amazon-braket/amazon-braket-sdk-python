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

import copy
from typing import Any, List, Optional, Sequence, Tuple

from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.qubit_set import QubitSet


class Gate(QuantumOperator):
    """
    Class `Gate` represents a quantum gate that operates on N qubits. Gates are considered the
    building blocks of quantum circuits. This class is considered the gate definition containing
    the metadata that defines what a gate is and what it does.
    """

    def __init__(self, qubit_count: Optional[int], ascii_symbols: Sequence[str]):
        """
        Args:
            qubit_count (int, optional): Number of qubits this gate interacts with.
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
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        self._is_adjoint = False

    def adjoint(self) -> Gate:
        """Returns the adjoint of this gate.

        Returns:
            Gate: The adjoint of this gate.
        """
        new = copy.copy(self)
        new._is_adjoint = not self._is_adjoint
        return new

    def adjoint_expansion(self) -> List[Gate]:
        """Returns a list of gates that comprise the adjoint of this gate.

        This list can only contain non-adjoint instances, in other words, gates that have not had
        `.adjoint` called (or equivalently have had `.adjoint` called an even number of times).
        For compatibility, it is best if all gates in this list are of the same type as this gate.

        Returns:
            List[Gate]: The gates comprising the adjoint of this gate.
        """
        raise NotImplementedError(f"Gate {self.name} does not have adjoint implemented")

    def to_ir(self, target: QubitSet) -> Any:
        """Returns IR object of quantum operator and target

        This method will throw an error if the gate is an adjoint and the adjoint expansion contains
        adjoint gate instances.

        Args:
            target (QubitSet): target qubit(s)
        Returns:
            IR object of the quantum operator and target
        Raises:
            ValueError: If a non-adjoint gate instance is found in the adjoint expansion
        """
        if self._is_adjoint:
            # Use adjoint list of original gate
            # After all, we want the adjoint of the original, not the adjoint of the adjoint!
            ir = []
            for elem in self.adjoint().adjoint_expansion():
                if elem._is_adjoint:
                    raise ValueError(
                        f"Only non-adjoint instances of gates allowed in expansion, found {elem}"
                    )
                ir.append(elem.to_ir(target))
            return ir
        return self._to_ir(target)

    def _to_ir(self, target: QubitSet) -> Any:
        raise NotImplementedError("to_ir has not been implemented yet.")

    @property
    def ascii_symbols(self) -> Tuple[str, ...]:
        """Tuple[str, ...]: Returns the ascii symbols for the quantum operator."""
        if self._is_adjoint:
            return tuple(
                # "C" stands for control, and doesn't need a dagger symbol
                f"({symbol})†" if symbol != "C" else symbol
                for symbol in self._ascii_symbols
            )
        return self._ascii_symbols

    def __eq__(self, other):
        if isinstance(other, Gate):
            return self.name == other.name and self._is_adjoint == other._is_adjoint
        return False

    def __repr__(self):
        if self._is_adjoint:
            return f"({self.name})†('qubit_count': {self._qubit_count})"
        return f"{self.name}('qubit_count': {self._qubit_count})"

    @classmethod
    def register_gate(cls, gate: Gate):
        """Register a gate implementation by adding it into the Gate class.

        Args:
            gate (Gate): Gate class to register.
        """
        setattr(cls, gate.__name__, gate)
