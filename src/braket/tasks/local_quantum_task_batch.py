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
from os import cpu_count
from typing import Dict, List, Optional, Union

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.default_simulator.simulator import BaseLocalSimulator
from braket.ir.ahs import Program as AHSProgram
from braket.ir.openqasm import Program
from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
    QuantumTaskBatch,
)
from braket.tasks.local_quantum_task import LocalQuantumTask
from braket.tasks.quantum_task_helper import (
    _batch_tasks_and_inputs,
    _convert_to_sim_format,
    _wrap_results,
)


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

    @staticmethod
    def create(
        task_specifications: Union[
            Union[Circuit, Problem, Program, AnalogHamiltonianSimulation, AHSProgram],
            List[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation, AHSProgram]],
        ],
        delegate: BaseLocalSimulator,
        shots: int = 0,
        max_parallel: Optional[int] = None,
        inputs: Optional[Union[Dict[str, float], List[Dict[str, float]]]] = None,
        *args,
        **kwargs,
    ) -> "LocalQuantumTaskBatch":
        """Create and initialize a list of LocalQuantumTask instances for local quantum simulation.

        Args:
            task_specifications (Union[Union[Circuit,Problem,Program,AnalogHamiltonianSimulation,AHSProgram],List[Union[Circuit,Problem,Program,AnalogHamiltonianSimulation,AHSProgram]]]): # noqa
                The specifications for the quantum tasks to be created. This parameter
                accepts a single specification or a list of specifications.

            delegate (BaseLocalSimulator): Concrete simulator based of BaseLocalSimulator to be used for running the quantum tasks.

            shots (int): The number of times each quantum task should be executed
                (i.e., the number of shots for the simulation).
                Default is 0, which means no shots are performed.

            max_parallel (Optional[int]): The maximum number of tasks that can be executed in parallel.
                If not specified, the number of available CPU cores will be used as the default value.

            inputs (Optional[Union[Dict[str, float], List[Dict[str, float]]]]): Input data for the quantum tasks.
                This parameter can be a dictionary of input values for a single task or a list of dictionaries
                for multiple tasks.Default is an empty dictionary.

        Returns:
            : A LocalQuantumTaskBatch object containing _tasks which is a list of initialized LocalQuantumTask instances based
            on the given task specifications.

        Example:
            # Create a single quantum task using a Circuit specification
            circuit_spec = Circuit(...)
            simulator = LocalSimulator()
            task_list = LocalQuantumTask.create(task_specifications=circuit_spec,
                                                delegate=simulator, shots=100)

            # Create multiple quantum tasks using a list of Circuit and Program specifications
            circuit_spec_1 = Circuit(...)
            circuit_spec_2 = Circuit(...)
            program_spec = Program(...)
            task_list = LocalQuantumTaskBatch.create(task_specifications=[circuit_spec_1,
                                                circuit_spec_2, program_spec],
                                                delegate=simulator, shots=100, max_parallel=4)

        Notes:
            - The `inputs`, `*args`, and `**kwargs` parameters allow for customization
              and additional data to be passed to the quantum tasks as required.
            - The `max_parallel` parameter can be used to take advantage of parallelism
              when executing multiple tasks simultaneously, which can improve the overall
              performance for tasks that are independent of each other.
            - The `shots` parameter specifies the number of times each task should be
              executed, useful for statistical analysis or running quantum algorithms
              with multiple measurements.
            - When providing multiple task specifications and inputs, they must
              be equal in number.
            - If a Circuit task contains unbound parameters, an error will be
              raised before execution.
        """

        if not max_parallel:
            max_parallel = cpu_count()

        tasks_and_inputs = _batch_tasks_and_inputs(task_specifications, inputs)
        execution_managers = []
        for task, inp in tasks_and_inputs:
            args_ = _convert_to_sim_format(task, delegate, shots, inputs=inp) + list(args)
            try:
                execution_managers.append(delegate.execution_manager(*args_, **kwargs))
            except AttributeError:
                execution_managers.append([args_, kwargs])

        with ThreadPoolExecutor(max_workers=min(max_parallel, len(execution_managers))) as executor:
            if hasattr(delegate, "execution_manager"):
                task_futures = [
                    executor.submit(
                        LocalQuantumTask.create,
                        execution_manager,
                        *args,
                        **kwargs,
                    )
                    for execution_manager in execution_managers
                ]

                tasks = [future.result() for future in task_futures]
                local_quantum_task_batch = LocalQuantumTaskBatch()
                local_quantum_task_batch._tasks = tasks
                return local_quantum_task_batch
            else:
                task_futures = [
                    executor.submit(
                        delegate.run,
                        *args_,
                        **kwargs,
                    )
                    for args_, kwargs in execution_managers
                ]
                results = [_wrap_results(future.result()) for future in task_futures]
                return LocalQuantumTaskBatch(results)

    def results(
        self,
    ) -> List[
        Union[
            GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult
        ]
    ]:
        """Get the quantum task results.
        Returns:
            List[Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult, PhotonicModelQuantumTaskResult]]:: # noqa
            Get the quantum task results.
        """
        if not self._results:
            self._results = [local_quantum_task.result() for local_quantum_task in self._tasks]

        return self._results
