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

from unittest.mock import Mock

import pytest
from aqx.qdk.aws.aws_qpu import AwsQpu
from aqx.qdk.devices.qpu.qpu_type import QpuType
from common_test_utils import MockDevices


@pytest.fixture
def qpu():
    def _qpu(arn):
        mock_session = Mock()
        mock_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1
        return AwsQpu(arn, mock_session)

    return _qpu


def test_qpu_refresh_metadata_success():
    mock_session = Mock()
    mock_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1
    qpu = AwsQpu(QpuType.RIGETTI, mock_session)
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
        AwsQpu(QpuType.RIGETTI, mock_session)
    assert err_message in str(excinfo.value)


def test_equality(qpu):
    qpu_1 = qpu(QpuType.RIGETTI)
    qpu_2 = qpu(QpuType.RIGETTI)
    mock_session = Mock()
    mock_session.get_qpu_metadata.return_value = MockDevices.MOCK_IONQ_QPU
    other_qpu = AwsQpu(QpuType.IONQ, mock_session)
    non_qpu = "HI"

    assert qpu_1 == qpu_2
    assert qpu_1 is not qpu_2
    assert qpu_1 != other_qpu
    assert qpu_1 != non_qpu


def test_repr(qpu):
    qpu = qpu(QpuType.RIGETTI)
    expected = "QPU('name': {}, 'arn': {})".format(qpu.name, qpu.arn)
    assert repr(qpu) == expected
