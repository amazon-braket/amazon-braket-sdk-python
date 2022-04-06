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
        return OQ3QuantumProgramResult(
            task_metadata=result.taskMetadata,
            additional_metadata=result.additionalMetadata,
            output_variables={
                var_name: np.array(values) for var_name, values in result.outputVariables.items()
            },
            result_types=result.resultTypes,
        )
