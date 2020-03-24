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
from functools import singledispatch
from typing import Set, Union

import pkg_resources

from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.devices.braket_simulator import BraketSimulator
from braket.devices.device import Device
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask

_simulator_devices = {
    entry.name: entry for entry in pkg_resources.iter_entry_points("braket.simulators")
}


class LocalSimulator(Device):
    """ A simulator meant to run directly on the user's machine.

    This class wraps an IRSimulator object so that it can be run and returns
    results using constructs from the SDK rather than Braket IR.
    """

    def __init__(self, backend: Union[str, BraketSimulator]):
        """
        Args:
            backend (Union[str, IRSimulator]): The name of the simulator backend or
            the actual simulator instance to use for simulation
        """
        delegate = _get_simulator(backend)
        super().__init__(
            name=delegate.__class__.__name__,
            status="AVAILABLE",
            status_reason="Local simulator loaded successfully",
        )
        self._delegate = delegate

    def run(
        self, task_specification: Union[Circuit, Problem], *args, **kwargs,
    ) -> LocalQuantumTask:
        """ Runs the given task with the wrapped local simulator.

        Note: If running a circuit, the number of qubits will be passed
        to the backend as the argument after the circuit itself.

        Args:
            task_specification (Union[Circuit, Problem]):
            *args: Positional args to pass to the IR simulator
            **kwargs: Keyword arguments to pass to the IR simulator

        Returns:
            LocalQuantumTask: A LocalQuantumTask object containing the results
            of the simulation
        """
        result = _run_internal(task_specification, self._delegate, *args, **kwargs)
        return LocalQuantumTask(result)

    @classmethod
    def registered_backends(cls) -> Set[str]:
        """ Gets the backends that have been registered as entry points

        Returns:
            Set[str]: The names of the available backends that can be passed
            into LocalSimulator's constructor
        """
        return set(_simulator_devices.keys())


@singledispatch
def _get_simulator(simulator):
    raise TypeError("Simulator must either be a string or an IRSimulator instance")


@_get_simulator.register
def _(backend_name: str):
    if backend_name in _simulator_devices:
        device_class = _simulator_devices[backend_name].load()
        return device_class()
    else:
        raise ValueError(f"Only the following devices are available {_simulator_devices.keys()}")


@_get_simulator.register
def _(backend_impl: BraketSimulator):
    return backend_impl


@singledispatch
def _run_internal(task_specification, simulator: BraketSimulator, *args, **kwargs):
    raise NotImplementedError("Unsupported task type")


@_run_internal.register
def _(circuit: Circuit, simulator: BraketSimulator, *args, **kwargs):
    program = circuit.to_ir()
    qubits = circuit.qubit_count
    result_json = simulator.run(program, qubits, *args, **kwargs)
    return GateModelQuantumTaskResult.from_string(result_json)


@_run_internal.register
def _(problem: Problem, simulator: BraketSimulator, *args, **kwargs):
    ir = problem.to_ir()
    result_json = simulator.run(ir, *args, *kwargs)
    return AnnealingQuantumTaskResult.from_string(result_json)
