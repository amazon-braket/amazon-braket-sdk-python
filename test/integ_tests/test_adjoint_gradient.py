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

import pytest

from braket.aws import AwsQuantumTask, AwsQuantumTaskBatch
from braket.circuits import Circuit, Observable
from braket.parametric import FreeParameter


@pytest.fixture
def sv1_device():
    return "arn:aws:braket:::device/quantum-simulator/amazon/sv1"


def test_adjoint_gradient_quantum_task_with_nested_targets(
    aws_session, s3_destination_folder, sv1_device
):
    theta = FreeParameter("theta")
    inputs = {"theta": 0.2}
    circ = (
        Circuit()
        .rx(0, theta)
        .adjoint_gradient(
            observable=(-2 * Observable.Y()) @ (3 * Observable.I())
            + 0.75 * Observable.Y() @ Observable.Z(),
            target=[[0, 1], [2, 3]],
            parameters=["theta"],
        )
    )

    expected_openqasm = (
        "OPENQASM 3.0;\n"
        "input float theta;\n"
        "qubit[4] q;\n"
        "rx(theta) q[0];\n"
        "#pragma braket result adjoint_gradient expectation(-6 * y(q[0]) @ i(q[1]) + 0.75 * "
        "y(q[2]) @ z(q[3])) theta"
    )

    gradient_task = AwsQuantumTask.create(
        aws_session=aws_session,
        task_specification=circ,
        s3_destination_folder=s3_destination_folder,
        device_arn=sv1_device,
        shots=0,
        inputs=inputs,
    )

    assert gradient_task.result().additional_metadata.action.source == expected_openqasm
    assert gradient_task.result().values == [
        {"expectation": 1.1920159847703675, "gradient": {"theta": 5.880399467047451}}
    ]
    assert gradient_task.result().result_types[0].type.observable == "-6 * y @ i + 0.75 * y @ z"
    assert gradient_task.result().additional_metadata.action.inputs == inputs


def test_adjoint_gradient_with_standard_observable_terms(
    aws_session, s3_destination_folder, sv1_device
):
    theta = FreeParameter("theta")
    inputs = {"theta": 0.2}
    circ = (
        Circuit()
        .rx(0, theta)
        .adjoint_gradient(
            observable=(2 * Observable.X()) + (3 * Observable.Y()) - Observable.Z(),
            target=[[0], [1], [2]],
            parameters=["theta"],
        )
    )

    expected_openqasm = (
        "OPENQASM 3.0;\n"
        "input float theta;\n"
        "qubit[3] q;\n"
        "rx(theta) q[0];\n"
        "#pragma braket result adjoint_gradient expectation(2 * x(q[0]) + 3 * y(q[1]) "
        "- 1 * z(q[2])) theta"
    )

    gradient_task = AwsQuantumTask.create(
        aws_session=aws_session,
        task_specification=circ,
        s3_destination_folder=s3_destination_folder,
        device_arn=sv1_device,
        shots=0,
        inputs=inputs,
    )

    assert gradient_task.result().additional_metadata.action.source == expected_openqasm
    assert gradient_task.result().values == [{"expectation": -1.0, "gradient": {"theta": 0.0}}]
    assert gradient_task.result().result_types[0].type.observable == "2 * x + 3 * y - 1 * z"
    assert gradient_task.result().additional_metadata.action.inputs == inputs


def test_adjoint_gradient_with_batch_circuits(aws_session, s3_destination_folder, sv1_device):
    theta = FreeParameter("theta")

    inputs = {"theta": 0.2}
    circ_1 = (
        Circuit()
        .rx(0, theta)
        .adjoint_gradient(
            observable=(2 * Observable.Y()) @ (3 * Observable.I()),
            target=[0, 1],
            parameters=["theta"],
        )
    )
    circ_2 = (
        Circuit()
        .rx(0, theta)
        .adjoint_gradient(
            observable=(-2 * Observable.Y()) @ (3 * Observable.I())
            + 0.75 * Observable.Y() @ Observable.Z(),
            target=[[0, 1], [0, 1]],
            parameters=["theta"],
        )
    )

    expected_openqasm = [
        (
            "OPENQASM 3.0;\n"
            "input float theta;\n"
            "qubit[2] q;\n"
            "rx(theta) q[0];\n"
            "#pragma braket result adjoint_gradient expectation(6 * y(q[0]) @ i(q[1])) theta"
        ),
        (
            "OPENQASM 3.0;\n"
            "input float theta;\n"
            "qubit[2] q;\n"
            "rx(theta) q[0];\n"
            "#pragma braket result adjoint_gradient expectation(-6 * y(q[0]) @ i(q[1]) + 0.75 * "
            "y(q[0]) @ z(q[1])) theta"
        ),
    ]

    expected_result_values = [
        [{"expectation": -1.1920159847703675, "gradient": {"theta": -5.880399467047451}}],
        [{"expectation": 1.0430139866740715, "gradient": {"theta": 5.145349533666519}}],
    ]
    expected_observables = ["6 * y @ i", "-6 * y @ i + 0.75 * y @ z"]

    gradient_batch_tasks = AwsQuantumTaskBatch(
        aws_session=aws_session,
        device_arn=sv1_device,
        task_specifications=[circ_1, circ_2],
        shots=0,
        max_parallel=1,
        s3_destination_folder=s3_destination_folder,
        inputs=inputs,
    )

    for i in range(2):
        assert (
            gradient_batch_tasks.tasks[i].result().additional_metadata.action.source
            == expected_openqasm[i]
        )
        assert gradient_batch_tasks.tasks[i].result().values == expected_result_values[i]
        assert (
            gradient_batch_tasks.tasks[i].result().result_types[0].type.observable
            == expected_observables[i]
        )
        assert gradient_batch_tasks.tasks[i].result().additional_metadata.action.inputs == inputs
