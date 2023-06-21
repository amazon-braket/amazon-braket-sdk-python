from __future__ import annotations

from braket.pulse.pulse_sequence import PulseSequence
from braket.circuits.qubit_set import QubitSet
from braket.circuits.gate import Gate

from typing import Dict, List, Optional, Tuple


class NativeGateCalibration:
    """
    A collection of gate calibrations for a QPU with the timestamp of when the data was collected.
    """

    def __init__(self, calibration_json: Dict[Tuple[Gate, QubitSet], PulseSequence]):
        self._calibration_data = calibration_json

    @property
    def calibration_date(self):
        """
        Gets the calibration data from the object.

        Returns:
            Dict[Tuple[Gate, QubitSet], PulseSequence]: The calibration data Dictionary.
        """
        return self._calibration_data

    def filter_data(
            self,
            gates: Optional[List[Gate]] = None,
            qubits: Optional[QubitSet] = None) -> NativeGateCalibration:
        """
        Filters the data based on optional lists of gates or QubitSets.

        Args:
            gates (Optional[List[Gate]]): An optional list of gates to filter on.
            qubits (Optional[QubitSet]): An optional set of qubits to filter on.

        Returns:
            A filtered NativeGateCalibration object.
        """
        keys = self._calibration_data.keys()
        filtered_calibration_keys = [tup for tup in keys if any(i in tup for i in gates or qubits)]
        return NativeGateCalibration(
            {k: v for (k, v) in self.calibration_data.items() if filtered_calibration_keys in k}
        )

    def to_defcal(self, key: [Optional[Tuple[Gate, QubitSet]]] = None) -> str:
        """
        Returns the defcal representation for the `NativeGateCalibration` object.




