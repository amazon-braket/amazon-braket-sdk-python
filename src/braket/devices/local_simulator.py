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

import sys
from functools import singledispatchmethod
from itertools import repeat
from os import cpu_count
from typing import Any, Optional

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.circuits.circuit_helpers import validate_circuit_and_shots
from braket.circuits.noise_model import NoiseModel
from braket.circuits.serialization import IRType, SerializableProgram
from braket.device_schema import DeviceActionType, DeviceCapabilities
from braket.devices.device import Device
from braket.ir.ahs import Program as AHSProgram
from braket.ir.openqasm import Program as OpenQASMProgram
from braket.simulator import BraketSimulator
from braket.task_result import (
    AnalogHamiltonianSimulationTaskResult,
    AnnealingTaskResult,
    GateModelTaskResult,
)
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
    AnalogHamiltonianSimulationQuantumTaskResult,
)
from braket.tasks.local_quantum_task import LocalQuantumTask
from braket.tasks.local_quantum_task_batch import LocalQuantumTaskBatch

if sys.version_info.minor == 9:
    from backports.entry_points_selectable import entry_points
else:
    from importlib.metadata import entry_points

_simulator_devices = {entry.name: entry for entry in entry_points(group="braket.simulators")}


class LocalSimulator(Device):
    """A simulator meant to run directly on the user's machine.

    This class wraps a BraketSimulator object so that it can be run and returns
    results using constructs from the SDK rather than Braket IR.
    """

    def __init__(
        self,
        backend: str | BraketSimulator = "default",
        noise_model: Optional[NoiseModel] = None,
    ):
        """Initializes a `LocalSimulator`.

        Args:
            backend (Union[str, BraketSimulator]): The name of the simulator backend or
                the actual simulator instance to use for simulation. Defaults to the
                `default` simulator backend name.
            noise_model (Optional[NoiseModel]): The Braket noise model to apply to the circuit
                before execution. Noise model can only be added to the devices that support
                noise simulation.
        """
        delegate = self._get_simulator(backend)
        super().__init__(
            name=delegate.__class__.__name__,
            status="AVAILABLE",
        )
        self._delegate = delegate
        if noise_model:
            self._validate_device_noise_model_support(noise_model)
        self._noise_model = noise_model

    def run(
        self,
        task_specification: Circuit
        | Problem
        | OpenQASMProgram
        | AnalogHamiltonianSimulation
        | SerializableProgram,
        shots: int = 0,
        inputs: Optional[dict[str, float]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> LocalQuantumTask:
        """Runs the given task with the wrapped local simulator.

        Args:
            task_specification (Union[Circuit, Problem, OpenQASMProgram, AnalogHamiltonianSimulation, SerializableProgram]):
                The quantum task specification.
            shots (int): The number of times to run the circuit or annealing problem.
                Default is 0, which means that the simulator will compute the exact
                results based on the quantum task specification.
                Sampling is not supported for shots=0.
            inputs (Optional[dict[str, float]]): Inputs to be passed along with the
                IR. If the IR supports inputs, the inputs will be updated with this
                value. Default: {}.
            *args (Any): Arbitrary arguments.
            **kwargs(Any): Arbitrary keyword arguments.

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
        """  # noqa: E501
        if self._noise_model:
            task_specification = self._apply_noise_model_to_circuit(task_specification)
        payload = self._construct_payload(task_specification, inputs, shots)
        result = self._delegate.run(payload, *args, shots=shots, **kwargs)
        return LocalQuantumTask(self._to_result_object(result))

    def run_batch(
        self,
        task_specifications: Circuit
        | Problem
        | OpenQASMProgram
        | AnalogHamiltonianSimulation
        | SerializableProgram
        | list[
            Circuit | Problem | OpenQASMProgram | AnalogHamiltonianSimulation | SerializableProgram
        ],
        shots: int | None = 0,
        max_parallel: int | None = None,
        inputs: dict[str, float] | list[dict[str, float]] | None = None,
        *args,
        **kwargs,
    ) -> LocalQuantumTaskBatch:
        """Executes a batch of quantum tasks in parallel

        Args:
            task_specifications (Union[Union[Circuit, Problem, OpenQASMProgram, AnalogHamiltonianSimulation, SerializableProgram], list[Union[Circuit, Problem, OpenQASMProgram, AnalogHamiltonianSimulation, SerializableProgram]]]): # noqa
                Single instance or list of quantum task specification.
            shots (Optional[int]): The number of times to run the quantum task.
                Default: 0.
            max_parallel (Optional[int]): The maximum number of quantum tasks to run  in parallel. Default
                is the number of logical CPUs.
            inputs (Optional[Union[dict[str, float], list[dict[str, float]]]]): Inputs to be passed
                along with the IR. If the IR supports inputs, the inputs will be updated with
                this value. Default: {}.

        Returns:
            LocalQuantumTaskBatch: A batch containing all of the quantum tasks run

        See Also:
            `braket.tasks.local_quantum_task_batch.LocalQuantumTaskBatch`
        """  # noqa: E501
        inputs = inputs or {}

        if self._noise_model:
            task_specifications = [
                self._apply_noise_model_to_circuit(task_specification)
                for task_specification in task_specifications
            ]

        if not max_parallel:
            max_parallel = cpu_count()

        single_task = isinstance(
            task_specifications,
            (Circuit, OpenQASMProgram, Problem, AnalogHamiltonianSimulation),
        )

        single_input = isinstance(inputs, dict)

        if not single_task and not single_input and len(task_specifications) != len(inputs):
            raise ValueError("Multiple inputs and task specifications must be equal in number.")
        if single_task:
            task_specifications = repeat(task_specifications)

        if single_input:
            inputs = repeat(inputs)

        tasks_and_inputs = zip(task_specifications, inputs)

        if single_task and single_input:
            tasks_and_inputs = [next(tasks_and_inputs)]
        else:
            tasks_and_inputs = list(tasks_and_inputs)

        payloads = []
        for task_specification, input_map in tasks_and_inputs:
            if isinstance(task_specification, Circuit):
                param_names = {param.name for param in task_specification.parameters}
                if unbounded_parameters := param_names - set(input_map.keys()):
                    raise ValueError(
                        f"Cannot execute circuit with unbound parameters: {unbounded_parameters}"
                    )
            payloads.append(self._construct_payload(task_specification, input_map, shots))

        results = self._delegate.run_multiple(
            payloads, *args, shots=shots, max_parallel=max_parallel, **kwargs
        )
        return LocalQuantumTaskBatch([self._to_result_object(result) for result in results])

    @property
    def properties(self) -> DeviceCapabilities:
        """DeviceCapabilities: Return the device properties

        Please see `braket.device_schema` in amazon-braket-schemas-python_

        .. _amazon-braket-schemas-python: https://github.com/aws/amazon-braket-schemas-python
        """
        return self._delegate.properties

    @staticmethod
    def registered_backends() -> set[str]:
        """Gets the backends that have been registered as entry points

        Returns:
            set[str]: The names of the available backends that can be passed
            into LocalSimulator's constructor
        """
        return set(_simulator_devices.keys())

    @singledispatchmethod
    def _get_simulator(self, simulator: Any) -> BraketSimulator:
        raise TypeError("Simulator must either be a string or a BraketSimulator instance")

    @_get_simulator.register
    def _(self, backend_name: str) -> BraketSimulator:
        if backend_name not in _simulator_devices:
            raise ValueError(
                f"Only the following devices are available {_simulator_devices.keys()}"
            )
        device_class = _simulator_devices[backend_name].load()
        return device_class()

    @_get_simulator.register
    def _(self, backend_impl: BraketSimulator) -> BraketSimulator:
        return backend_impl

    @singledispatchmethod
    def _construct_payload(
        self,
        task_specification: Any,
        inputs: dict[str, float] | None,
        shots: int | None,
    ) -> Any:
        raise NotImplementedError(f"Unsupported task type {type(task_specification)}")

    @_construct_payload.register
    def _(self, circuit: Circuit, inputs: Optional[dict[str, float]], shots: Optional[int]):
        simulator = self._delegate
        if DeviceActionType.OPENQASM in simulator.properties.action:
            validate_circuit_and_shots(circuit, shots)
            program = circuit.to_ir(ir_type=IRType.OPENQASM)
            program.inputs.update(inputs or {})
            return program
        if DeviceActionType.JAQCD in simulator.properties.action:
            validate_circuit_and_shots(circuit, shots)
            return circuit.to_ir(ir_type=IRType.JAQCD)
        raise NotImplementedError(f"{type(simulator)} does not support qubit gate-based programs")

    @_construct_payload.register
    def _(self, program: OpenQASMProgram, inputs: Optional[dict[str, float]], _shots: int):
        simulator = self._delegate
        if DeviceActionType.OPENQASM not in simulator.properties.action:
            raise NotImplementedError(f"{type(simulator)} does not support OpenQASM programs")
        if inputs:
            inputs_copy = program.inputs.copy() if program.inputs is not None else {}
            inputs_copy.update(inputs)
            program = OpenQASMProgram(
                source=program.source,
                inputs=inputs_copy,
            )
        return program

    @_construct_payload.register
    def _(self, program: SerializableProgram, inputs: Optional[dict[str, float]], _shots: int):
        inputs_copy = inputs.copy() if inputs is not None else {}
        return OpenQASMProgram(source=program.to_ir(ir_type=IRType.OPENQASM), inputs=inputs_copy)

    @_construct_payload.register
    def _(self, program: AnalogHamiltonianSimulation, _inputs: dict[str, float], _shots: int):
        simulator = self._delegate
        if DeviceActionType.AHS not in simulator.properties.action:
            raise NotImplementedError(
                f"{type(simulator)} does not support analog Hamiltonian simulation programs"
            )
        return program.to_ir()

    @_construct_payload.register
    def _(self, program: AHSProgram, _inputs: dict[str, float], _shots: int):
        simulator = self._delegate
        if DeviceActionType.AHS not in simulator.properties.action:
            raise NotImplementedError(
                f"{type(simulator)} does not support analog Hamiltonian simulation programs"
            )
        return program

    @_construct_payload.register
    def _(self, problem: Problem, _inputs: dict[str, float], _shots: int):
        simulator = self._delegate
        if DeviceActionType.ANNEALING not in simulator.properties.action:
            raise NotImplementedError(
                f"{type(simulator)} does not support quantum annealing problems"
            )
        return problem.to_ir()

    @singledispatchmethod
    def _to_result_object(self, result: Any) -> Any:
        raise NotImplementedError(f"Unsupported task result type {type(result)}")

    @_to_result_object.register
    def _(self, result: GateModelQuantumTaskResult) -> GateModelQuantumTaskResult:
        return result

    @_to_result_object.register
    def _(self, result: GateModelTaskResult) -> GateModelQuantumTaskResult:
        return GateModelQuantumTaskResult.from_object(result)

    @_to_result_object.register
    def _(
        self, result: AnalogHamiltonianSimulationTaskResult
    ) -> AnalogHamiltonianSimulationQuantumTaskResult:
        return AnalogHamiltonianSimulationQuantumTaskResult.from_object(result)

    @_to_result_object.register
    def _(self, result: AnnealingTaskResult) -> AnnealingQuantumTaskResult:
        return AnnealingQuantumTaskResult.from_object(result)
