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

from typing import Optional, Union

from pydantic.v1 import BaseModel

from braket.ir.ahs import Program as AHSProgram
from braket.ir.annealing import Problem
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.jaqcd import Program as JaqcdProgram
from braket.ir.openqasm import Program as OpenQASMProgram
from braket.task_result.dwave_metadata_v1 import DwaveMetadata
from braket.task_result.ionq_metadata_v1 import IonQMetadata
from braket.task_result.iqm_metadata_v1 import IqmMetadata
from braket.task_result.oqc_metadata_v1 import OqcMetadata
from braket.task_result.quera_metadata_v1 import QueraMetadata
from braket.task_result.rigetti_metadata_v1 import RigettiMetadata
from braket.task_result.simulator_metadata_v1 import SimulatorMetadata
from braket.task_result.xanadu_metadata_v1 import XanaduMetadata


class AdditionalMetadata(BaseModel):
    """
    The additional metadata result schema.

    Attributes:
        action (Union[Program, Problem]): The action of the task
        dwaveMetadata (Optional[DWaveMetadata]): Additional metadata for tasks that ran on D-Wave
            devices. Default: None.
        ionqMetadata (Optional[IonQMetadata): Additional metadata for tasks that ran on IonQ
            devices. Default: None.
        rigettiMetadata (Optional[RigettiMetadata): Additional metadata for tasks that ran on
            Rigetti devices. Default: None.
        oqcMetadata (Optional[OqcMetadata): Additional metadata for tasks that ran on Oxforc Quantum
            Computing devices. Default: None.
        xanaduMetadata (Optional[XanaduMetadata): Additional metadata for tasks that ran on Xanadu
            devices. Default: None.
        queraMetadata (Optional[QueraMetadata): Additional metadata for tasks that ran on QuEra
            devices. Default: None.
        simulatorMetadata (Optional[SimulatorQMetadata): Additional metadata for tasks that ran on
            simulator devices. Default: None.
        iqmMetadata (Optional[IqmMetadata): Additional metadata for tasks that ran on IQM.

    Examples:
        >>> AdditionalMetadata(action=OpenQASMProgram(source='OPENQASM3.0; cx $0, $1'))
    """

    action: Union[JaqcdProgram, OpenQASMProgram, BlackbirdProgram, Problem, AHSProgram]
    dwaveMetadata: Optional[DwaveMetadata]
    ionqMetadata: Optional[IonQMetadata]
    rigettiMetadata: Optional[RigettiMetadata]
    oqcMetadata: Optional[OqcMetadata]
    xanaduMetadata: Optional[XanaduMetadata]
    queraMetadata: Optional[QueraMetadata]
    simulatorMetadata: Optional[SimulatorMetadata]
    iqmMetadata: Optional[IqmMetadata]
