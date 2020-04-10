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

from typing import Any, Dict, Optional
from unittest.mock import Mock

import braket.ir as ir
import pytest
from braket.annealing import Problem, ProblemType
from braket.circuits import Circuit
from braket.devices import LocalSimulator, local_simulator
from braket.devices.braket_simulator import BraketSimulator
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult

GATE_MODEL_RESULT = {
    "StateVector": {
        "00": complex(0.2, 0.2),
        "01": complex(0.3, 0.1),
        "10": complex(0.1, 0.3),
        "11": complex(0.2, 0.2),
    },
    "Measurements": [[0, 0], [0, 1], [0, 1], [0, 1]],
    "TaskMetadata": {"Id": "UUID_blah_1", "Status": "COMPLETED"},
}

ANNEALING_RESULT = {
    "Solutions": [[-1, -1, -1, -1], [1, -1, 1, 1], [1, -1, -1, 1]],
    "VariableCount": 4,
    "Values": [0.0, 1.0, 2.0],
    "SolutionCounts": None,
    "ProblemType": "ising",
    "Foo": {"Bar": "Baz"},
    "TaskMetadata": {"Id": "UUID_blah_1", "Status": "COMPLETED", "Shots": 5,},
}


class DummyCircuitSimulator(BraketSimulator):
    def run(
        self, program: ir.jaqcd.Program, qubits: int, shots: Optional[int], *args, **kwargs
    ) -> Dict[str, Any]:
        self._shots = shots
        self._qubits = qubits
        return GATE_MODEL_RESULT

    def assert_shots(self, shots):
        assert self._shots == shots

    def assert_qubits(self, qubits):
        assert self._qubits == qubits


class DummyAnnealingSimulator(BraketSimulator):
    def run(self, problem: ir.annealing.Problem, *args, **kwargs) -> Dict[str, Any]:
        return ANNEALING_RESULT


mock_entry = Mock()
mock_entry.load.return_value = DummyCircuitSimulator
local_simulator._simulator_devices = {"dummy": mock_entry}


def test_load_from_entry_point():
    sim = LocalSimulator("dummy")
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    assert task.result() == GateModelQuantumTaskResult.from_dict(GATE_MODEL_RESULT)


def test_run_gate_model():
    dummy = DummyCircuitSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    dummy.assert_shots(10)
    dummy.assert_qubits(2)
    assert task.result() == GateModelQuantumTaskResult.from_dict(GATE_MODEL_RESULT)


def test_run_annealing():
    sim = LocalSimulator(DummyAnnealingSimulator())
    task = sim.run(Problem(ProblemType.ISING))
    assert task.result() == AnnealingQuantumTaskResult.from_dict(ANNEALING_RESULT)


def test_registered_backends():
    assert LocalSimulator.registered_backends() == {"dummy"}


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
