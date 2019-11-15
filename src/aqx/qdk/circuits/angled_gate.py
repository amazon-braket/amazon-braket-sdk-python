# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from typing import Sequence

from aqx.qdk.circuits.gate import Gate


class AngledGate(Gate):
    """
    Class `AngledGate` represents a quantum gate that operates on N qubits and an angle.
    """

    def __init__(self, angle: float, qubit_count: int, ascii_symbols: Sequence[str]):
        """
        Args:
            angle (float): Angle of gate in radians
            qubit_count (int): Number of qubits this gate interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the gate, these are used when
                printing a diagram of circuits. Length must be the same as `qubit_count`, and
                index ordering is expected to correlate with target ordering on the instruction.
                For instance, if CNOT instruction has the control qubit on the first index and
                target qubit on the second index. Then ASCII symbols would have ["C", "X"] to
                correlate a symbol with that index.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are None, or
                `ascii_symbols` length != `qubit_count`, or `angle` is None
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        if angle is None:
            raise ValueError(f"angle must not be None")
        self._angle = angle

    @property
    def angle(self) -> float:
        """
        Returns angle for the gate

        Returns:
            angle (float): angle of gate in radians
        """
        return self._angle
