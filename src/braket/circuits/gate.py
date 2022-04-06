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

from typing import Any, Optional, Sequence

from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.qubit_set import QubitSet
from braket.circuits.serialization import IRType


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

    def to_ir(
        self, target: QubitSet, ir_type: IRType = IRType.JAQCD, qubit_reference_format: str = "${}"
    ) -> Any:
        """Returns IR object of quantum operator and target

        Args:
            target (QubitSet): target qubit(s)
            ir_type(IRType) : The IRType to use for converting the gate object to its
                IR representation. Defaults to IRType.JAQCD.
            qubit_reference_format (str): The string format to use for referencing the qubits
                within the gate. Defaults to "${}" for referencing qubits physically.
        Returns:
            IR object of the quantum operator and target
        """
        if ir_type == IRType.JAQCD:
            return self.to_jaqcd(target)
        elif ir_type == IRType.OPENQASM:
            return self.to_openqasm(target, qubit_reference_format)
        else:
            raise ValueError(f"Supplied ir_type {ir_type} is not supported.")

    def to_jaqcd(self, target: QubitSet) -> Any:
        """
        Returns the JAQCD representation of the gate.

        Args:
            target (QubitSet): target qubit(s).

        Returns:
            Any: JAQCD object representing the gate.
        """
        raise NotImplementedError("to_jaqcd has not been implemented yet.")

    def to_openqasm(self, target: QubitSet, qubit_reference_format: str) -> str:
        """
        Returns the openqasm string representation of the gate.

        Args:
            target (QubitSet): target qubit(s).
            qubit_reference_format(str): The string format to use for referencing the qubits
                within the gate.

        Returns:
            str: Representing the openqasm representation of the gate.
        """
        raise NotImplementedError("to_openqasm has not been implemented yet.")

    def __eq__(self, other):
        if isinstance(other, Gate):
            return self.name == other.name
        return False

    def __repr__(self):
        return f"{self.name}('qubit_count': {self.qubit_count})"

    @classmethod
    def register_gate(cls, gate: "Gate"):
        """Register a gate implementation by adding it into the Gate class.

        Args:
            gate (Gate): Gate class to register.
        """
        setattr(cls, gate.__name__, gate)
