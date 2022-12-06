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

import boto3

from braket.aws import AwsDevice, AwsSession
from braket.circuits import Circuit
from braket.tracking import Tracker
from braket.tracking.tracker import MIN_SIMULATOR_DURATION


def test_qpu_tracking():
    circuit = Circuit().h(0)
    with Tracker() as t:
        AwsDevice("arn:aws:braket:::device/qpu/ionq/ionQdevice").run(circuit, shots=10)
        AwsDevice("arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy").run(circuit, shots=10)
        AwsDevice("arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-2").run(circuit, shots=10)

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


def test_all_devices_price_search():
    devices = AwsDevice.get_devices(statuses=["ONLINE", "OFFLINE"])

    tasks = {}
    for region in AwsDevice.REGIONS:
        s = AwsSession(boto3.Session(region_name=region))
        for device in devices:
            try:
                s.get_device(device.arn)

                # If we are here, device can create tasks in region
                details = {
                    "shots": 100,
                    "device": device.arn,
                    "billed_duration": MIN_SIMULATOR_DURATION,
                    "job_task": False,
                    "status": "COMPLETED",
                }
                tasks[f"task:for:{device.name}:{region}"] = details.copy()
                details["job_task"] = True
                tasks[f"jobtask:for:{device.name}:{region}"] = details
            except s.braket_client.exceptions.ResourceNotFoundException:
                # device does not exist in region, so nothing to test
                pass

    t = Tracker()
    t._resources = tasks

    assert t.qpu_tasks_cost() + t.simulator_tasks_cost() > 0
