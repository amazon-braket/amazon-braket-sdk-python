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

from typing import TYPE_CHECKING, Callable, Tuple

import braket
from braket.experimental.autoqasm import program as aq_program
from braket.pulse import PulseSequence

if TYPE_CHECKING:
    from braket.experimental.autoqasm import Qubit


class GateCalibrations:
    # TODO: Possibly inherits from BDK GateCalibrations
    """
    A set of gate calibrations.
    """

    def __init__(self):
        self._calibrations = {}

    def register(self, gate_name: str, qubits: Tuple[Qubit], angles: Tuple[float] = ()):
        """A decorator that register the decorated function as a calibration definition of a gate
        in this `GateCalibrations` object.

        Args:
            gate_name (str): Name of the gate
            qubits (Tuple[Qubit]): The qubits on which the gate calibration is defined.
            angles (Tuple[float], optional): The angles at which the gate calibration is defined.
                Defaults to ().
        """

        def wrapper(f: Callable):
            self._calibrations[(gate_name, qubits, angles)] = f
            return f

        return wrapper

    def _register_to_program_context(
        self, program_conversion_context: aq_program.ProgramConversionContext
    ) -> None:
        """Register the gate calibrations to a program conversion_context.

        Args:
            program_conversion_context (aq_program.ProgramConversionContext): The program context
                to register the gate calibrations.
        """
        for calibration_target, calibration_callable in self.calibrations.items():
            gate_name, qubits, angles = calibration_target
            with program_conversion_context.calibration_definition(gate_name, qubits, angles):
                calibration_callable()

    def export(self) -> braket.circuits.GateCalibrations:
        """[WIP] Export to `device.run` compatible object

        Returns:
            braket.circuits.GateCalibrations:
        """
        # TODO: compete this part by making it compatible with device.run
        exported_calibrations = {}
        for calibration_target, calibration_callable in self.calibrations.items():
            with aq_program.build_program(aq_program.UserConfig()) as program_conversion_context:
                gate_name, qubits, angles = calibration_target
                with program_conversion_context.calibration_definition(gate_name, qubits, angles):
                    pulse_sequence = PulseSequence()
                    pulse_sequence._program = calibration_callable()._oqpy_program
                    exported_calibrations[calibration_target] = pulse_sequence
        return braket.circuits.GateCalibrations(exported_calibrations)

    @property
    def calibrations(self):
        return self._calibrations
