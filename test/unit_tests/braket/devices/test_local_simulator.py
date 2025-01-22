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

import json
import textwrap
import warnings
from typing import Any, Optional
from unittest.mock import Mock, patch

import pytest
from pydantic.v1 import create_model  # This is temporary for defining properties below

import braket.ir as ir
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.ahs.atom_arrangement import AtomArrangement
from braket.ahs.hamiltonian import Hamiltonian
from braket.annealing import Problem, ProblemType
from braket.circuits import Circuit, FreeParameter, Gate, Noise
from braket.circuits.noise_model import GateCriteria, NoiseModel, NoiseModelInstruction
from braket.circuits.serialization import IRType, SerializableProgram
from braket.device_schema import DeviceActionType, DeviceCapabilities
from braket.device_schema.openqasm_device_action_properties import OpenQASMDeviceActionProperties
from braket.devices import LocalSimulator, local_simulator
from braket.ir.openqasm import Program
from braket.simulator import BraketSimulator
from braket.task_result import AnnealingTaskResult, GateModelTaskResult
from braket.task_result.analog_hamiltonian_simulation_task_result_v1 import (
    AnalogHamiltonianSimulationTaskResult,
)
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
    AnalogHamiltonianSimulationQuantumTaskResult,
)

GATE_MODEL_RESULT = GateModelTaskResult(**{
    "measurements": [[0, 0], [0, 0], [0, 0], [1, 1]],
    "measuredQubits": [0, 1],
    "taskMetadata": {
        "braketSchemaHeader": {"name": "braket.task_result.task_metadata", "version": "1"},
        "id": "task_arn",
        "shots": 100,
        "deviceId": "default",
    },
    "additionalMetadata": {
        "action": {
            "braketSchemaHeader": {"name": "braket.ir.jaqcd.program", "version": "1"},
            "instructions": [{"control": 0, "target": 1, "type": "cnot"}],
        },
    },
})

ANNEALING_RESULT = AnnealingTaskResult(**{
    "solutions": [[-1, -1, -1, -1], [1, -1, 1, 1], [1, -1, -1, 1]],
    "solutionCounts": [3, 2, 4],
    "values": [0.0, 1.0, 2.0],
    "variableCount": 4,
    "taskMetadata": {
        "id": "task_arn",
        "shots": 100,
        "deviceId": "device_id",
    },
    "additionalMetadata": {
        "action": {
            "type": "ISING",
            "linear": {"0": 0.3333, "1": -0.333, "4": -0.333, "5": 0.333},
            "quadratic": {"0,4": 0.667, "0,5": -1.0, "1,4": 0.667, "1,5": 0.667},
        },
        "dwaveMetadata": {
            "activeVariables": [0],
            "timing": {
                "qpuSamplingTime": 100,
                "qpuAnnealTimePerSample": 20,
                "qpuAccessTime": 10917,
                "qpuAccessOverheadTime": 3382,
                "qpuReadoutTimePerSample": 274,
                "qpuProgrammingTime": 9342,
                "qpuDelayTimePerSample": 21,
                "postProcessingOverheadTime": 117,
                "totalPostProcessingTime": 117,
                "totalRealTime": 10917,
                "runTimeChip": 1575,
                "annealTimePerRun": 20,
                "readoutTimePerRun": 274,
            },
        },
    },
})

AHS_RESULT = AnalogHamiltonianSimulationTaskResult(**{
    "taskMetadata": {
        "id": "rydberg",
        "shots": 100,
        "deviceId": "rydbergLocalSimulator",
    },
})


class DummyCircuitSimulator(BraketSimulator):
    def run(
        self,
        program: ir.jaqcd.Program,
        qubits: int,
        shots: Optional[int],
        inputs: Optional[dict[str, float]],
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        self._shots = shots
        self._qubits = qubits
        return GATE_MODEL_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj({
            "service": {
                "executionWindows": [
                    {
                        "executionDay": "Everyday",
                        "windowStartHour": "11:00",
                        "windowEndHour": "12:00",
                    }
                ],
                "shotsRange": [1, 10],
            },
            "action": {
                "braket.ir.openqasm.program": {
                    "actionType": "braket.ir.openqasm.program",
                    "version": ["1"],
                },
                "braket.ir.jaqcd.program": {
                    "actionType": "braket.ir.jaqcd.program",
                    "version": ["1"],
                },
            },
            "deviceParameters": {},
        })


class DummyJaqcdSimulator(BraketSimulator):
    def run(
        self,
        program: ir.jaqcd.Program,
        qubits: Optional[int] = None,
        shots: Optional[int] = None,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        if not isinstance(program, ir.jaqcd.Program):
            raise TypeError("Not a Jaqcd program")
        self._shots = shots
        self._qubits = qubits
        return GATE_MODEL_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj({
            "service": {
                "executionWindows": [
                    {
                        "executionDay": "Everyday",
                        "windowStartHour": "11:00",
                        "windowEndHour": "12:00",
                    }
                ],
                "shotsRange": [1, 10],
            },
            "action": {
                "braket.ir.jaqcd.program": {
                    "actionType": "braket.ir.jaqcd.program",
                    "version": ["1"],
                },
            },
            "deviceParameters": {},
        })

    def assert_shots(self, shots):
        assert self._shots == shots

    def assert_qubits(self, qubits):
        assert self._qubits == qubits


class DummyProgramSimulator(BraketSimulator):
    def run(
        self,
        openqasm_ir: Program,
        shots: int = 0,
        batch_size: int = 1,
    ) -> GateModelTaskResult:
        return GATE_MODEL_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        device_properties = DeviceCapabilities.parse_obj({
            "service": {
                "executionWindows": [
                    {
                        "executionDay": "Everyday",
                        "windowStartHour": "00:00",
                        "windowEndHour": "23:59:59",
                    }
                ],
                "shotsRange": [1, 10],
            },
            "action": {
                "braket.ir.openqasm.program": {
                    "actionType": "braket.ir.openqasm.program",
                    "version": ["1"],
                }
            },
            "deviceParameters": {},
        })
        oq3_action = OpenQASMDeviceActionProperties.parse_raw(
            json.dumps({
                "actionType": "braket.ir.openqasm.program",
                "version": ["1"],
                "supportedOperations": ["rx", "ry", "h", "cy", "cnot", "unitary"],
                "supportedResultTypes": [
                    {"name": "StateVector", "observables": None, "minShots": 0, "maxShots": 0},
                ],
                "supportedPragmas": [
                    "braket_unitary_matrix",
                    "braket_result_type_sample",
                    "braket_result_type_expectation",
                    "braket_result_type_variance",
                    "braket_result_type_probability",
                    "braket_result_type_state_vector",
                ],
            })
        )
        device_properties.action[DeviceActionType.OPENQASM] = oq3_action
        return device_properties


class DummySerializableProgram(SerializableProgram):
    def __init__(self, source: str):
        self.source = source

    def to_ir(self, ir_type: IRType = IRType.OPENQASM) -> str:
        return self.source


class DummySerializableProgramSimulator(DummyProgramSimulator):
    def run(
        self,
        program: SerializableProgram,
        shots: int = 0,
        batch_size: int = 1,
    ) -> GateModelQuantumTaskResult:
        return GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


class DummyProgramDensityMatrixSimulator(BraketSimulator):
    def run(
        self, program: ir.openqasm.Program, shots: Optional[int], *args, **kwargs
    ) -> dict[str, Any]:
        self._shots = shots
        return GATE_MODEL_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        device_properties = DeviceCapabilities.parse_obj({
            "service": {
                "executionWindows": [
                    {
                        "executionDay": "Everyday",
                        "windowStartHour": "11:00",
                        "windowEndHour": "12:00",
                    }
                ],
                "shotsRange": [1, 10],
            },
            "action": {},
            "deviceParameters": {},
        })
        oq3_action = OpenQASMDeviceActionProperties.parse_raw(
            json.dumps({
                "actionType": "braket.ir.openqasm.program",
                "version": ["1"],
                "supportedOperations": ["rx", "ry", "h", "cy", "cnot", "unitary"],
                "supportedResultTypes": [
                    {"name": "StateVector", "observables": None, "minShots": 0, "maxShots": 0},
                ],
                "supportedPragmas": [
                    "braket_noise_bit_flip",
                    "braket_noise_depolarizing",
                    "braket_noise_kraus",
                    "braket_noise_pauli_channel",
                    "braket_noise_generalized_amplitude_damping",
                    "braket_noise_amplitude_damping",
                    "braket_noise_phase_flip",
                    "braket_noise_phase_damping",
                    "braket_noise_two_qubit_dephasing",
                    "braket_noise_two_qubit_depolarizing",
                    "braket_unitary_matrix",
                    "braket_result_type_sample",
                    "braket_result_type_expectation",
                    "braket_result_type_variance",
                    "braket_result_type_probability",
                    "braket_result_type_density_matrix",
                ],
            })
        )
        device_properties.action[DeviceActionType.OPENQASM] = oq3_action
        return device_properties


class DummyAnnealingSimulator(BraketSimulator):
    def run(self, problem: ir.annealing.Problem, *args, **kwargs) -> AnnealingTaskResult:
        return ANNEALING_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj({
            "service": {
                "executionWindows": [
                    {
                        "executionDay": "Everyday",
                        "windowStartHour": "11:00",
                        "windowEndHour": "12:00",
                    }
                ],
                "shotsRange": [1, 10],
            },
            "action": {
                "braket.ir.annealing.problem": {
                    "actionType": "braket.ir.annealing.problem",
                    "version": ["1"],
                }
            },
            "deviceParameters": {},
        })


class DummyRydbergSimulator(BraketSimulator):
    def run(
        self, program: AnalogHamiltonianSimulation, *args, **kwargs
    ) -> AnalogHamiltonianSimulationTaskResult:
        return AHS_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        properties = {
            "service": {
                "executionWindows": [
                    {
                        "executionDay": "Everyday",
                        "windowStartHour": "00:00",
                        "windowEndHour": "23:59:59",
                    }
                ],
                "shotsRange": [0, 10],
            },
            "action": {"braket.ir.ahs.program": {}},
        }

        RydbergSimulatorDeviceCapabilities = create_model(
            "RydbergSimulatorDeviceCapabilities", **properties
        )

        return RydbergSimulatorDeviceCapabilities.parse_obj(properties)


mock_circuit_entry = Mock()
mock_program_entry = Mock()
mock_jaqcd_entry = Mock()
mock_circuit_dm_entry = Mock()
mock_circuit_entry.load.return_value = DummyCircuitSimulator
mock_program_entry.load.return_value = DummyProgramSimulator
mock_jaqcd_entry.load.return_value = DummyJaqcdSimulator
mock_circuit_dm_entry.load.return_value = DummyProgramDensityMatrixSimulator
local_simulator._simulator_devices = {
    "dummy": mock_circuit_entry,
    "dummy_oq3": mock_program_entry,
    "dummy_jaqcd": mock_jaqcd_entry,
    "dummy_oq3_dm": mock_circuit_dm_entry,
}

mock_ahs_program = AnalogHamiltonianSimulation(
    register=AtomArrangement(), hamiltonian=Hamiltonian()
)


def test_load_from_entry_point():
    sim = LocalSimulator("dummy_oq3")
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_gate_model():
    dummy = DummyProgramSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_batch_circuit():
    dummy = DummyProgramSimulator()
    theta = FreeParameter("theta")
    task = Circuit().rx(angle=theta, target=0)
    device = LocalSimulator(dummy)
    num_tasks = 3
    circuits = [task for _ in range(num_tasks)]
    inputs = [{"theta": i} for i in range(num_tasks)]
    batch = device.run_batch(circuits, inputs=inputs, shots=10)
    assert len(batch.results()) == num_tasks
    for x in batch.results():
        assert x == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_batch_with_max_parallel():
    dummy = DummyProgramSimulator()
    task = Circuit().h(0).cnot(0, 1)
    device = LocalSimulator(dummy)
    num_tasks = 3
    circuits = [task for _ in range(num_tasks)]
    batch = device.run_batch(circuits, shots=10, max_parallel=2)
    assert len(batch.results()) == num_tasks
    for x in batch.results():
        assert x == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_batch_with_annealing_problems():
    dummy = DummyAnnealingSimulator()
    problem = Problem(ProblemType.ISING)
    device = LocalSimulator(dummy)
    num_tasks = 3
    problems = [problem for _ in range(num_tasks)]
    batch = device.run_batch(problems, shots=10)
    assert len(batch.results()) == num_tasks
    for x in batch.results():
        assert x == AnnealingQuantumTaskResult.from_object(ANNEALING_RESULT)


def test_batch_circuit_without_inputs():
    dummy = DummyProgramSimulator()
    bell = Circuit().h(0).cnot(0, 1)
    device = LocalSimulator(dummy)
    num_tasks = 3
    circuits = [bell for _ in range(num_tasks)]
    batch = device.run_batch(circuits, shots=10)
    assert len(batch.results()) == num_tasks
    for x in batch.results():
        assert x == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_batch_circuit_with_unbound_parameters():
    dummy = DummyProgramSimulator()
    device = LocalSimulator(dummy)
    theta = FreeParameter("theta")
    task = Circuit().rx(angle=theta, target=0)
    inputs = {"beta": 0.2}
    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"
    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        device.run_batch(task, inputs=inputs, shots=10)


def test_batch_circuit_with_single_task():
    dummy = DummyProgramSimulator()
    bell = Circuit().h(0).cnot(0, 1)
    device = LocalSimulator(dummy)
    batch = device.run_batch(bell, shots=10)
    assert len(batch.results()) == 1
    assert batch.results()[0] == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_batch_circuit_with_task_and_input_mismatch():
    dummy = DummyProgramSimulator()
    bell = Circuit().h(0).cnot(0, 1)
    device = LocalSimulator(dummy)
    num_tasks = 3
    circuits = [bell for _ in range(num_tasks)]
    inputs = [{} for _ in range(num_tasks - 1)]
    with pytest.raises(ValueError):
        device.run_batch(circuits, inputs=inputs, shots=10)


def test_run_gate_model_inputs():
    dummy = DummyProgramSimulator()
    dummy.run = Mock(return_value=GATE_MODEL_RESULT)
    sim = LocalSimulator(dummy)
    circuit = Circuit().rx(0, FreeParameter("theta"))
    task = sim.run(circuit, inputs={"theta": 2}, shots=10)
    dummy.run.assert_called_with(
        Program(
            source="\n".join((
                "OPENQASM 3.0;",
                "input float theta;",
                "bit[1] b;",
                "qubit[1] q;",
                "rx(theta) q[0];",
                "b[0] = measure q[0];",
            )),
            inputs={"theta": 2},
        ),
        shots=10,
    )
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_program_model_inputs():
    dummy = DummyProgramSimulator()
    dummy.run = Mock(return_value=GATE_MODEL_RESULT)
    sim = LocalSimulator(dummy)
    inputs = {"theta": 2}
    source_string = (
        "OPENQASM 3.0;",
        "input float theta;",
        "bit[1] b;",
        "qubit[1] q;",
        "rx(theta) q[0];",
        "b[0] = measure q[0];",
    )
    program = Program.construct(source="\n".join(source_string), inputs=inputs)
    update_inputs = {"beta": 3}
    task = sim.run(program, inputs=update_inputs, shots=10)
    assert program.inputs == inputs
    program.inputs.update(update_inputs)
    dummy.run.assert_called_with(program, shots=10)
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_jaqcd_only():
    dummy = DummyJaqcdSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    dummy.assert_shots(10)
    dummy.assert_qubits(None)
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_program_model():
    dummy = DummyProgramSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(
        Program(
            source="""
qubit[2] q;
bit[2] c;

h q[0];
cnot q[0], q[1];

c = measure q;
"""
        )
    )
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_serializable_program_model():
    dummy = DummySerializableProgramSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(
        DummySerializableProgram(
            source="""
qubit[2] q;
bit[2] c;
h q[0];
cnot q[0], q[1];
c = measure q;
"""
        )
    )
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_serializable_program_model_with_inputs():
    dummy = DummySerializableProgramSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(
        DummySerializableProgram(
            source="""
input float a;
qubit[2] q;
bit[2] c;
h q[0];
cnot q[0], q[1];
c = measure q;
"""
        ),
        inputs={"a": 0.1},
    )
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


@pytest.mark.xfail(raises=ValueError)
def test_run_gate_model_value_error():
    dummy = DummyCircuitSimulator()
    sim = LocalSimulator(dummy)
    sim.run(Circuit().h(0).cnot(0, 1))


def test_run_annealing():
    sim = LocalSimulator(DummyAnnealingSimulator())
    task = sim.run(Problem(ProblemType.ISING))
    assert task.result() == AnnealingQuantumTaskResult.from_object(ANNEALING_RESULT)


def test_run_ahs():
    sim = LocalSimulator(DummyRydbergSimulator())
    task = sim.run(mock_ahs_program)
    assert task.result() == AnalogHamiltonianSimulationQuantumTaskResult.from_object(AHS_RESULT)

    task = sim.run(mock_ahs_program.to_ir())
    assert task.result() == AnalogHamiltonianSimulationQuantumTaskResult.from_object(AHS_RESULT)


def test_registered_backends():
    assert LocalSimulator.registered_backends() == {
        "dummy",
        "dummy_oq3",
        "dummy_jaqcd",
        "dummy_oq3_dm",
    }


@pytest.mark.xfail(raises=TypeError)
def test_init_invalid_backend_type():
    LocalSimulator(1234)


@pytest.mark.xfail(raises=ValueError)
def test_init_unregistered_backend():
    LocalSimulator("foo")


@pytest.mark.xfail(raises=NotImplementedError)
def test_run_unsupported_type():
    sim = LocalSimulator(DummyCircuitSimulator())
    sim.run("I'm unsupported")


@pytest.mark.xfail(raises=NotImplementedError)
def test_run_annealing_unsupported():
    sim = LocalSimulator(DummyCircuitSimulator())
    sim.run(Problem(ProblemType.ISING))


@pytest.mark.xfail(raises=NotImplementedError)
def test_run_qubit_gate_unsupported():
    sim = LocalSimulator(DummyAnnealingSimulator())
    sim.run(Circuit().h(0).cnot(0, 1), 1000)


def test_properties():
    dummy = DummyCircuitSimulator()
    sim = LocalSimulator(dummy)
    expected_properties = dummy.properties
    assert sim.properties == expected_properties


@pytest.fixture
def noise_model():
    return (
        NoiseModel()
        .add_noise(Noise.BitFlip(0.05), GateCriteria(Gate.H))
        .add_noise(Noise.TwoQubitDepolarizing(0.10), GateCriteria(Gate.CNot))
    )


@pytest.mark.parametrize("backend", ["dummy_oq3_dm"])
def test_valid_local_device_for_noise_model(backend, noise_model):
    device = LocalSimulator(backend, noise_model=noise_model)
    assert device._noise_model.instructions == [
        NoiseModelInstruction(Noise.BitFlip(0.05), GateCriteria(Gate.H)),
        NoiseModelInstruction(Noise.TwoQubitDepolarizing(0.10), GateCriteria(Gate.CNot)),
    ]


@pytest.mark.parametrize("backend", ["dummy_oq3"])
def test_invalid_local_device_for_noise_model(backend, noise_model):
    with pytest.raises(ValueError):
        _ = LocalSimulator(backend, noise_model=noise_model)


@pytest.mark.parametrize("backend", ["dummy_oq3_dm"])
def test_local_device_with_invalid_noise_model(backend, noise_model):
    with pytest.raises(TypeError):
        _ = LocalSimulator(backend, noise_model=Mock())


@patch.object(DummyProgramDensityMatrixSimulator, "run")
def test_run_with_noise_model(mock_run, noise_model):
    mock_run.return_value = GATE_MODEL_RESULT
    device = LocalSimulator("dummy_oq3_dm", noise_model=noise_model)
    circuit = Circuit().h(0).cnot(0, 1)
    _ = device.run(circuit, shots=4)

    expected_circuit = textwrap.dedent(
        """
        OPENQASM 3.0;
        bit[2] b;
        qubit[2] q;
        h q[0];
        #pragma braket noise bit_flip(0.05) q[0]
        cnot q[0], q[1];
        #pragma braket noise two_qubit_depolarizing(0.1) q[0], q[1]
        b[0] = measure q[0];
        b[1] = measure q[1];
        """
    ).strip()

    mock_run.assert_called_with(
        Program(source=expected_circuit, inputs={}),
        shots=4,
    )


@patch.object(LocalSimulator, "_apply_noise_model_to_circuit")
def test_run_batch_with_noise_model(mock_apply, noise_model):
    device = LocalSimulator("dummy_oq3_dm", noise_model=noise_model)
    circuit = Circuit().h(0).cnot(0, 1)

    mock_apply.return_value = noise_model.apply(circuit)
    _ = device.run_batch([circuit] * 2, shots=4).results()
    assert mock_apply.call_count == 2


@patch.object(DummyProgramDensityMatrixSimulator, "run")
def test_run_noisy_circuit_with_noise_model(mock_run, noise_model):
    mock_run.return_value = GATE_MODEL_RESULT
    device = LocalSimulator("dummy_oq3_dm", noise_model=noise_model)
    circuit = Circuit().h(0).depolarizing(0, 0.1)
    with warnings.catch_warnings(record=True) as w:
        _ = device.run(circuit, shots=4)

    expected_warning = (
        "The noise model of the device is applied to a circuit that already has noise instructions."
    )
    expected_circuit = textwrap.dedent(
        """
        OPENQASM 3.0;
        bit[1] b;
        qubit[1] q;
        h q[0];
        #pragma braket noise bit_flip(0.05) q[0]
        #pragma braket noise depolarizing(0.1) q[0]
        b[0] = measure q[0];
        """
    ).strip()

    mock_run.assert_called_with(
        Program(source=expected_circuit, inputs={}),
        shots=4,
    )
    assert w[-1].message.__str__() == expected_warning


@patch.object(DummyProgramDensityMatrixSimulator, "run")
def test_run_openqasm_with_noise_model(mock_run, noise_model):
    mock_run.return_value = GATE_MODEL_RESULT
    device = LocalSimulator("dummy_oq3_dm", noise_model=noise_model)
    expected_circuit = textwrap.dedent(
        """
        OPENQASM 3.0;
        bit[1] b;
        qubit[1] q;
        h q[0];
        b[0] = measure q[0];
        """
    ).strip()
    expected_warning = (
        "Noise model is only applicable to circuits. The type of the task specification "
        "is Program. The noise model of the device does not apply."
    )
    circuit = Program(source=expected_circuit)
    with warnings.catch_warnings(record=True) as w:
        _ = device.run(circuit, shots=4)

    mock_run.assert_called_with(
        Program(source=expected_circuit, inputs=None),
        shots=4,
    )
    assert w[-1].message.__str__() == expected_warning
