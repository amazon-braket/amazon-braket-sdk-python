from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from braket.circuits.angled_gate import AngledGate
from braket.circuits.gate import Gate
from braket.circuits.qubit_set import QubitSet
from braket.pulse.pulse_sequence import PulseSequence


class GateCalibrations:
    """
    An object containing gate fidelities and calibration data.

    Args:
        calibration_data (Dict[Tuple[Gate, QubitSet], PulseSequence]): A mapping containing a key of
            `(Gate, QubitSet)` mapped to the corresponding pulse sequence.
        fidelities  Optional[Dict[Tuple[Gate, QubitSet], float]]: Gate fidelities.
    """

    def __init__(
        self,
        calibration_data: Dict[Tuple[Gate, QubitSet], PulseSequence],
        fidelities: Optional[Dict[Tuple[Gate, QubitSet], float]] = None,
    ):
        self._calibration_data = calibration_data
        self._fidelities = fidelities

    @property
    def calibration_data(self) -> Dict[Tuple[Gate, QubitSet], PulseSequence]:
        """
        Gets the mapping of (Gate, Qubit) to the corresponding `PulseSequences`.

        Returns:
            Dict[Tuple[Gate, QubitSet], PulseSequence]: The calibration data Dictionary.
        """
        return self._calibration_data

    @property
    def fidelities(self) -> Dict[Tuple[Gate, QubitSet], float]:
        """
        Gets the mapping of (Gate, Qubit) to the corresponding fidelity.

        Returns:
            Dict[Tuple[Gate, QubitSet], float]: The fidelity data.
        """
        if self._fidelities:
            return self._fidelities
        return None

    def copy(self) -> GateCalibrations:
        """
        Returns a copy of the object.

        Returns:
            GateCalibrations: a copy of the calibrations.
        """
        return GateCalibrations(deepcopy(self._calibration_data), deepcopy(self._fidelities))

    def __len__(self):
        return len(self._calibration_data)

    def filter_data(
        self, gates: Optional[List[Gate]] = None, qubits: Optional[List[QubitSet]] = None
    ) -> Optional[GateCalibrations]:
        """
        Filters the data based on optional lists of gates or QubitSets.

        Args:
            gates (Optional[List[Gate]]): An optional list of gates to filter on.
            qubits (Optional[List[QubitSet]]): An optional set of qubits to filter on.

        Returns:
            Optional[GateCalibrations]: A filteredGateCalibrations object. Otherwise, returns none if no matches are found.
        """  # noqa: E501
        keys = self._calibration_data.keys()
        filtered_calibration_keys = [
            tup
            for tup in keys
            if isinstance(tup, tuple) and any(i in set(tup) for i in gates or qubits)
        ]
        if self._fidelities is None:
            return GateCalibrations(
                {
                    k: v
                    for (k, v) in self.calibration_data.items()
                    if k in filtered_calibration_keys
                },
                None,
            )
        return GateCalibrations(
            {k: v for (k, v) in self.calibration_data.items() if k in filtered_calibration_keys},
            {k: v for (k, v) in self._fidelities.items() if k in filtered_calibration_keys},
        )

    def get_pulse_sequence(self, key: Tuple[Gate, QubitSet]) -> PulseSequence:
        """
        Returns the pulse implementation for the gate and QubitSet.

        Args:
            key (Tuple[Gate, QubitSet]): A key to get a specific PulseSequence.

        Returns:
            PulseSequence: the PulseSequence object corresponding the gate acting on the QubitSet.

        """
        if not isinstance(key[0], Gate) or not isinstance(key[1], QubitSet):
            raise ValueError("The key must be a tuple of a gate object and a qubit set.")
        return self._calibration_data.get(key, None)

    def get_fidelity(self, key: Tuple[Gate, QubitSet]) -> float:
        """
        Returns the fidelity for the gate and QubitSet that has been computed by the provider.

        Args:
            key (Tuple[Gate, QubitSet]): A key to get a specific fidelity.

        Returns:
            float: the fidelity measured for the gate acting on the QubitSet.

        """
        if self._fidelities:
            return self._fidelities.get(key, None)
        return None

    def to_defcal(self, key: Optional[Tuple[Gate, QubitSet]] = None) -> str:
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
        gate_to_qasm = gate_key[0]._qasm_name
        if isinstance(gate_key[0], AngledGate):
            gate_to_qasm += f"(angle {gate_key[0].angle})"
        qubit_to_qasm = " ".join([f"${int(q)}" for q in gate_key[1]])
        return " ".join(["defcal", gate_to_qasm, qubit_to_qasm])

    def __eq__(self, other):
        return (
            isinstance(other, GateCalibrations)
            and other.calibration_data == self.calibration_data
            and other.fidelities == self.fidelities
        )
