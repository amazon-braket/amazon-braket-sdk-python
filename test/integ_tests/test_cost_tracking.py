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

from datetime import timedelta

from braket.annealing import Problem, ProblemType
from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.tracking import Tracker
from braket.tracking.tracker import MIN_SIMULATOR_DURATION


def test_qpu_tracking():
    problem = Problem(ProblemType("QUBO"), linear={35: 1}, quadratic={(35, 36): -1})
    device = AwsDevice("arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6")
    other_device = AwsDevice("arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6")

    device.run(problem, shots=50).result()
    with Tracker() as t:
        device.run(problem, shots=100).result()
        other_device.run(problem, shots=400).result()
        t_partial_cost = t.qpu_tasks_cost()
        assert t_partial_cost > 0
        with Tracker() as s:
            task = device.run(problem, shots=200)
            assert s.quantum_tasks_statistics() == {
                "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6": {
                    "shots": 200,
                    "tasks": {"CREATED": 1},
                }
            }
            task.result()

    assert s.simulator_tasks_cost() == 0
    assert t.simulator_tasks_cost() == 0

    assert s.quantum_tasks_statistics() == {
        "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6": {"shots": 200, "tasks": {"COMPLETED": 1}}
    }
    assert t.quantum_tasks_statistics() == {
        "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6": {"shots": 300, "tasks": {"COMPLETED": 2}},
        "arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6": {
            "shots": 400,
            "tasks": {"COMPLETED": 1},
        },
    }

    assert s.qpu_tasks_cost() > 0
    assert t.qpu_tasks_cost() > s.qpu_tasks_cost()
    assert t.qpu_tasks_cost() > t_partial_cost

    circuit = Circuit().h(0)
    with Tracker() as t:
        AwsDevice("arn:aws:braket:::device/qpu/ionq/ionQdevice").run(circuit, shots=10)
        AwsDevice("arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy").run(circuit, shots=10)
        AwsDevice("arn:aws:braket:::device/qpu/rigetti/Aspen-11").run(circuit, shots=10)

    assert t.qpu_tasks_cost() > 0


def test_simulator_tracking():
    circuit = Circuit().h(0).cnot(0, 1)
    device = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")

    with Tracker() as t:
        task0 = device.run(circuit, shots=100)
        task1 = device.run(circuit, shots=100)
        assert t.quantum_tasks_statistics() == {
            "arn:aws:braket:::device/quantum-simulator/amazon/sv1": {
                "shots": 200,
                "tasks": {"CREATED": 2},
            }
        }
        task0.result()
        task1.result()

        device.run(circuit, shots=100).cancel()

    quantum_stats = t.quantum_tasks_statistics()[device.arn]
    assert quantum_stats["shots"] == 300
    assert quantum_stats["tasks"] == {"COMPLETED": 2, "CANCELLING": 1}
    assert quantum_stats["execution_duration"] > timedelta(0)
    assert quantum_stats["billed_execution_duration"] >= quantum_stats["execution_duration"]
    assert quantum_stats["billed_execution_duration"] >= 2 * MIN_SIMULATOR_DURATION

    assert t.qpu_tasks_cost() == 0
    assert t.simulator_tasks_cost() > 0
