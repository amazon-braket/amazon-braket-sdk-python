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
# language governing permissions and limitations under the License.

from typing import Optional, Union

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit, Gate, QubitSet
from braket.circuits.noise_model import NoiseModel
from braket.device_schema.pulse.pulse_device_action_properties_v1 import (  # noqa TODO: Remove device_action module once this is added to init in the schemas repo
    PulseDeviceActionProperties,
)
from braket.devices import LocalSimulator
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.pulse import PulseSequence
from braket.emulation.emulated_aws_quantum_task import EmulatedAwsQuantumTask
from braket.emulation.emulated_aws_quantum_task_batch import EmulatedAwsQuantumTaskBatch


class DeviceEmulator:
    def __init__(
            self,
            arn: str,
            aws_session,
            noise_model: Optional[NoiseModel] = None,
    ):
        self._device_arn = arn
        self._aws_session = aws_session
        self._noise_model = noise_model

    def run(
        self,
        task_specification: Union[
            Circuit,
            Problem,
            OpenQasmProgram,
            BlackbirdProgram,
            PulseSequence,
            AnalogHamiltonianSimulation,
        ],
        s3_destination_folder: Optional[AwsSession.S3DestinationFolder] = None,
        shots: Optional[int] = None,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: Optional[float] = None,
        inputs: Optional[dict[str, float]] = None,
        gate_definitions: Optional[dict[tuple[Gate, QubitSet], PulseSequence]] = None,
        reservation_arn: str | None = None,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> EmulatedAwsQuantumTask:
        local_sim = LocalSimulator("braket_dm" if self._noise_model else "default", noise_model=self._noise_model)
        local_task = local_sim.run(
            task_specification=task_specification,
            shots=shots,
            inputs=inputs,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs
        )
        return EmulatedAwsQuantumTask(local_task)

    def run_batch(
        self,
        task_specifications: Union[
            Union[
                Circuit, Problem, OpenQasmProgram, BlackbirdProgram, AnalogHamiltonianSimulation],
            list[
                Union[
                    Circuit, Problem, OpenQasmProgram, BlackbirdProgram, AnalogHamiltonianSimulation
                ]
            ],
        ],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int,
        max_parallel: int,
        max_workers: int = 0,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        inputs: Union[dict[str, float], list[dict[str, float]]] | None = None,
        reservation_arn: str | None = None,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> EmulatedAwsQuantumTaskBatch:
        local_sim = LocalSimulator("braket_dm" if self._noise_model else "default", noise_model=self._noise_model)
        local_task_batch = local_sim.run_batch(
            task_specifications=task_specifications,
            shots=shots,
            inputs=inputs,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs
        )
        return EmulatedAwsQuantumTaskBatch(local_task_batch)
