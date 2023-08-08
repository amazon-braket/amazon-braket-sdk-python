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
import uuid
from time import sleep

import numpy as np
import pytest

from braket.circuits import Circuit
from braket.default_simulator.local_execution_manager import LocalExecutionManager
from braket.device_schema import DeviceCapabilities
from braket.devices import LocalSimulator
from braket.ir.openqasm import Program
from braket.simulator import BraketSimulator
from braket.task_result import GateModelTaskResult, TaskMetadata
from braket.tasks import GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask
from braket.tasks.quantum_task_helper import _wrap_results

RESULT = GateModelQuantumTaskResult(
    task_metadata=TaskMetadata(**{"id": str(uuid.uuid4()), "deviceId": "default", "shots": 100}),
    additional_metadata=None,
    measurements=np.array([[0, 1], [1, 0]]),
    measured_qubits=[0, 1],
    result_types=None,
    values=None,
)

GATE_MODEL_RESULT = GateModelTaskResult(
    **{
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
    }
)


class DummyProgramSimulator(BraketSimulator):
    def run(
        self,
        openqasm_ir: Program,
        shots: int = 0,
        batch_size: int = 1,
    ) -> GateModelTaskResult:
        return GATE_MODEL_RESULT

    def execution_manager(self, *args, **kwargs):
        return LocalExecutionManager(self, *args, **kwargs)

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
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
            }
        )


class DummyProgramSleepSimulator(BraketSimulator):
    def run(
        self,
        openqasm_ir: Program,
        shots: int = 0,
        batch_size: int = 1,
    ) -> GateModelTaskResult:
        sleep(5)
        return GATE_MODEL_RESULT

    def execution_manager(self, *args, **kwargs):
        return LocalExecutionManager(self, *args, **kwargs)

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
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
            }
        )


class DummyExceptionSimulator(BraketSimulator):
    def run(
        self,
        openqasm_ir: Program,
        shots: int = 0,
        batch_size: int = 1,
    ) -> GateModelTaskResult:
        raise Exception("Catch in main thread")

    def execution_manager(self, *args, **kwargs):
        return LocalExecutionManager(self, *args, **kwargs)

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
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
            }
        )


def test_state():
    task = LocalQuantumTask(RESULT)
    assert task.state() == "CREATED"


def test_result():
    task = LocalQuantumTask(RESULT)
    result = task.result()
    assert result == RESULT


def test_result_from_sim():
    sim = LocalSimulator(DummyProgramSimulator())
    local_quantum_task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    result = local_quantum_task.result()
    assert result == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_exception_from_sim():
    sim = LocalSimulator(DummyExceptionSimulator())
    local_quantum_task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    with pytest.raises(Exception, match="Catch in main thread"):
        local_quantum_task.result()


def test_result_without_passing_in_result():
    sim = LocalSimulator(DummyProgramSimulator())
    local_quantum_task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    result = local_quantum_task.result()
    assert result == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_running():
    sim = LocalSimulator(DummyProgramSleepSimulator())
    local_quantum_task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    assert local_quantum_task.state() == "RUNNING"


@pytest.mark.xfail(raises=NotImplementedError)
def test_cancel():
    task = LocalQuantumTask(RESULT)
    task.cancel()


def test_cancel_task_without_result():
    sim = LocalSimulator(DummyProgramSimulator())
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    with pytest.raises(NotImplementedError, match="LocalQuantumTask does not support cancelling"):
        task.cancel()


def test_async():
    sim = LocalSimulator(DummyProgramSimulator())
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    assert isinstance(task.async_result(), asyncio.Task)


def test_async_without_result():
    sim = LocalSimulator(DummyProgramSimulator())
    local_quantum_task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    local_quantum_task.async_result()
    local_quantum_task._thread.join()
    assert _wrap_results(
        local_quantum_task._task._result
    ) == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)
    assert local_quantum_task.state() == "COMPLETED"
