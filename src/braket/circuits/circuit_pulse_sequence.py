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

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from braket.aws.aws_device import AwsDevice

import braket.circuits.circuit as cir
from braket.circuits.gate_calibrations import GateCalibrations
from braket.circuits.gates import Gate, PulseGate
from braket.circuits.qubit_set import QubitSet
from braket.circuits.result_type import ResultType
from braket.circuits.serialization import IRType
from braket.pulse.pulse_sequence import PulseSequence


class CircuitPulseSequenceBuilder:
    """Builds ASCII string circuit diagrams."""

    def __init__(
        self,
        device: AwsDevice,
        gate_definitions: Optional[Dict[Tuple[Gate, QubitSet], PulseSequence]] = None,
    ) -> None:
        self._device = device
        self._gate_calibrations = GateCalibrations(
            gate_definitions if gate_definitions is not None else {}
        )

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

        # circuit needs to be verbatim
        # if circuit not verbatim
        #     raise ValueError("Circuit must be encapsulated in a verbatim box.")

        for instruction in circuit.instructions:
            gate = instruction.operator
            qubit = instruction.target
            if isinstance(gate, PulseGate):
                gate_pulse_sequence = gate.pulse_sequence
            elif (
                gate_pulse_sequence := self._gate_calibrations.pulse_sequences[(gate, qubit)]
            ) is None:
                raise ValueError(
                    f"No pulse sequence for {gate.name} was provided in the gate"
                    " calibration set."
                )

            # FIXME: this creates a single cal block, we should have defcals because barrier;
            # would be applied to everything
            pulse_sequence += gate_pulse_sequence

        if circuit.result_types:
            for result_type in circuit.result_types:
                pragma_str = result_type.to_ir(IRType.OPENQASM)
                if pragma_str[:8] == "#pragma ":
                    pulse_sequence._program.pragma(pragma_str[8:])
                else:
                    raise ValueError("Result type cannot be used with pulse sequences.")
        else:
            for qubit in circuit.qubits:
                pulse_sequence.capture_v0(self._readout_frame(qubit))
                # if (
                #     measure_pulse_sequence := self._gate_calibrations.pulse_sequences[
                #         ("MEASURE", qubit)
                #     ]
                # ) is None:
                #     raise ValueError(
                #         "No pulse sequence for the measurement instruction was provided"
                #         " in the gate calibration set."
                #     )
                # pulse_sequence += measure_pulse_sequence

        # Result type columns
        (
            additional_result_types,
            _,
        ) = CircuitPulseSequenceBuilder._categorize_result_types(circuit.result_types)

        # Additional result types line on bottom
        if additional_result_types:
            print(f"\nAdditional result types: {', '.join(additional_result_types)}")

        return pulse_sequence

    def _readout_frame(self, qubit: QubitSet):
        if self._device.name == "Aspen-M-3":
            return self._device.frames[f"q{int(qubit)}_ro_rx_frame"]
        elif self._device.name == "Lucy":
            return self._device.frames[f"r{int(qubit)}_measure"]

    @staticmethod
    def _categorize_result_types(
        result_types: List[ResultType],
    ) -> Tuple[List[str], List[ResultType]]:
        """
        Categorize result types into result types with target and those without.

        Args:
            result_types (List[ResultType]): list of result types

        Returns:
            Tuple[List[str], List[ResultType]]: first element is a list of result types
            without `target` attribute; second element is a list of result types with
            `target` attribute
        """
        additional_result_types = []
        target_result_types = []
        for result_type in result_types:
            if hasattr(result_type, "target"):
                target_result_types.append(result_type)
            else:
                additional_result_types.extend(result_type.ascii_symbols)
        return additional_result_types, target_result_types
