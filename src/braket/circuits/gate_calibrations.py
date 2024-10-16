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

from copy import deepcopy
from typing import Any

from braket.circuits.gate import Gate
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)
from braket.pulse.pulse_sequence import PulseSequence
from braket.registers.qubit_set import QubitSet


class GateCalibrations:
    """An object containing gate calibration data. The data represents the mapping on a particular
    gate on a set of qubits to its calibration to be used by a quantum device. This is represented
    by a dictionary with keys of `Tuple(Gate, QubitSet)` mapped to a `PulseSequence`.
    """

    def __init__(
        self,
        pulse_sequences: dict[tuple[Gate, QubitSet], PulseSequence],
    ):
        """Inits a `GateCalibrations`.

        Args:
            pulse_sequences (dict[tuple[Gate, QubitSet], PulseSequence]): A mapping containing a key
                of `(Gate, QubitSet)` mapped to the corresponding pulse sequence.

        """
        self.pulse_sequences: dict[tuple[Gate, QubitSet], PulseSequence] = pulse_sequences

    @property
    def pulse_sequences(self) -> dict[tuple[Gate, QubitSet], PulseSequence]:
        """Gets the mapping of (Gate, Qubit) to the corresponding `PulseSequence`.

        Returns:
            dict[tuple[Gate, QubitSet], PulseSequence]: The calibration data Dictionary.
        """
        return self._pulse_sequences

    @pulse_sequences.setter
    def pulse_sequences(self, value: Any) -> None:
        """Sets the mapping of (Gate, Qubit) to the corresponding `PulseSequence`.

        Args:
            value(Any): The value for the pulse_sequences property to be set to.

        Raises:
            TypeError: Raised if the type is not dict[tuple[Gate, QubitSet], PulseSequence]

        """
        if isinstance(value, dict) and all(
            isinstance(k[0], Gate) and isinstance(k[1], QubitSet) and isinstance(v, PulseSequence)
            for (k, v) in value.items()
        ):
            self._pulse_sequences = value
        else:
            raise TypeError(
                "The value for pulse_sequence must be of type: "
                "dict[tuple[Gate, QubitSet], PulseSequence]"
            )

    def copy(self) -> GateCalibrations:
        """Returns a copy of the object.

        Returns:
            GateCalibrations: a copy of the calibrations.
        """
        return GateCalibrations(deepcopy(self._pulse_sequences))

    def __len__(self):
        return len(self._pulse_sequences)

    def filter(
        self,
        gates: list[Gate] | None = None,
        qubits: QubitSet | list[QubitSet] | None = None,
    ) -> GateCalibrations:
        """Filters the data based on optional lists of gates and QubitSets.

        Args:
            gates (list[Gate] | None): An optional list of gates to filter on.
            qubits (QubitSet | list[QubitSet] | None): An optional `QubitSet` or
                list of `QubitSet` to filter on.

        Returns:
            GateCalibrations: A filtered GateCalibrations object.
        """
        keys = self.pulse_sequences.keys()
        if isinstance(qubits, QubitSet):
            qubits = [qubits]
        filtered_calibration_keys = [
            tup
            for tup in keys
            if (gates is None or tup[0] in gates)
            and (qubits is None or any(qset.issubset(tup[1]) for qset in qubits))
        ]
        return GateCalibrations(
            {k: v for (k, v) in self.pulse_sequences.items() if k in filtered_calibration_keys},
        )

    def to_ir(self, calibration_key: tuple[Gate, QubitSet] | None = None) -> str:
        """Returns the defcal representation for the `GateCalibrations` object.

        Args:
            calibration_key (tuple[Gate, QubitSet] | None): An optional key to get a
                specific defcal. Default: None

        Raises:
            ValueError: Key does not exist in the `GateCalibrations` object.

        Returns:
            str: the defcal string for the object.

        """
        if calibration_key is not None:
            if calibration_key not in self.pulse_sequences:
                raise ValueError(
                    f"The key {calibration_key} does not exist in this GateCalibrations object."
                )
            return (
                self.pulse_sequences[calibration_key]
                .to_ir()
                .replace("cal", self._def_cal_gate(calibration_key), 1)
            )
        return "\n".join(
            v.to_ir().replace("cal", self._def_cal_gate(k), 1)
            for (k, v) in self.pulse_sequences.items()
        )

    def _def_cal_gate(self, gate_key: tuple[Gate, QubitSet]) -> str:
        return " ".join([
            "defcal",
            gate_key[0].to_ir(
                target=gate_key[1],
                serialization_properties=OpenQASMSerializationProperties(
                    QubitReferenceType.PHYSICAL
                ),
                ir_type=IRType.OPENQASM,
            )[:-1],
        ])

    def __eq__(self, other: GateCalibrations):
        return isinstance(other, GateCalibrations) and other.pulse_sequences == self.pulse_sequences
