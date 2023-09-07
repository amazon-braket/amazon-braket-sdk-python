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

from typing import Callable, Iterable

import oqpy

from braket.experimental.autoqasm.instructions.qubits import QubitIdentifierType as Qubit


class GateCalibration:
    def __init__(
        self,
        gate_function: Callable,
        qubits: Iterable[Qubit],
        angles: Iterable[float],
        oqpy_program: oqpy.Program,
    ):
        """_summary_

        Args:
            gate_function (Callable): The gate function which calibration is defined.
            qubits (Tuple[Qubit]): The qubits on which the gate calibration is defined.
            angles (Tuple[float]): The angles at which the gate calibration is defined.
            calibration_callable (oqpy.Program): _description_
        """
        self.gate_function = gate_function
        self.qubits = qubits
        self.angles = angles
        self.oqpy_program = oqpy_program
