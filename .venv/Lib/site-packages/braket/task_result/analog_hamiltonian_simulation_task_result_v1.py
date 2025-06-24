# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License

from typing import Optional

from pydantic.v1 import BaseModel, Field, conint, conlist, constr

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader
from braket.task_result.additional_metadata import AdditionalMetadata
from braket.task_result.task_metadata_v1 import TaskMetadata


class AnalogHamiltonianSimulationShotMetadata(BaseModel):
    """
    The analog hamiltonian simulation shot metadata schema.

    Attributes:
        shotStatus (str): The status of the shot.
    """

    shotStatus: constr(min_length=1)


class AnalogHamiltonianSimulationShotResult(BaseModel):
    """
    The analog hamiltonian simulation shot result schema.

    Attributes:
        preSequence (Optional[conlist(conint(ge=0, le=1), min_items=1)]): Pre-sequence measurement
            bits (one for each atomic site) for each shot: 0 if site is empty, 1 if site is filled,
            measured before the sequences of pulses that run the quantum evolution
        postSequence (Optional[conlist(conint(ge=0, le=1), min_items=1)]): Post-sequence
            measurement bits for each shot: 0 if atom is in Rydberg state or site is empty, 1 if
            atom is in ground state, measured at the end of the sequences of pulses that run the
            quantum evolution
    """

    preSequence: Optional[conlist(conint(ge=0, le=1), min_items=1)]
    postSequence: Optional[conlist(conint(ge=0, le=1), min_items=1)]


class AnalogHamiltonianSimulationShotMeasurement(BaseModel):
    """
    The analog hamiltonian simulation shot measurement schema.

    Attributes:
        shotMetadata (AnalogHamiltonianSimulationShotMetadata): The analog hamiltonian simulation
            shot metadata schema.
        shotResult (AnalogHamiltonianSimulationShotResult): The analog hamiltonian simulation shot
            result schema.
    """

    shotMetadata: AnalogHamiltonianSimulationShotMetadata
    shotResult: AnalogHamiltonianSimulationShotResult


class AnalogHamiltonianSimulationTaskResult(BraketSchemaBase):
    """
    The Analog Hamiltonian Simulation task result schema

    Attributes:
        braketSchemaHeader (BraketSchemaHeader): Schema header. Users do not need
            to set this value. Only default is allowed.
        taskMetadata (TaskMetadata): The task metadata
        measurements (list[AnalogHamiltonianSimulationShotMeasurement]): List of measurements for
            each shot.
    """

    _AHS_TASK_RESULT_HEADER = BraketSchemaHeader(
        name="braket.task_result.analog_hamiltonian_simulation_task_result", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(
        default=_AHS_TASK_RESULT_HEADER, const=_AHS_TASK_RESULT_HEADER
    )
    taskMetadata: TaskMetadata
    measurements: Optional[list[AnalogHamiltonianSimulationShotMeasurement]]
    additionalMetadata: Optional[AdditionalMetadata]
