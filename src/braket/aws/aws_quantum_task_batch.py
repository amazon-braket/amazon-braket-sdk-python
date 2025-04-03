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

from __future__ import annotations

import time
from concurrent.futures.thread import ThreadPoolExecutor
from itertools import repeat
from typing import TYPE_CHECKING, Any, Optional

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing import Problem
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit
from braket.circuits.gate import Gate
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.pulse.pulse_sequence import PulseSequence
from braket.registers.qubit_set import QubitSet
from braket.tasks.quantum_task_batch import QuantumTaskBatch

if TYPE_CHECKING:
    from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
        AnalogHamiltonianSimulationQuantumTaskResult,
    )
    from braket.tasks.annealing_quantum_task_result import AnnealingQuantumTaskResult
    from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult
    from braket.tasks.photonic_model_quantum_task_result import PhotonicModelQuantumTaskResult


class AwsQuantumTaskBatch(QuantumTaskBatch):
    """Executes a batch of quantum tasks in parallel.

    Using this class can yield vast speedups over executing quantum tasks sequentially,
    and is particularly useful for computations that can be parallelized,
    such as calculating quantum gradients or statistics of terms in a Hamiltonian.

    Note: there is no benefit to using this method with QPUs outside of their execution windows,
    since results will not be available until the window opens.
    """

    MAX_CONNECTIONS_DEFAULT = 100
    MAX_RETRIES = 3

    def __init__(
        self,
        aws_session: AwsSession,
        device_arn: str,
        task_specifications: Circuit
        | Problem
        | OpenQasmProgram
        | BlackbirdProgram
        | AnalogHamiltonianSimulation
        | list[
            Circuit | Problem | OpenQasmProgram | BlackbirdProgram | AnalogHamiltonianSimulation
        ],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int,
        max_parallel: int,
        max_workers: int = MAX_CONNECTIONS_DEFAULT,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        inputs: Optional[dict[str, float] | list[dict[str, float]]] = None,
        gate_definitions: (
            Optional[
                dict[tuple[Gate, QubitSet], PulseSequence]
                | list[dict[tuple[Gate, QubitSet], PulseSequence]]
            ]
        ) = None,
        reservation_arn: Optional[str] = None,
        *aws_quantum_task_args: Any,
        **aws_quantum_task_kwargs: Any,
    ):
        """Creates a batch of quantum tasks.

        Args:
            aws_session (AwsSession): AwsSession to connect to AWS with.
            device_arn (str): The ARN of the quantum device.
            task_specifications (Union[Union[Circuit,Problem,OpenQasmProgram,BlackbirdProgram,AnalogHamiltonianSimulation],list[Union[Circuit,Problem,OpenQasmProgram,BlackbirdProgram,AnalogHamiltonianSimulation]]]): # noqa
                Single instance or list of circuits, annealing
                problems, pulse sequences, or photonics program as specification of quantum task
                to run on device.
            s3_destination_folder (AwsSession.S3DestinationFolder): NamedTuple, with bucket
                for index 0 and key for index 1, that specifies the Amazon S3 bucket and folder
                to store quantum task results in.
            shots (int): The number of times to run the quantum task on the device. If the device is
                a simulator, this implies the state is sampled N times, where N = `shots`.
                `shots=0` is only available on simulators and means that the simulator
                will compute the exact results based on the quantum task specification.
            max_parallel (int): The maximum number of quantum tasks to run on AWS in parallel.
                Batch creation will fail if this value is greater than the maximum allowed
                concurrent quantum tasks on the device.
            max_workers (int): The maximum number of thread pool workers. Default: 100
            poll_timeout_seconds (float): The polling timeout for `AwsQuantumTask.result()`,
                in seconds. Default: 5 days.
            poll_interval_seconds (float): The polling interval for results in seconds.
                Default: 1 second.
            inputs (Union[dict[str, float], list[dict[str, float]]] | None): Inputs to be passed
                along with the IR. If the IR supports inputs, the inputs will be updated
                with this value. Default: {}.
            gate_definitions (Union[dict[tuple[Gate, QubitSet], PulseSequence], list[dict[tuple[Gate, QubitSet], PulseSequence]]] | None): # noqa: E501
                User-defined gate calibration. The calibration is defined for a particular `Gate` on a
                particular `QubitSet` and is represented by a `PulseSequence`. Default: None.
            reservation_arn (str | None): The reservation ARN provided by Braket Direct
                to reserve exclusive usage for the device to run the quantum task on.
                Note: If you are creating tasks in a job that itself was created reservation ARN,
                those tasks do not need to be created with the reservation ARN.
                Default: None.
            *aws_quantum_task_args (Any): Arbitrary args for `QuantumTask`.
            **aws_quantum_task_kwargs (Any): Arbitrary kwargs for `QuantumTask`.,
        """  # noqa: E501
        self._tasks = AwsQuantumTaskBatch._execute(
            aws_session,
            device_arn,
            task_specifications,
            s3_destination_folder,
            shots,
            max_parallel,
            max_workers,
            poll_timeout_seconds,
            poll_interval_seconds,
            inputs,
            gate_definitions,
            reservation_arn,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs,
        )
        self._aws_session = aws_session
        self._results = None
        self._unsuccessful = set()

        # Cache execution inputs for retries.
        self._device_arn = device_arn
        self._task_specifications = task_specifications
        self._s3_destination_folder = s3_destination_folder
        self._shots = shots
        self._max_parallel = max_parallel
        self._max_workers = max_workers
        self._poll_timeout_seconds = poll_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._inputs = inputs
        self._reservation_arn = reservation_arn
        self._aws_quantum_task_args = aws_quantum_task_args
        self._aws_quantum_task_kwargs = aws_quantum_task_kwargs

    @staticmethod
    def _tasks_inputs_gatedefs(
        task_specifications: Circuit
        | Problem
        | OpenQasmProgram
        | BlackbirdProgram
        | AnalogHamiltonianSimulation
        | list[
            Circuit | Problem | OpenQasmProgram | BlackbirdProgram | AnalogHamiltonianSimulation
        ],
        inputs: Optional[dict[str, float] | list[dict[str, float]]] = None,
        gate_definitions: Optional[
            dict[tuple[Gate, QubitSet], PulseSequence]
            | list[dict[tuple[Gate, QubitSet], PulseSequence]]
        ] = None,
    ) -> list[
        tuple[
            Circuit | Problem | OpenQasmProgram | BlackbirdProgram | AnalogHamiltonianSimulation,
            dict[str, float],
            dict[tuple[Gate, QubitSet], PulseSequence],
        ]
    ]:
        inputs = inputs or {}
        gate_definitions = gate_definitions or {}

        single_task_type = (
            Circuit,
            Problem,
            OpenQasmProgram,
            BlackbirdProgram,
            AnalogHamiltonianSimulation,
        )
        single_input_type = dict
        single_gate_definitions_type = dict

        args = [task_specifications, inputs, gate_definitions]
        single_arg_types = [single_task_type, single_input_type, single_gate_definitions_type]

        batch_length = 1
        arg_lengths = []
        for arg, single_arg_type in zip(args, single_arg_types):
            arg_length = 1 if isinstance(arg, single_arg_type) else len(arg)
            arg_lengths.append(arg_length)

            if arg_length != 1:
                if batch_length not in {1, arg_length}:
                    raise ValueError(
                        "Multiple inputs, task specifications and gate definitions must "
                        "be equal in length."
                    )
                batch_length = arg_length

        for i in range(len(arg_lengths)):
            if isinstance(args[i], (dict, single_task_type)):
                args[i] = repeat(args[i], batch_length)

        tasks_inputs_definitions = list(zip(*args))

        for task_specification, input_map, _gate_definitions in tasks_inputs_definitions:
            if isinstance(task_specification, Circuit):
                param_names = {param.name for param in task_specification.parameters}
                if unbounded_parameters := param_names - set(input_map.keys()):
                    raise ValueError(
                        f"Cannot execute circuit with unbound parameters: {unbounded_parameters}"
                    )

        return tasks_inputs_definitions

    @staticmethod
    def _execute(
        aws_session: AwsSession,
        device_arn: str,
        task_specifications: Circuit
        | Problem
        | OpenQasmProgram
        | BlackbirdProgram
        | AnalogHamiltonianSimulation
        | list[
            Circuit | Problem | OpenQasmProgram | BlackbirdProgram | AnalogHamiltonianSimulation
        ],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int,
        max_parallel: int,
        max_workers: int = MAX_CONNECTIONS_DEFAULT,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        inputs: Optional[dict[str, float] | list[dict[str, float]]] = None,
        gate_definitions: (
            Optional[
                dict[tuple[Gate, QubitSet], PulseSequence]
                | list[dict[tuple[Gate, QubitSet], PulseSequence]]
            ]
        ) = None,
        reservation_arn: Optional[str] = None,
        *args,
        **kwargs,
    ) -> list[AwsQuantumTask]:
        tasks_inputs_gatedefs = AwsQuantumTaskBatch._tasks_inputs_gatedefs(
            task_specifications, inputs, gate_definitions
        )
        max_threads = min(max_parallel, max_workers)
        remaining = [0 for _ in tasks_inputs_gatedefs]
        try:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                task_futures = [
                    executor.submit(
                        AwsQuantumTaskBatch._create_task,
                        remaining,
                        aws_session,
                        device_arn,
                        task,
                        s3_destination_folder,
                        shots,
                        poll_timeout_seconds=poll_timeout_seconds,
                        poll_interval_seconds=poll_interval_seconds,
                        inputs=input_map,
                        gate_definitions=gatedefs,
                        reservation_arn=reservation_arn,
                        *args,
                        **kwargs,
                    )
                    for task, input_map, gatedefs in tasks_inputs_gatedefs
                ]
        except KeyboardInterrupt:
            # If an exception is thrown before the thread pool has finished,
            # clean up the quantum tasks which have not yet been created before reraising it.
            if "task_futures" in locals():
                for future in task_futures:
                    future.cancel()

            # Signal to the workers that there is no mork work to do
            remaining.clear()

            raise
        return [future.result() for future in task_futures]

    @staticmethod
    def _create_task(
        remaining: list[int],
        aws_session: AwsSession,
        device_arn: str,
        task_specification: Circuit
        | Problem
        | OpenQasmProgram
        | BlackbirdProgram
        | AnalogHamiltonianSimulation,
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int,
        poll_interval_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        inputs: Optional[dict[str, float]] = None,
        gate_definitions: Optional[dict[tuple[Gate, QubitSet], PulseSequence]] = None,
        reservation_arn: str | None = None,
        *args,
        **kwargs,
    ) -> AwsQuantumTask:
        task = AwsQuantumTask.create(
            aws_session,
            device_arn,
            task_specification,
            s3_destination_folder,
            shots,
            poll_interval_seconds=poll_interval_seconds,
            inputs=inputs,
            gate_definitions=gate_definitions,
            reservation_arn=reservation_arn,
            *args,
            **kwargs,
        )

        remaining.pop()

        # If the quantum task hits a terminal state before all quantum tasks have been created,
        # it can be returned immediately
        while remaining and task.state() not in AwsQuantumTask.TERMINAL_STATES:
            time.sleep(poll_interval_seconds)
        return task

    def results(
        self,
        fail_unsuccessful: bool = False,
        max_retries: int = MAX_RETRIES,
        use_cached_value: bool = True,
    ) -> list[
        GateModelQuantumTaskResult
        | AnnealingQuantumTaskResult
        | PhotonicModelQuantumTaskResult
        | AnalogHamiltonianSimulationQuantumTaskResult
    ]:
        """Retrieves the result of every quantum task in the batch.

        Polling for results happens in parallel; this method returns when all quantum tasks
        have reached a terminal state. The result of this method is cached.

        Args:
            fail_unsuccessful (bool): If set to `True`, this method will fail
                if any quantum task in the batch fails to return a result even after
                `max_retries` retries.
            max_retries (int): Maximum number of times to retry any failed quantum tasks,
                i.e. any quantum tasks in the `FAILED` or `CANCELLED` state or that didn't
                complete within the timeout. Default: 3.
            use_cached_value (bool): If `False`, will refetch the results from S3,
                even when results have already been cached. Default: `True`.

        Returns:
            list[GateModelQuantumTaskResult | AnnealingQuantumTaskResult | PhotonicModelQuantumTaskResult | AnalogHamiltonianSimulationQuantumTaskResult]: The
            results of all of the quantum tasks in the batch.
            `FAILED`, `CANCELLED`, or timed out quantum tasks will have a result of None
        """  # noqa: E501
        if not self._results or not use_cached_value:
            self._results = AwsQuantumTaskBatch._retrieve_results(self._tasks, self._max_workers)
            self._unsuccessful = {
                task.id for task, result in zip(self._tasks, self._results) if not result
            }

        retries = 0
        while self._unsuccessful and retries < max_retries:
            self.retry_unsuccessful_tasks()
            retries += 1

        if fail_unsuccessful and self._unsuccessful:
            raise RuntimeError(
                f"{len(self._unsuccessful)} tasks failed to complete after {max_retries} retries"
            )
        return self._results

    @staticmethod
    def _retrieve_results(
        tasks: list[AwsQuantumTask], max_workers: int
    ) -> list[
        GateModelQuantumTaskResult
        | AnnealingQuantumTaskResult
        | PhotonicModelQuantumTaskResult
        | AnalogHamiltonianSimulationQuantumTaskResult
    ]:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            result_futures = [executor.submit(task.result) for task in tasks]
        return [future.result() for future in result_futures]

    def retry_unsuccessful_tasks(self) -> bool:
        """Retries any quantum tasks in the batch without valid results.

        This method should only be called after `results()` has been called at least once.
        The method will generate new quantum tasks for any failed quantum tasks, so `self.task` and
        `self.results()` may return different values after a call to this method.

        Returns:
            bool: Whether or not all retried quantum tasks completed successfully.
        """
        if not self._results:
            raise RuntimeError("results() should be called before attempting to retry")
        unsuccessful_indices = [index for index, result in enumerate(self._results) if not result]
        # Return early if there's nothing to retry
        if not unsuccessful_indices:
            return True
        retried_tasks = AwsQuantumTaskBatch._execute(
            self._aws_session,
            self._device_arn,
            [self._task_specifications[i] for i in unsuccessful_indices],
            self._s3_destination_folder,
            self._shots,
            self._max_parallel,
            self._max_workers,
            self._poll_timeout_seconds,
            self._poll_interval_seconds,
            self._reservation_arn,
            *self._aws_quantum_task_args,
            **self._aws_quantum_task_kwargs,
        )
        for index, task in zip(unsuccessful_indices, retried_tasks):
            self._tasks[index] = task

        retried_results = AwsQuantumTaskBatch._retrieve_results(retried_tasks, self._max_workers)
        for index, result in zip(unsuccessful_indices, retried_results):
            self._results[index] = result
        self._unsuccessful = {
            task.id for task, result in zip(retried_tasks, retried_results) if not result
        }
        return not self._unsuccessful

    @property
    def tasks(self) -> list[AwsQuantumTask]:
        """list[AwsQuantumTask]: The quantum tasks in this batch, as a list of AwsQuantumTask
        objects
        """
        return list(self._tasks)

    @property
    def size(self) -> int:
        """int: The number of quantum tasks in the batch"""
        return len(self._tasks)

    @property
    def unfinished(self) -> set[str]:
        """Gets all the IDs of all the quantum tasks in the batch that have yet to complete.

        Returns:
            set[str]: The IDs of all the quantum tasks in the batch that have yet to complete.
        """
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            status_futures = {task.id: executor.submit(task.state) for task in self._tasks}
        unfinished = set()
        for task_id, task_result in status_futures.items():
            status = task_result.result()
            if status not in AwsQuantumTask.TERMINAL_STATES:
                unfinished.add(task_id)
            if status in AwsQuantumTask.NO_RESULT_TERMINAL_STATES:
                self._unsuccessful.add(task_id)
        return unfinished

    @property
    def unsuccessful(self) -> set[str]:
        """set[str]: The IDs of all the FAILED, CANCELLED, or timed out quantum tasks in the
        batch.
        """
        return set(self._unsuccessful)
