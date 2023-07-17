from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from braket.circuits.gate import Gate
from braket.circuits.qubit_set import QubitSet
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)
from braket.pulse.pulse_sequence import PulseSequence


class GateCalibrations:
    """
    An object containing gate calibration data. The data respresents the mapping on a particular gate
    on a set of qubits to its calibration to be used by a quantum device. This is represented by a dictionary
    with keys of `Tuple(Gate, QubitSet)` mapped to a `PulseSequence`.
    """  # noqa: E501

    def __init__(
        self,
        pulse_sequences: Dict[Tuple[Gate, QubitSet], PulseSequence],
    ):
        """
        Args:
            pulse_sequences (Dict[Tuple[Gate, QubitSet], PulseSequence]): A mapping containing a key of
                `(Gate, QubitSet)` mapped to the corresponding pulse sequence.

        """  # noqa: E501
        self._pulse_sequences = pulse_sequences

    @property
    def pulse_sequences(self) -> Dict[Tuple[Gate, QubitSet], PulseSequence]:
        """
        Gets the mapping of (Gate, Qubit) to the corresponding `PulseSequence`.

        Returns:
            Dict[Tuple[Gate, QubitSet], PulseSequence]: The calibration data Dictionary.
        """
        return self._pulse_sequences

    def copy(self) -> GateCalibrations:
        """
        Returns a copy of the object.

        Returns:
            GateCalibrations: a copy of the calibrations.
        """
        return GateCalibrations(deepcopy(self._pulse_sequences))

    def __len__(self):
        return len(self._pulse_sequences)

    def filter_pulse_sequences(
        self, gates: Optional[List[Gate]] = None, qubits: Optional[QubitSet] = None
    ) -> Optional[GateCalibrations]:
        """
        Filters the data based on optional lists of gates and QubitSets.

        Args:
            gates (Optional[List[Gate]]): An optional list of gates to filter on.
            qubits (Optional[QubitSet]): An optional `QubitSet` to filter on.

        Returns:
            Optional[GateCalibrations]: A filtered GateCalibrations object. Otherwise, returns
            none if no matches are found.
        """  # noqa: E501
        keys = self.pulse_sequences.keys()
        filtered_calibration_keys = [
            tup
            for tup in keys
            if (gates is None or tup[0] in gates) and (qubits is None or qubits.issubset(tup[1]))
        ]
        return GateCalibrations(
            {k: v for (k, v) in self.pulse_sequences.items() if k in filtered_calibration_keys},
        )

    def to_ir(self, calibration_key: Optional[Tuple[Gate, QubitSet]] = None) -> str:
        """
        Returns the defcal representation for the `GateCalibrations` object.

        Args:
            calibration_key (Optional[Tuple[Gate, QubitSet]]): An optional key to get a specific defcal.
                Default: None

        Returns:
            str: the defcal string for the object.

        """  # noqa: E501
        if calibration_key is not None:
            if calibration_key not in self.pulse_sequences.keys():
                raise ValueError(
                    f"The key {calibration_key} does not exist in this GateCalibrations object."
                )
            return (
                self.pulse_sequences[calibration_key]
                .to_ir()
                .replace("cal", self._def_cal_gate(calibration_key), 1)
            )
        else:
            defcal = "\n".join(
                v.to_ir().replace("cal", self._def_cal_gate(k), 1)
                for (k, v) in self.pulse_sequences.items()
                if isinstance(v, PulseSequence)
            )
            return defcal

    def _def_cal_gate(self, gate_key: Tuple[Gate, QubitSet]) -> str:
        return " ".join(
            [
                "defcal",
                gate_key[0].to_ir(
                    target=gate_key[1],
                    serialization_properties=OpenQASMSerializationProperties(
                        QubitReferenceType.PHYSICAL
                    ),
                    ir_type=IRType.OPENQASM,
                )[:-1],
            ]
        )

    def __eq__(self, other):
        return isinstance(other, GateCalibrations) and other.pulse_sequences == self.pulse_sequences
