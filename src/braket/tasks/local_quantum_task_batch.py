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
from concurrent.futures.thread import ThreadPoolExecutor
from itertools import repeat
from os import cpu_count
from typing import Dict, List, Optional, Union

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.ir.openqasm import Program
from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
    QuantumTaskBatch,
)
from braket.tasks.local_quantum_task import LocalQuantumTask


class LocalQuantumTaskBatch(QuantumTaskBatch):
    """Executes a batch of quantum tasks in parallel.

    Since this class is instantiated with the results, cancel() and run_async() are unsupported.
    """

    def __init__(
        self,
        results: Optional[
            List[
                Union[
                    GateModelQuantumTaskResult,
                    AnnealingQuantumTaskResult,
                    PhotonicModelQuantumTaskResult,
                ]
            ]
        ] = None,
    ):
        self._results = results

    # flake8: noqa: C901
    @staticmethod
    def create(
        task_specifications: Union[
            Union[Circuit, Problem, Program, AnalogHamiltonianSimulation],
            List[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]],
        ],
        delegate,  # noqa
        shots: Optional[int] = 0,
        max_parallel: Optional[int] = None,
        inputs: Optional[Union[Dict[str, float], List[Dict[str, float]]]] = None,
        *args,
        **kwargs,
    ):
        """LocalQuantumTask factory method that serializes a quantum task specification
        (either a quantum circuit or problem), computes the result,
        and returns back an LocalQuantumTask tracking the execution.

        Args:
            task_specifications (Union[Circuit, Problem, Program, AnalogHamiltonianSimulation, AHSProgram]):  # noqa
                The specifications of the tasks to run on device.

            delegate ('LocalSimulator'): LocalSimulator to run the task on.

            shots (int): The number of times to run the task on the device. If the device is a
                simulator, this implies the state is sampled N times, where N = `shots`.
                `shots=0` is only available on simulators and means that the simulator
                will compute the exact results based on the task specification.
            max_parallel (Optional[int]): The maximum number of tasks to run  in parallel. Default
                is the number of CPU.
            inputs (Optional[Dict[str, float]]): Inputs to be passed along with the
                IR. If the IR supports inputs, the inputs will be updated with this value.
                Default: {}.

        Returns:
            : List[LocalQuantumTask] tracking the task execution on the device.
        """
        inputs = inputs or {}

        if not max_parallel:
            max_parallel = cpu_count()

        single_task = isinstance(
            task_specifications,
            (Circuit, Program, Problem, AnalogHamiltonianSimulation),
        )

        single_input = isinstance(inputs, dict)

        if not single_task and not single_input:
            if len(task_specifications) != len(inputs):
                raise ValueError(
                    "Multiple inputs and task specifications must " "be equal in number."
                )
        if single_task:
            task_specifications = repeat(task_specifications)

        if single_input:
            inputs = repeat(inputs)

        tasks_and_inputs = zip(task_specifications, inputs)

        if single_task and single_input:
            tasks_and_inputs = [next(tasks_and_inputs)]
        else:
            tasks_and_inputs = list(tasks_and_inputs)

        for task_specification, input_map in tasks_and_inputs:
            if isinstance(task_specification, Circuit):
                param_names = {param.name for param in task_specification.parameters}
                unbounded_parameters = param_names - set(input_map.keys())
                if unbounded_parameters:
                    raise ValueError(
                        f"Cannot execute circuit with unbound parameters: "
                        f"{unbounded_parameters}"
                    )

        with ThreadPoolExecutor(max_workers=min(max_parallel, len(tasks_and_inputs))) as executor:
            task_futures = [
                executor.submit(
                    LocalQuantumTask.create,
                    task,
                    delegate,
                    shots,
                    inp,
                    *args,
                    **kwargs,
                )
                for task, inp in tasks_and_inputs
            ]

        tasks = [future.result() for future in task_futures]
        return tasks

    def results(
        self,
    ) -> List[
        Union[
            GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult
        ]
    ]:
        return self._results
