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

import asyncio
import threading
from asyncio import AbstractEventLoop, Task
from typing import Dict, Optional, Union

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.default_simulator.simulator import BaseLocalSimulator
from braket.ir.ahs import Program as AHSProgram
from braket.ir.openqasm import Program
from braket.task_result import (
    AnalogHamiltonianSimulationTaskResult,
    AnnealingTaskResult,
    GateModelTaskResult,
)
from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
    QuantumTask,
)
from braket.tasks.quantum_task_helper import _convert_to_sim_format, _wrap_results


class LocalQuantumTask(QuantumTask):
    """A task containing the results of a local simulation.

    Since this class is instantiated with the results, cancel() and run_async() are unsupported.
    """

    def __init__(
        self,
        result: Optional[
            Union[
                GateModelQuantumTaskResult,
                AnnealingQuantumTaskResult,
                PhotonicModelQuantumTaskResult,
            ]
        ] = None,
    ):
        self._result = result
        self._loop = asyncio.new_event_loop()

    @staticmethod
    def create(
        task_specification: Union[
            Circuit, Problem, Program, AnalogHamiltonianSimulation, AHSProgram
        ],
        delegate: BaseLocalSimulator,
        shots: int = 0,
        inputs: Optional[Dict[str, float]] = None,
        *args,
        **kwargs,
    ) -> "LocalQuantumTask":
        """LocalQuantumTask factory method that serializes a quantum task specification
        (either a quantum circuit or problem), computes the result,
        and returns back an LocalQuantumTask tracking the execution.

        Args:
            task_specification (Union[Circuit, Problem, Program, AnalogHamiltonianSimulation, AHSProgram]):  # noqa
                The specification of the task to run on device.

            delegate (BaseLocalSimulator): Concrete simulator based of BaseLocalSimulator to run the task on.

            shots (int): The number of times to run the task on the device. If the device is a
                simulator, this implies the state is sampled N times, where N = `shots`.
                `shots=0` is only available on simulators and means that the simulator
                will compute the exact results based on the task specification.

            inputs (Optional[Dict[str, float]]): Inputs to be passed along with the
                IR. If the IR supports inputs, the inputs will be updated with this value.
                Default: {}.

        Returns:
            : LocalQuantumTask tracking the task execution on the device.
        """
        task = LocalQuantumTask()
        task._delegate = delegate
        task._args = _convert_to_sim_format(
            task_specification, delegate, shots, inputs=inputs
        ) + list(args)
        task._kwargs = kwargs
        task.async_result()
        return task

    def id(self) -> str:
        raise NotImplementedError

    def cancel(self) -> None:
        """Cancel the quantum task."""
        raise NotImplementedError("LocalQuantumTask does not support cancelling")

    def state(self) -> str:
        return self._status()

    def _status(self) -> str:
        if hasattr(self, "_thread"):
            if self._thread.is_alive():
                return "RUNNING"

            return "COMPLETED"
        return "CREATED"

    def result(
        self,
    ) -> Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult]:
        """
        Get the quantum task result by running the task on the designated local simulator.
        Once the task is completed, the result is returned as a
        `GateModelQuantumTaskResult` or `AnnealingQuantumTaskResult`

        This method is a blocking thread call and synchronously returns a result.
        Call `async_result()` if you require an asynchronous invocation.

        Returns:
            Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult]: # noqa
            The result of the task, if the task completed successfully; returns `None` if the task
            did not complete successfully.

        Raises:
            Exception:
                Raises an exception raised in the thread while running the task on the simulator.
        """
        if not self._result:
            self._thread.join()

            if self._task._exception:
                raise self._task._exception

            self._result = self._task._result

        return self._result

    def async_result(self) -> asyncio.Task:
        """Get the quantum task result asynchronously.
        Returns:
            Task: Get the quantum task result asynchronously.
        """

        return self._get_task()

    def _create_task(self) -> asyncio.Task:
        """
        Wrap the `_wait_for_completion` coroutine inside a future-like object.
        Invoking this method starts the coroutine and returns back the future-like object
        that contains it. Note that this does not block on the coroutine to finish.

        Returns:
            asyncio.Task: An asyncio Task that contains the `_wait_for_completion()` coroutine.
        """
        return self._loop.create_task(self._async_run_internal())

    def _run_event_loop(self, loop: AbstractEventLoop, task: Task) -> None:
        """
        Run the event loop with the given task.

        Parameters:
        - loop (asyncio.AbstractEventLoop): The asyncio event loop to use for running the task.
        - task (coroutine): The coroutine or future
                        that represents the task to run in the event loop.

        Raises:
        - Exception: If an exception occurs during the execution of the task.

        Description:
        This method sets the specified event loop using asyncio.set_event_loop(),
        and then runs the event loop until the given task is completed.
        If any other exception occurs during the execution of the task, it is re-raised
        to be handled in the calling context.

        Note:
        - This method assumes that the event loop is not already running in the current thread.
        - It is intended to be used internally or by advanced asyncio applications.

        Example:
        # Create and run an event loop with a task
        loop = asyncio.get_event_loop()
        task = loop.create_task(some_coroutine())
        _run_event_loop(loop, task)
        """
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(task)
        except Exception as e:
            raise e

    def _get_task(self) -> asyncio.Task:
        if not hasattr(self, "_task") or (
            self._task.done() and not self._task.cancelled() and self._result is None
        ):
            self._task = self._create_task()
            self._thread = threading.Thread(
                target=self._run_event_loop, args=(self._loop, self._task)
            )
            self._thread.start()

        return self._task

    async def _async_run_internal(self):
        results = self._run_internal(*self._args, **self._kwargs)
        return _wrap_results(results)

    def _run_internal(
        self,
        *args,
        **kwargs,
    ) -> Union[GateModelTaskResult, AnnealingTaskResult, AnalogHamiltonianSimulationTaskResult,]:
        simulator = self._delegate
        return simulator.run(*args, **kwargs)
