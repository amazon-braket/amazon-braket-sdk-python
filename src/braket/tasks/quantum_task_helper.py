# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from itertools import repeat
from typing import Dict, List, Optional, Tuple, Union

from braket.ahs import AnalogHamiltonianSimulation
from braket.annealing import Problem
from braket.circuits import Circuit
from braket.circuits.circuit_helpers import validate_circuit_and_shots
from braket.circuits.serialization import IRType
from braket.device_schema import DeviceActionType
from braket.ir.ahs import Program as AHSProgram
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.task_result import (
    AnalogHamiltonianSimulationTaskResult,
    AnnealingTaskResult,
    GateModelTaskResult,
)
from braket.tasks import (
    AnalogHamiltonianSimulationQuantumTaskResult,
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
)


@singledispatch
def _convert_to_sim_format(
    task_specification: Union[
        Circuit, Problem, OpenQasmProgram, AnalogHamiltonianSimulation, AHSProgram
    ],
    delegate,  # noqa
    shots: Optional[int] = None,
    **kwargs,
) -> list:
    raise NotImplementedError(f"Unsupported task type {type(task_specification)}")


@_convert_to_sim_format.register
def _(program: OpenQasmProgram, delegate, shots: Optional[int] = None, **kwargs) -> list:  # noqa
    simulator = delegate
    if DeviceActionType.OPENQASM not in simulator.properties.action:
        raise NotImplementedError(f"{type(simulator)} does not support OpenQASM programs")
    if kwargs["inputs"]:
        inputs_copy = program.inputs.copy() if program.inputs is not None else {}
        inputs_copy.update(kwargs["inputs"])
        program = OpenQasmProgram(
            source=program.source,
            inputs=inputs_copy,
        )
    return [program, shots]


@_convert_to_sim_format.register
def _(circuit: Circuit, delegate, shots: Optional[int] = None, **kwargs) -> list:  # noqa
    simulator = delegate
    if DeviceActionType.OPENQASM in simulator.properties.action:
        validate_circuit_and_shots(circuit, shots)
        program = circuit.to_ir(ir_type=IRType.OPENQASM)
        program.inputs.update(kwargs["inputs"] or {})
        return [program, shots]
    elif DeviceActionType.JAQCD in simulator.properties.action:
        validate_circuit_and_shots(circuit, shots)
        program = circuit.to_ir(ir_type=IRType.JAQCD)
        qubits = circuit.qubit_count
        return [program, qubits, shots]
    raise NotImplementedError(f"{type(simulator)} does not support qubit gate-based programs")


@_convert_to_sim_format.register
def _(problem: Problem, delegate, shots: Optional[int] = None, **kwargs) -> list:  # noqa
    simulator = delegate
    if DeviceActionType.ANNEALING not in simulator.properties.action:
        raise NotImplementedError(f"{type(simulator)} does not support quantum annealing problems")
    ir = problem.to_ir()
    return [ir, shots]


@_convert_to_sim_format.register
def _(
    program: AnalogHamiltonianSimulation, delegate, shots: Optional[int] = None, **kwargs  # noqa
) -> list:
    simulator = delegate
    if DeviceActionType.AHS not in simulator.properties.action:
        raise NotImplementedError(
            f"{type(simulator)} does not support analog Hamiltonian simulation programs"
        )
    return [program.to_ir(), shots]


@_convert_to_sim_format.register
def _(program: AHSProgram, delegate, shots: Optional[int] = None, **kwargs) -> list:  # noqa
    simulator = delegate
    if DeviceActionType.AHS not in simulator.properties.action:
        raise NotImplementedError(
            f"{type(simulator)} does not support analog Hamiltonian simulation programs"
        )
    return [program, shots]


@singledispatch
def _wrap_results(
    results: Union[GateModelTaskResult, AnalogHamiltonianSimulationTaskResult, AnnealingTaskResult]
) -> [
    GateModelQuantumTaskResult,
    AnnealingQuantumTaskResult,
    AnalogHamiltonianSimulationQuantumTaskResult,
]:
    raise NotImplementedError


@_wrap_results.register
def _(results: GateModelTaskResult) -> GateModelQuantumTaskResult:
    return GateModelQuantumTaskResult.from_object(results)


@_wrap_results.register
def _(
    results: AnalogHamiltonianSimulationTaskResult,
) -> AnalogHamiltonianSimulationQuantumTaskResult:
    return AnalogHamiltonianSimulationQuantumTaskResult.from_object(results)


@_wrap_results.register
def _(results: AnnealingTaskResult) -> AnnealingQuantumTaskResult:
    return AnnealingQuantumTaskResult.from_object(results)


def _batch_tasks_and_inputs(
    task_specifications: Union[
        Union[Circuit, Problem, OpenQasmProgram, BlackbirdProgram, AnalogHamiltonianSimulation],
        List[
            Union[Circuit, Problem, OpenQasmProgram, BlackbirdProgram, AnalogHamiltonianSimulation]
        ],
    ],
    inputs: Union[Dict[str, float], List[Dict[str, float]]] = None,
) -> List[
    Tuple[
        Union[Circuit, Problem, OpenQasmProgram, BlackbirdProgram, AnalogHamiltonianSimulation],
        Dict[str, float],
    ]
]:
    inputs = inputs or {}

    single_task = isinstance(
        task_specifications,
        (Circuit, Problem, OpenQasmProgram, BlackbirdProgram, AnalogHamiltonianSimulation),
    )
    single_input = isinstance(inputs, dict)

    if not single_task and not single_input:
        if len(task_specifications) != len(inputs):
            raise ValueError("Multiple inputs and task specifications must be equal in number.")
    if single_task:
        task_specifications = repeat(task_specifications)

    if single_input:
        inputs = repeat(inputs)

    tasks_and_inputs = zip(task_specifications, inputs)

    if single_task and single_input:
        tasks_and_inputs = [next(tasks_and_inputs)]

    tasks_and_inputs = list(tasks_and_inputs)

    for task_specification, input_map in tasks_and_inputs:
        if isinstance(task_specification, Circuit):
            param_names = {param.name for param in task_specification.parameters}
            unbounded_parameters = param_names - set(input_map.keys())
            if unbounded_parameters:
                raise ValueError(
                    f"Cannot execute circuit with unbound parameters: " f"{unbounded_parameters}"
                )

    return tasks_and_inputs
