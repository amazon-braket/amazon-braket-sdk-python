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

from typing import Callable, Tuple

from braket.experimental.autoqasm import program as aq_program
from braket.experimental.autoqasm.instructions.qubits import QubitIdentifierType as Qubit
from braket.pulse import PulseSequence


class GateCalibration:
    def __init__(
        self,
        gate_name: str,
        qubits: Tuple[Qubit],
        angles: Tuple[float],
        calibration_callable: Callable,
    ):
        """_summary_

        Args:
            gate_name (str): Name of the gate.
            qubits (Tuple[Qubit]): The qubits on which the gate calibration is defined.
            angles (Tuple[float], optional): The angles at which the gate calibration is defined.
            calibration_callable (Callable): _description_
        """
        self.gate_name = gate_name
        self.qubits = qubits
        self.angles = angles
        self.calibration_callable = calibration_callable

    def _to_oqpy_program(self) -> PulseSequence:
        with aq_program.build_program() as program_conversion_context:
            self._register_to_program_context(program_conversion_context)
        return program_conversion_context.get_oqpy_program()

    def _register_to_program_context(
        self, program_conversion_context: aq_program.ProgramConversionContext
    ) -> None:
        """Register the gate calibrations to a program conversion_context.

        Args:
            program_conversion_context (aq_program.ProgramConversionContext): The program context
                to register the gate calibrations.
        """
        with program_conversion_context.calibration_definition(
            self.gate_name, self.qubits, self.angles
        ):
            self.calibration_callable()
