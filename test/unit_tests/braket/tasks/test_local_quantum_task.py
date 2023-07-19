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

from braket.circuits import Circuit
from braket.device_schema import DeviceCapabilities
from braket.simulator import BraketSimulator
from braket.task_result import TaskMetadata, GateModelTaskResult
from braket.tasks import GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask

RESULT = GateModelQuantumTaskResult(
    task_metadata=TaskMetadata(**{"id": str(uuid.uuid4()), "deviceId": "default", "shots": 100}),
    additional_metadata=None,
    measurements=np.array([[0, 1], [1, 0]]),
    measured_qubits=[0, 1],
    result_types=None,
    values=None,
)


class DummyCircuitSimulator(BraketSimulator):
    def run(
        self,
        circuit: Circuit,
        *args,
        **kwargs,
    ) -> GateModelTaskResult:
        sleep(5)
        return GateModelTaskResult(
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

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
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
            }
        )


def test_id():
    # Task ID is valid UUID
    TASK = LocalQuantumTask(RESULT)
    TASK.result()
    uuid.UUID(TASK.id)


def test_state():
    TASK = LocalQuantumTask(RESULT)
    assert TASK.state() == "CREATED"


def test_result():
    TASK = LocalQuantumTask(RESULT)
    result = TASK.result()
    assert result == RESULT
    assert RESULT.task_metadata.id == TASK.id

def test_cancel():
    sim = DummyCircuitSimulator()
    task = LocalQuantumTask().create(Circuit().h(0), sim, shots=1)
    sleep(1)
    task.cancel()
    assert task.state() == "CANCELLING"


def test_async():
    TASK = LocalQuantumTask(RESULT)
    assert isinstance(TASK.async_result(), asyncio.Task)


def test_str():
    TASK = LocalQuantumTask(RESULT)
    expected = "LocalQuantumTask('id':{})".format(TASK.id)
    assert str(TASK) == expected
