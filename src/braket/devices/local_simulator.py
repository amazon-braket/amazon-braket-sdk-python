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
from itertools import repeat
from multiprocessing import Pool
from os import cpu_count
from typing import Optional, Union

import pkg_resources

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.circuits.circuit_helpers import validate_circuit_and_shots
from braket.circuits.serialization import IRType
from braket.device_schema import DeviceActionType, DeviceCapabilities
from braket.devices.device import Device
from braket.ir.ahs import Program as AHSProgram
from braket.ir.openqasm import Program
from braket.simulator import BraketSimulator
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
    AnalogHamiltonianSimulationQuantumTaskResult,
)
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
        inputs: Optional[dict[str, float]] = None,
        *args,
        **kwargs,
    ) -> LocalQuantumTask:
        """Runs the given task with the wrapped local simulator.

        Args:
            task_specification (Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]):
                The quantum task specification.
            shots (int): The number of times to run the circuit or annealing problem.
                Default is 0, which means that the simulator will compute the exact
                results based on the quantum task specification.
                Sampling is not supported for shots=0.
            inputs (Optional[dict[str, float]]): Inputs to be passed along with the
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
        result = self._run_internal(task_specification, shots, inputs=inputs, *args, **kwargs)
        return LocalQuantumTask(result)

    def run_batch(
        self,
        task_specifications: Union[
            Union[Circuit, Problem, Program, AnalogHamiltonianSimulation],
            list[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]],
        ],
        shots: Optional[int] = 0,
        max_parallel: Optional[int] = None,
        inputs: Optional[Union[dict[str, float], list[dict[str, float]]]] = None,
        *args,
        **kwargs,
    ) -> LocalQuantumTaskBatch:
        """Executes a batch of quantum tasks in parallel

        Args:
            task_specifications (Union[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation], list[Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]]]): # noqa
                Single instance or list of quantum task specification.
            shots (Optional[int]): The number of times to run the quantum task.
                Default: 0.
            max_parallel (Optional[int]): The maximum number of quantum tasks to run  in parallel. Default
                is the number of CPU.
            inputs (Optional[Union[dict[str, float], list[dict[str, float]]]]): Inputs to be passed
                along with the IR. If the IR supports inputs, the inputs will be updated with
                this value. Default: {}.

        Returns:
            LocalQuantumTaskBatch: A batch containing all of the quantum tasks run

        See Also:
            `braket.tasks.local_quantum_task_batch.LocalQuantumTaskBatch`
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

        with Pool(min(max_parallel, len(tasks_and_inputs))) as pool:
            param_list = [(task, shots, inp, *args, *kwargs) for task, inp in tasks_and_inputs]
            results = pool.starmap(self._run_internal_wrap, param_list)

        return LocalQuantumTaskBatch(results)

    @property
    def properties(self) -> DeviceCapabilities:
        """DeviceCapabilities: Return the device properties

        Please see `braket.device_schema` in amazon-braket-schemas-python_

        .. _amazon-braket-schemas-python: https://github.com/aws/amazon-braket-schemas-python"""
        return self._delegate.properties

    @staticmethod
    def registered_backends() -> set[str]:
        """Gets the backends that have been registered as entry points

        Returns:
            set[str]: The names of the available backends that can be passed
            into LocalSimulator's constructor
        """
        return set(_simulator_devices.keys())

    def _run_internal_wrap(
        self,
        task_specification: Union[Circuit, Problem, Program, AnalogHamiltonianSimulation],
        shots: Optional[int] = None,
        inputs: Optional[dict[str, float]] = None,
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

    @singledispatchmethod
    def _run_internal(
        self,
        task_specification: Union[
            Circuit, Problem, Program, AnalogHamiltonianSimulation, AHSProgram
        ],
        shots: Optional[int] = None,
        *args,
        **kwargs,
    ) -> Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult]:
        raise NotImplementedError(f"Unsupported task type {type(task_specification)}")

    @_run_internal.register
    def _(
        self,
        circuit: Circuit,
        shots: Optional[int] = None,
        inputs: Optional[dict[str, float]] = None,
        *args,
        **kwargs,
    ):
        simulator = self._delegate
        if DeviceActionType.OPENQASM in simulator.properties.action:
            validate_circuit_and_shots(circuit, shots)
            program = circuit.to_ir(ir_type=IRType.OPENQASM)
            program.inputs.update(inputs or {})
            results = simulator.run(program, shots, *args, **kwargs)
            return GateModelQuantumTaskResult.from_object(results)
        elif DeviceActionType.JAQCD in simulator.properties.action:
            validate_circuit_and_shots(circuit, shots)
            program = circuit.to_ir(ir_type=IRType.JAQCD)
            qubits = circuit.qubit_count
            results = simulator.run(program, qubits, shots, *args, **kwargs)
            return GateModelQuantumTaskResult.from_object(results)
        raise NotImplementedError(f"{type(simulator)} does not support qubit gate-based programs")

    @_run_internal.register
    def _(self, problem: Problem, shots: Optional[int] = None, *args, **kwargs):
        simulator = self._delegate
        if DeviceActionType.ANNEALING not in simulator.properties.action:
            raise NotImplementedError(
                f"{type(simulator)} does not support quantum annealing problems"
            )
        ir = problem.to_ir()
        results = simulator.run(ir, shots, *args, *kwargs)
        return AnnealingQuantumTaskResult.from_object(results)

    @_run_internal.register
    def _(
        self,
        program: Program,
        shots: Optional[int] = None,
        inputs: Optional[dict[str, float]] = None,
        *args,
        **kwargs,
    ):
        simulator = self._delegate
        if DeviceActionType.OPENQASM not in simulator.properties.action:
            raise NotImplementedError(f"{type(simulator)} does not support OpenQASM programs")
        if inputs:
            inputs_copy = program.inputs.copy() if program.inputs is not None else {}
            inputs_copy.update(inputs)
            program = Program(
                source=program.source,
                inputs=inputs_copy,
            )
        results = simulator.run(program, shots, *args, **kwargs)
        return GateModelQuantumTaskResult.from_object(results)

    @_run_internal.register
    def _(
        self,
        program: AnalogHamiltonianSimulation,
        shots: Optional[int] = None,
        *args,
        **kwargs,
    ):
        simulator = self._delegate
        if DeviceActionType.AHS not in simulator.properties.action:
            raise NotImplementedError(
                f"{type(simulator)} does not support analog Hamiltonian simulation programs"
            )
        results = simulator.run(program.to_ir(), shots, *args, **kwargs)
        return AnalogHamiltonianSimulationQuantumTaskResult.from_object(results)

    @_run_internal.register
    def _(
        self,
        program: AHSProgram,
        shots: Optional[int] = None,
        *args,
        **kwargs,
    ):
        simulator = self._delegate
        if DeviceActionType.AHS not in simulator.properties.action:
            raise NotImplementedError(
                f"{type(simulator)} does not support analog Hamiltonian simulation programs"
            )
        results = simulator.run(program, shots, *args, **kwargs)
        return AnalogHamiltonianSimulationQuantumTaskResult.from_object(results)
