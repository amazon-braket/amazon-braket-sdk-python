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

from collections.abc import Callable, Iterable

from braket.experimental.autoqasm.program import Program
from braket.experimental.autoqasm.types import QubitIdentifierType as Qubit


class GateCalibration:
    def __init__(
        self,
        gate_function: Callable,
        qubits: Iterable[Qubit],
        angles: Iterable[float],
        program: Program,
    ):
        """Definition of a gate calibration, including pulse instructions and the qubits, angles
        and the gate it implements.

        Args:
            gate_function (Callable): The gate function which calibration is defined.
            qubits (Iterable[Qubit]): The qubits on which the gate calibration is defined.
            angles (Iterable[float]): The angles at which the gate calibration is defined.
            program (Program): Calibration instructions as an AutoQASM program.
        """
        self.gate_function = gate_function
        self.qubits = qubits
        self.angles = angles
        self.program = program
