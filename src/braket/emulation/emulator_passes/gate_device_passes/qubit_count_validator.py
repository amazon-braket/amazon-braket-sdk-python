from braket.circuits import Circuit
from braket.emulation.emulator_passes.validation_pass import ValidationPass


class QubitCountValidator(ValidationPass[Circuit]):
    """
    A simple validator class that checks that an input program does not use more qubits
    than available on a device, as set during this validator's instantiation.
    """

    def __init__(self, qubit_count: int):
        if qubit_count <= 0:
            raise ValueError(f"qubit_count ({qubit_count}) must be a positive integer.")
        self._qubit_count = qubit_count

    def validate(self, circuit: Circuit) -> None:
        """
        Checks that the number of qubits used in this circuit does not exceed this
        validator's qubit_count max.

        Args:
            circuit (Circuit): The Braket circuit whose qubit count to validate.

        Raises:
            ValueError: If the number of qubits used in the circuit exceeds the qubit_count.

        """
        if circuit.qubit_count > self._qubit_count:
            raise ValueError(
                f"Circuit must use at most {self._qubit_count} qubits, \
but uses {circuit.qubit_count} qubits."
            )

    def __eq__(self, other: ValidationPass) -> bool:
        return isinstance(other, QubitCountValidator) and self._qubit_count == other._qubit_count
