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
        calibration_data: Dict[Tuple[Gate, QubitSet], PulseSequence],
    ):
        """
        Args:
            calibration_data (Dict[Tuple[Gate, QubitSet], PulseSequence]): A mapping containing a key of
                `(Gate, QubitSet)` mapped to the corresponding pulse sequence.

        """  # noqa: E501
        self._calibration_data = calibration_data

    @property
    def calibration_data(self) -> Dict[Tuple[Gate, QubitSet], PulseSequence]:
        """
        Gets the mapping of (Gate, Qubit) to the corresponding `PulseSequences`.

        Returns:
            Dict[Tuple[Gate, QubitSet], PulseSequence]: The calibration data Dictionary.
        """
        return self._calibration_data

    def copy(self) -> GateCalibrations:
        """
        Returns a copy of the object.

        Returns:
            GateCalibrations: a copy of the calibrations.
        """
        return GateCalibrations(deepcopy(self._calibration_data))

    def __len__(self):
        return len(self._calibration_data)

    def filter_by_qubits_or_gates(
        self, gates: Optional[List[Gate]] = None, qubits: Optional[List[QubitSet]] = None
    ) -> Optional[GateCalibrations]:
        """
        Filters the data based on optional lists of gates or QubitSets.

        Args:
            gates (Optional[List[Gate]]): An optional list of gates to filter on.
            qubits (Optional[List[QubitSet]]): An optional set of qubits to filter on.

        Returns:
            Optional[GateCalibrations]: A filtered GateCalibrations object. Otherwise, returns
            none if no matches are found.
        """  # noqa: E501
        keys = self._calibration_data.keys()
        filtered_calibration_keys = [
            tup
            for tup in keys
            if isinstance(tup, tuple) and any(i in set(tup) for i in gates or qubits)
        ]
        return GateCalibrations(
            {k: v for (k, v) in self.calibration_data.items() if k in filtered_calibration_keys},
        )

    def get_gate_calibration(
        self, calibration_key: Tuple[Gate, QubitSet]
    ) -> Optional[PulseSequence]:
        """
        Returns the pulse implementation for the gate and QubitSet.

        Args:
            calibration_key (Tuple[Gate, QubitSet]): A key to get a specific PulseSequence.

        Returns:
            Optional[PulseSequence]: the PulseSequence object corresponding the gate acting on
            the QubitSet.

        """
        if not isinstance(calibration_key[0], Gate) or not isinstance(calibration_key[1], QubitSet):
            raise ValueError("The key must be a tuple of a gate object and a qubit set.")
        return self._calibration_data.get(calibration_key, None)

    def to_ir(self, key: Optional[Tuple[Gate, QubitSet]] = None) -> str:
        """
        Returns the defcal representation for the `GateCalibrations` object.

        Args:
            key (Optional[Tuple[Gate, QubitSet]]): An optional key to get a specific defcal.
                Default: None

        Returns:
            str: the defcal string for the object.

        """
        if key is not None:
            if key not in self.calibration_data.keys():
                raise ValueError(f"The key {key} does not exist in this GateCalibrations object.")
            return self.calibration_data[key].to_ir().replace("cal", self._def_cal_gate(key), 1)
        else:
            defcal = "\n".join(
                v.to_ir().replace("cal", self._def_cal_gate(k), 1)
                for (k, v) in self.calibration_data.items()
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
        return (
            isinstance(other, GateCalibrations) and other.calibration_data == self.calibration_data
        )
