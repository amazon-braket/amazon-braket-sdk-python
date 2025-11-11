from braket.emulation.passes import ValidationPass
from braket.tasks.quantum_task import TaskSpecification


class SpecificationValidator(ValidationPass):
    def __init__(self, device_supported_specifications: TaskSpecification):
        """
        A validator that checks whether or not the device supports the Specification.

        Args:
            device_supported_specifications (TaskSpecification): 
                The device.properties.action dictionary.

        Raises:
            ValueError: The task specification is not supported.
        """
        self.device_supported_specifications = device_supported_specifications
        self._supported_specifications = TaskSpecification

    def validate(self, circuit: TaskSpecification) -> None:
        """
        Checks that the number of qubits used in this circuit does not exceed this
        validator's qubit_count max.

        Args:
            circuit (Circuit): The Braket circuit whose qubit count to validate.

        Raises:
            ValueError: If the number of qubits used in the circuit exceeds the qubit_count.

        """
        if not isinstance(circuit, self.device_supported_specifications):
            raise ValueError(  # noqa: TRY004
                f"{type(circuit)} not in supported specifications: {
                    self.device_supported_specifications}"
                )
