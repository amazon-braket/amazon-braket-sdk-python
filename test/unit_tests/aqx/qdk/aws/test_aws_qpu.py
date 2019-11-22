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

from unittest.mock import Mock, patch

import pytest
from aqx.qdk.aws import AwsQpu, AwsQpuArns
from aqx.qdk.circuits import Circuit
from common_test_utils import MockDevices


@pytest.fixture
def qpu():
    def _qpu(arn):
        mock_session = Mock()
        mock_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1
        return AwsQpu(arn, mock_session)

    return _qpu


@pytest.fixture
def s3_destination_folder():
    return ("bucket-foo", "key-bar")


@pytest.fixture
def circuit():
    return Circuit().h(0)


def test_qpu_refresh_metadata_success():
    mock_session = Mock()
    mock_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1
    qpu = AwsQpu(AwsQpuArns.RIGETTI, mock_session)
    assert qpu.arn == MockDevices.MOCK_RIGETTI_QPU_1.get("arn")
    assert qpu.name == MockDevices.MOCK_RIGETTI_QPU_1.get("name")
    assert qpu.qubit_count == MockDevices.MOCK_RIGETTI_QPU_1.get("qubitCount")
    assert qpu.connectivity_graph == MockDevices.MOCK_RIGETTI_QPU_1.get("connectivity").get(
        "connectivityGraph"
    )
    assert qpu.supported_quantum_operations == MockDevices.MOCK_RIGETTI_QPU_1.get(
        "supportedQuantumOperations"
    )
    assert qpu.status == MockDevices.MOCK_RIGETTI_QPU_1.get("status")
    assert qpu.status_reason is None

    # describe_qpus now returns new metadata
    mock_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_2
    qpu.refresh_metadata()
    assert qpu.arn == MockDevices.MOCK_RIGETTI_QPU_2.get("arn")
    assert qpu.name == MockDevices.MOCK_RIGETTI_QPU_2.get("name")
    assert qpu.qubit_count == MockDevices.MOCK_RIGETTI_QPU_2.get("qubitCount")
    assert qpu.connectivity_graph == MockDevices.MOCK_RIGETTI_QPU_2.get("connectivity").get(
        "connectivityGraph"
    )
    assert qpu.supported_quantum_operations == MockDevices.MOCK_RIGETTI_QPU_2.get(
        "supportedQuantumOperations"
    )
    assert qpu.status == MockDevices.MOCK_RIGETTI_QPU_2.get("status")
    assert qpu.status_reason == MockDevices.MOCK_RIGETTI_QPU_2.get("statusReason")


def test_qpu_refresh_metadata_error():
    mock_session = Mock()
    err_message = "nooo!"
    mock_session.get_qpu_metadata.side_effect = RuntimeError(err_message)
    with pytest.raises(RuntimeError) as excinfo:
        AwsQpu(AwsQpuArns.RIGETTI, mock_session)
    assert err_message in str(excinfo.value)


def test_equality(qpu):
    qpu_1 = qpu(AwsQpuArns.RIGETTI)
    qpu_2 = qpu(AwsQpuArns.RIGETTI)
    mock_session = Mock()
    mock_session.get_qpu_metadata.return_value = MockDevices.MOCK_IONQ_QPU
    other_qpu = AwsQpu(AwsQpuArns.IONQ, mock_session)
    non_qpu = "HI"

    assert qpu_1 == qpu_2
    assert qpu_1 is not qpu_2
    assert qpu_1 != other_qpu
    assert qpu_1 != non_qpu


def test_repr(qpu):
    qpu = qpu(AwsQpuArns.RIGETTI)
    expected = "QPU('name': {}, 'arn': {})".format(qpu.name, qpu.arn)
    assert repr(qpu) == expected


@patch("aqx.qdk.aws.aws_quantum_task.AwsQuantumTask.from_circuit")
def test_run_with_positional_args(aws_quantum_task_mock, qpu, circuit, s3_destination_folder):
    _run_and_assert(aws_quantum_task_mock, qpu, [circuit, s3_destination_folder], {})


@patch("aqx.qdk.aws.aws_quantum_task.AwsQuantumTask.from_circuit")
def test_run_with_kwargs(aws_quantum_task_mock, qpu, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        qpu,
        [],
        {"circuit": circuit, "s3_destination_folder": s3_destination_folder},
    )


@patch("aqx.qdk.aws.aws_quantum_task.AwsQuantumTask.from_circuit")
def test_run_with_positional_args_and_kwargs(
    aws_quantum_task_mock, qpu, circuit, s3_destination_folder
):
    _run_and_assert(aws_quantum_task_mock, qpu, [circuit, s3_destination_folder], {"shots": 100})


def _run_and_assert(aws_quantum_task_mock, qpu, run_args, run_kwargs):
    task_mock = Mock()
    aws_quantum_task_mock.return_value = task_mock

    qpu = qpu("test_arn")
    task = qpu.run(*run_args, **run_kwargs)
    assert task == task_mock
    aws_quantum_task_mock.assert_called_with(qpu._aws_session, qpu.arn, *run_args, **run_kwargs)
