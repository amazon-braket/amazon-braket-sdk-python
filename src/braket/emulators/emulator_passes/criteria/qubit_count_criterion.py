from braket.emulators.emulator_passes.criteria import EmulatorCriterion
from braket.circuits import Circuit 


class QubitCountCriterion(EmulatorCriterion):
    """
    A simple criterion class that checks that an input program does not use more qubits
    than available on a device, as set during this criterion's instantiation.
    """
    def __init__(self, qubit_count: int):
        self._qubit_count = qubit_count
        
        
    def validate(self, circuit: Circuit) -> Circuit:
        if circuit.qubit_count > self._qubit_count:
            raise ValueError(f"Circuit must use at most {self._qubit_count} qubits, but uses {circuit.qubit_count} qubits.")

    def __eq__(self, other: EmulatorCriterion) -> bool:
        return isinstance(other, QubitCountCriterion) and \
               self._qubit_count == other._qubit_count