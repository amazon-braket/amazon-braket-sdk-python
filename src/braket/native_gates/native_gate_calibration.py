from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from braket.circuits.angled_gate import AngledGate
from braket.circuits.gate import Gate
from braket.circuits.qubit_set import QubitSet
from braket.pulse.pulse_sequence import PulseSequence


class NativeGateCalibration:
    """
    A collection of gate calibrations for a QPU with the timestamp of when the data was collected.
    """

    def __init__(
        self,
        calibration_json: Dict[Tuple[Gate, QubitSet], PulseSequence],
        fidelities: Dict[Tuple[Gate, QubitSet], float] = {},
    ):
        self._calibration_data = calibration_json
        self._fidelities = fidelities

    @property
    def calibration_data(self):
        """
        Gets the calibration data from the object.

        Returns:
            Dict[Tuple[Gate, QubitSet], PulseSequence]: The calibration data Dictionary.
        """
        return self._calibration_data

    def __len__(self):
        return len(self._calibration_data)

    def filter_data(
        self, gates: Optional[List[Gate]] = None, qubits: Optional[QubitSet] = None
    ) -> NativeGateCalibration:
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

    def get_pulse_sequence(self, key: Tuple[Gate, QubitSet]) -> PulseSequence:
        """
        Returns the pulse implementation for the gate and QubitSet.

        Args:
            key (Tuple[Gate,QubitSet])): A key to get a specific PulseSequence.

        Returns:
            PulseSequence: the PulseSequence object corresponding the gate acting on the QubitSet.

        """
        return self._calibration_data.get(key, None)

    def get_fidelity(self, key: Tuple[Gate, QubitSet]) -> PulseSequence:
        """
        Returns the fidelity for the gate and QubitSet that has been computed by the provider.

        Args:
            key (Tuple[Gate,QubitSet])): A key to get a specific fidelity.

        Returns:
            float: the fidelity measured for the gate acting on the QubitSet.

        """
        return self._fidelities.get(key, None)

    def to_defcal(self, key: Optional[Tuple[Gate, QubitSet]] = None) -> str:
        """
        Returns the defcal representation for the `NativeGateCalibration` object.

        Args:
            key (Optional[Tuple[Gate,QubitSet]])): An optional key to get a specific defcal.
                Default: None

        Returns:
            str: the defcal string for the object.

        """
        if key is not None:
            return self.calibration_data[key].to_ir().replace("cal", self._def_cal_gate(key), 1)
        else:
            defcal = "\n".join(
                v.to_ir().replace("cal", self._def_cal_gate(k), 1)
                for (k, v) in self.calibration_data.items()
                if isinstance(v, PulseSequence)
            )
            return defcal

    def _def_cal_gate(self, gate_key: Tuple[Gate, QubitSet]) -> str:
        gate_to_qasm = gate_key[0]._qasm_name
        if isinstance(gate_key[0], AngledGate):
            gate_to_qasm += f"(angle {gate_key[0].angle})"
        qubit_to_qasm = " ".join([f"${int(q)}" for q in gate_key[1]])
        return " ".join(["defcal", gate_to_qasm, qubit_to_qasm])
