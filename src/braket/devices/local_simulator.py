# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import json
from functools import singledispatch
from typing import Optional, Set, Union

import pkg_resources

from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.devices.device import Device
from braket.devices.ir_simulator import IRSimulator
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask

simulator_devices = {
    entry.name: entry for entry in pkg_resources.iter_entry_points("braket.simulators")
}


class LocalSimulator(Device):
    """ A simulator meant to run directly on the user's machine.

    This class wraps an IRSimulator object so that it can be run and returns
    results using constructs from the SDK rather than Braket IR.
    """

    def __init__(self, backend: Union[str, IRSimulator]):
        """
        To create a LocalSimulator with a backend name, the name and class must
        be registered as an entry point for "braket.simulators". This is done
        by adding an entry to entry_points in the backend package's setup.py:

        >>> entry_points = {
        >>>     "braket.simulators": [
        >>>         "backend_name = <backend_class>"
        >>>     ]
        >>> }

        To create a LocalSimulator using an IRSimulator instance, simply pass the
        instance to the constructor.

        Args:
            backend (Union[str, IRSimulator]): The name of the simulator backend or
            the actual simulator instance to use for simulation
        """
        super().__init__(name=None, status=None, status_reason=None)
        self._delegate = _get_simulator(backend)

    def run(
        self,
        task_specification: Union[Circuit, Problem],
        shots: Optional[int] = None,
        *args,
        **kwargs,
    ) -> LocalQuantumTask:
        """ Runs the given task with the wrapped local simulator

        Args:
            task_specification (Union[Circuit, Problem]):
            shots (Optional[int]): Number of times to run task
            *args: Positional args to pass to the IR simulator
            **kwargs: Keyword arguments to pass to the IR simulator

        Returns:
            LocalQuantumTask: A LocalQuantumTask object containing the results
            of the simulation
        """
        result = _run_internal(task_specification, self._delegate, shots, *args, **kwargs)
        return LocalQuantumTask(result)

    @classmethod
    def registered_backends(cls) -> Set[str]:
        """ Gets the backends that have been registered as entry points

        Returns:
            Set[str]: The names of the available backends that can be passed
            into LocalSimulator's constructor
        """
        return set(simulator_devices.keys())


@singledispatch
def _get_simulator(simulator):
    raise TypeError("Simulator must either be a string or an IRSimulator instance")


@_get_simulator.register
def _(backend_name: str):
    if backend_name in simulator_devices:
        device_class = simulator_devices[backend_name].load()
        return device_class()
    else:
        raise ValueError(f"Only the following devices are available {simulator_devices.keys()}")


@_get_simulator.register
def _(backend_impl: IRSimulator):
    return backend_impl


@singledispatch
def _run_internal(task_specification, simulator: IRSimulator, shots: int, *args, **kwargs):
    raise NotImplementedError("Unsupported task type")


@_run_internal.register
def _(circuit: Circuit, simulator: IRSimulator, shots: Optional[int], *args, **kwargs):
    program = circuit.to_ir()
    qubits = circuit.qubit_count
    result_json = json.dumps(simulator.run(program, shots, qubits, *args, **kwargs))
    return GateModelQuantumTaskResult.from_string(result_json)


@_run_internal.register
def _(problem: Problem, simulator: IRSimulator, *args, **kwargs):
    ir = problem.to_ir()
    result_json = json.dumps(simulator.run(ir, *args, *kwargs))
    return AnnealingQuantumTaskResult.from_string(result_json)
