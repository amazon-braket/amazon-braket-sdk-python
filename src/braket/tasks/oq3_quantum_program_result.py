from collections import Counter
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from braket.schema_common import BraketSchemaHeader
from braket.task_result import AdditionalMetadata, ResultTypeValue, TaskMetadata
from braket.task_result.oq3_program_result_v1 import OQ3ProgramResult


@dataclass
class OQ3QuantumProgramResult:
    _OQ3_PROGRAM_RESULT_HEADER = BraketSchemaHeader(
        name="braket.task_result.oq3_program_result", version="1"
    )
    task_metadata: TaskMetadata
    additional_metadata: AdditionalMetadata
    output_variables: Dict[str, np.ndarray] = None
    result_types: List[ResultTypeValue] = None

    measurements: np.ndarray = None
    measured_qubits: List[int] = None
    measurement_counts: Counter = None

    @staticmethod
    def measurement_counts_from_measurements(measurements: np.ndarray) -> Counter:
        """
        Creates measurement counts from measurements

        Args:
            measurements (numpy.ndarray): 2d array - row is shot and column is qubit.

        Returns:
            Counter: A Counter of measurements. Key is the measurements in a big endian binary
                string. Value is the number of times that measurement occurred.
        """
        bitstrings = []
        for j in range(len(measurements)):
            bitstrings.append("".join([str(element) for element in measurements[j]]))
        return Counter(bitstrings)

    @staticmethod
    def from_object(result: OQ3ProgramResult):
        """
        Create GateModelQuantumTaskResult from GateModelTaskResult object.

        Args:
            result (GateModelTaskResult): GateModelTaskResult object

        Returns
            GateModelQuantumTaskResult: A GateModelQuantumTaskResult based on the given dict

        Raises:
            ValueError: If neither "Measurements" nor "MeasurementProbabilities" is a key
                in the result dict
        """
        program_result = OQ3QuantumProgramResult(
            task_metadata=result.taskMetadata,
            additional_metadata=result.additionalMetadata,
            output_variables={
                var_name: np.array(values) for var_name, values in result.outputVariables.items()
            },
            result_types=result.resultTypes
        )

        # if result.measurements:
        #     program_result.measurements = np.asarray(result.measurements, dtype=int)
        #     m_counts = OQ3QuantumProgramResult.measurement_counts_from_measurements(program_result.measurements)
        #     program_result.measurement_counts = m_counts

        return program_result
