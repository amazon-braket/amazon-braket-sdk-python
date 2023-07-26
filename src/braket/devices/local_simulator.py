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

from functools import singledispatchmethod
from typing import Dict, List, Optional, Set, Union

import pkg_resources

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.device_schema import DeviceCapabilities
from braket.devices.device import Device
from braket.ir.openqasm import Program
from braket.simulator import BraketSimulator
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask
from braket.tasks.local_quantum_task_batch import LocalQuantumTaskBatch

_simulator_devices = {
    entry.name: entry for entry in pkg_resources.iter_entry_points("braket.simulators")
}


class LocalSimulator(Device):
    """A simulator meant to run directly on the user's machine.

    This class wraps a BraketSimulator object so that it can be run and returns
    results using constructs from the SDK rather than Braket IR.
    """

    def __init__(self, backend: Union[str, BraketSimulator] = "default"):
        """
        Args:
            backend (Union[str, BraketSimulator]): The name of the simulator backend or
                the actual simulator instance to use for simulation. Defaults to the
                `default` simulator backend name.
        """
        delegate = self._get_simulator(backend)
        super().__init__(
            name=delegate.__class__.__name__,
            status="AVAILABLE",
        )
        self._delegate = delegate

    def run(
        self,
        task_specification: Union[Circuit, Problem, Program, AnalogHamiltonianSimulation],
        shots: int = 0,
        inputs: Optional[Dict[str, float]] = None,
        *args,
        **kwargs,
    ) -> LocalQuantumTask:
        """Runs the given task with the wrapped local simulator.

        Args:
            task_specification (Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]):
                The task specification.
            shots (int): The number of times to run the circuit or annealing problem.
                Default is 0, which means that the simulator will compute the exact
                results based on the task specification.
                Sampling is not supported for shots=0.
            inputs (Optional[Dict[str, float]]): Inputs to be passed along with the
                IR. If the IR supports inputs, the inputs will be updated with this
                value. Default: {}.

        Returns:
            LocalQuantumTask: A LocalQuantumTask object containing the results
            of the simulation

        Note:
            If running a circuit, the number of qubits will be passed
            to the backend as the argument after the circuit itself.

        Examples:
            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = LocalSimulator("default")
            >>> device.run(circuit, shots=1000)
        """
        return LocalQuantumTask.create(
            task_specification, self._delegate, shots, inputs=inputs, *args, **kwargs
        )

    def run_batch(
        self,
        task_specifications: Union[
            Union[Circuit, Problem, Program, AnalogHamiltonianSimulation],
            List[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]],
        ],
        shots: Optional[int] = 0,
        max_parallel: Optional[int] = None,
        inputs: Optional[Union[Dict[str, float], List[Dict[str, float]]]] = None,
        *args,
        **kwargs,
    ) -> LocalQuantumTaskBatch:
        """Executes a batch of tasks in parallel

        Args:
            task_specifications (Union[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation], List[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]]]): # noqa
                Single instance or list of task specification.
            shots (Optional[int]): The number of times to run the task.
                Default: 0.
            max_parallel (Optional[int]): The maximum number of tasks to run  in parallel. Default
                is the number of CPU.
            inputs (Optional[Union[Dict[str, float], List[Dict[str, float]]]]): Inputs to be passed
                along with the IR. If the IR supports inputs, the inputs will be updated with
                this value. Default: {}.

        Returns:
            LocalQuantumTaskBatch: A batch containing all of the tasks run

        See Also:
            `braket.tasks.local_quantum_task_batch.LocalQuantumTaskBatch`
        """

        return LocalQuantumTaskBatch.create(
            task_specifications, self._delegate, shots, max_parallel, inputs, *args, **kwargs
        )

    @property
    def properties(self) -> DeviceCapabilities:
        """DeviceCapabilities: Return the device properties

        Please see `braket.device_schema` in amazon-braket-schemas-python_

        .. _amazon-braket-schemas-python: https://github.com/aws/amazon-braket-schemas-python"""
        return self._delegate.properties

    @staticmethod
    def registered_backends() -> Set[str]:
        """Gets the backends that have been registered as entry points

        Returns:
            Set[str]: The names of the available backends that can be passed
            into LocalSimulator's constructor
        """
        return set(_simulator_devices.keys())

    def _run_internal_wrap(
        self,
        task_specification: Union[Circuit, Problem, Program, AnalogHamiltonianSimulation],
        shots: Optional[int] = None,
        inputs: Optional[Dict[str, float]] = None,
        *args,
        **kwargs,
    ) -> Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult]:  # pragma: no cover
        """Wraps _run_interal for pickle dump"""
        return self._run_internal(task_specification, shots, inputs=inputs, *args, **kwargs)

    @singledispatchmethod
    def _get_simulator(self, simulator: Union[str, BraketSimulator]) -> LocalSimulator:
        raise TypeError("Simulator must either be a string or a BraketSimulator instance")

    @_get_simulator.register
    def _(self, backend_name: str):
        if backend_name in _simulator_devices:
            device_class = _simulator_devices[backend_name].load()
            return device_class()
        else:
            raise ValueError(
                f"Only the following devices are available {_simulator_devices.keys()}"
            )

    @_get_simulator.register
    def _(self, backend_impl: BraketSimulator):
        return backend_impl
