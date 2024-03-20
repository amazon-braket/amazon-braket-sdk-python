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

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from braket.aws.aws_device import AwsDevice

import braket.circuits.circuit as cir
from braket.circuits.gate import Gate
from braket.circuits.gate_calibrations import GateCalibrations
from braket.circuits.qubit_set import QubitSet
from braket.circuits.result_type import ResultType
from braket.parametric.free_parameter import FreeParameter
from braket.pulse.frame import Frame
from braket.pulse.pulse_sequence import PulseSequence


class CircuitPulseSequenceBuilder:
    """Builds a pulse sequence from circuits."""

    def __init__(
        self,
        device: AwsDevice,
        gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence] | None = None,
    ) -> None:
        _validate_device(device)
        gate_definitions = gate_definitions or {}

        self._device = device
        self._gate_calibrations = (
            device.gate_calibrations
            if device.gate_calibrations is not None
            else GateCalibrations({})
        )
        self._gate_calibrations.pulse_sequences.update(gate_definitions)

    def build_pulse_sequence(self, circuit: cir.Circuit) -> PulseSequence:
        """
        Build a PulseSequence corresponding to the full circuit.

        Args:
            circuit (Circuit): Circuit for which to build a diagram.

        Returns:
            PulseSequence: a pulse sequence created from all gates.
        """

        pulse_sequence = PulseSequence()
        if not circuit.instructions:
            return pulse_sequence

        # A list of parameters in the circuit to the currently assigned values.
        if circuit.parameters:
            raise ValueError("All parameters must be assigned to draw the pulse sequence.")

        for instruction in circuit.instructions:
            gate = instruction.operator
            qubits = instruction.target

            gate_pulse_sequence = self._get_pulse_sequence(gate, qubits)

            # FIXME: this creates a single cal block, "barrier;" in defcal could be either
            # global or restricted to the defcal context
            # Right they are global
            pulse_sequence += gate_pulse_sequence

        # Result type columns
        target_result_types = CircuitPulseSequenceBuilder._categorize_result_types(
            circuit.result_types
        )

        for result_type in target_result_types:
            pulse_sequence += result_type._to_pulse_sequence()

        for qubit in circuit.qubits:
            pulse_sequence.capture_v0(self._readout_frame(qubit))

        return pulse_sequence

    def _get_pulse_sequence(self, gate: Gate, qubit: QubitSet) -> PulseSequence:
        parameters = gate.parameters if hasattr(gate, "parameters") else []
        if isinstance(gate, Gate) and gate.name == "PulseGate":
            gate_pulse_sequence = gate.pulse_sequence
        elif (
            gate_pulse_sequence := self._gate_calibrations.pulse_sequences.get((gate, qubit), None)
        ) is None:
            if (
                not hasattr(gate, "parameters")
                or (
                    gate_pulse_sequence := self._find_parametric_gate_calibration(
                        gate, qubit, len(gate.parameters)
                    )
                )
                is None
            ):
                raise ValueError(
                    f"No pulse sequence for {gate.name} was provided in the gate"
                    " calibration set."
                )

        return gate_pulse_sequence(
            **{p.name: v for p, v in zip(gate_pulse_sequence.parameters, parameters)}
        )

    def _find_parametric_gate_calibration(
        self, gate: Gate, qubitset: QubitSet, number_assignment_values: int
    ) -> PulseSequence | None:
        for key in self._gate_calibrations.pulse_sequences:
            if (
                key[0].name == gate.name
                and key[1] == qubitset
                and sum(isinstance(param, FreeParameter) for param in key[0].parameters)
                == number_assignment_values
            ):
                return self._gate_calibrations.pulse_sequences[key]

    def _readout_frame(self, qubit: QubitSet) -> Frame:
        readout_frame_names = {
            "Rigetti": f"q{int(qubit)}_ro_rx_frame",
            "Oxford": f"r{int(qubit)}_measure",
        }
        frame_name = readout_frame_names[self._device.provider_name]
        return self._device.frames[frame_name]

    @staticmethod
    def _categorize_result_types(
        result_types: list[ResultType],
    ) -> list[ResultType]:
        """
        Categorize result types into result types with target and those without.

        Args:
            result_types (list[ResultType]): list of result types

        Returns:
            list[ResultType]: a list of result types with `target` attribute
        """
        target_result_types = []
        for result_type in result_types:
            if hasattr(result_type, "target"):
                target_result_types.append(result_type)
            else:
                warnings.warn(
                    f"{result_type} does not have have a pulse representation"
                    " and it is ignored."
                )
        return target_result_types


def _validate_device(device: AwsDevice | None) -> None:
    if device is None:
        raise ValueError("Device must be set before building pulse sequences.")
    elif device.provider_name not in ("Rigetti", "Oxford"):
        raise ValueError(f"Device {device.name} is not supported.")
