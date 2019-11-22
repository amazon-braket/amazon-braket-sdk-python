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

import json
from unittest.mock import Mock

import pytest
from aqx.qdk.aws import AwsQpuArns, AwsQuantumSimulatorArns, AwsSession
from botocore.exceptions import ClientError
from common_test_utils import MockDevices

TEST_S3_OBJ_CONTENTS = {
    "TaskMetadata": {
        "Id": "UUID_blah",
        "Status": "COMPLETED",
        "BackendArn": AwsQpuArns.RIGETTI,
        "CwLogGroupArn": "blah",
        "Program": "....",
        "CreatedAt": "02/12/22 21:23",
        "UpdatedAt": "02/13/22 21:23",
    }
}


@pytest.fixture
def aws_session():
    return AwsSession(boto_session=Mock(), aqx_client=Mock())


def test_retrieve_s3_object_body_success():
    bucket_name = "aqx-integ-test"
    filename = "tasks/test_task_1.json"

    boto_session = Mock()
    mock_resource = Mock()
    boto_session.resource.return_value = mock_resource
    mock_object = Mock()
    mock_resource.Object.return_value = mock_object
    mock_body_object = Mock()
    mock_object.get.return_value = {"Body": mock_body_object}
    mock_read_object = Mock()
    mock_body_object.read.return_value = mock_read_object
    mock_read_object.decode.return_value = json.dumps(TEST_S3_OBJ_CONTENTS)
    json.dumps(TEST_S3_OBJ_CONTENTS)

    aws_session = AwsSession(boto_session=boto_session)
    return_value = aws_session.retrieve_s3_object_body(bucket_name, filename)
    assert return_value == json.dumps(TEST_S3_OBJ_CONTENTS)


@pytest.mark.xfail(raises=ClientError)
def test_retrieve_s3_object_body_client_error():
    bucket_name = "aqx-integ-test"
    filename = "tasks/test_task_1.json"

    boto_session = Mock()
    mock_resource = Mock()
    boto_session.resource.return_value = mock_resource
    mock_object = Mock()
    mock_resource.Object.return_value = mock_object
    mock_object.get.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "NoSuchKey"}}, "Operation"
    )
    aws_session = AwsSession(boto_session=boto_session)
    aws_session.retrieve_s3_object_body(bucket_name, filename)


def test_get_qpu_metadata_success():
    boto_session = Mock()
    aqx_client = Mock()
    aqx_client.describe_qpus.return_value = {"qpus": [MockDevices.MOCK_RIGETTI_QPU_1]}
    aws_session = AwsSession(boto_session=boto_session, aqx_client=aqx_client)
    qpu_metadata = aws_session.get_qpu_metadata(AwsQpuArns.RIGETTI)
    assert qpu_metadata == MockDevices.MOCK_RIGETTI_QPU_1


# TODO: revisit once we actually use boto3
@pytest.mark.xfail(raises=ClientError)
def test_get_qpu_metadata_client_error():
    boto_session = Mock()
    aqx_client = Mock()
    aqx_client.describe_qpus.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "NoSuchQpu"}}, "Operation"
    )
    aws_session = AwsSession(boto_session=boto_session, aqx_client=aqx_client)
    aws_session.get_qpu_metadata(AwsQpuArns.RIGETTI)


def test_get_simulator_metadata_success():
    boto_session = Mock()
    aqx_client = Mock()
    aqx_client.describe_quantum_simulators.return_value = {
        "quantumSimulators": [MockDevices.MOCK_QS1_SIMULATOR_1]
    }
    aws_session = AwsSession(boto_session=boto_session, aqx_client=aqx_client)
    simulator_metadata = aws_session.get_simulator_metadata(AwsQuantumSimulatorArns.QS1)
    assert simulator_metadata == MockDevices.MOCK_QS1_SIMULATOR_1


# TODO: revisit once we actually use boto3
@pytest.mark.xfail(raises=ClientError)
def test_get_simulator_metadata_client_error():
    boto_session = Mock()
    aqx_client = Mock()
    aqx_client.describe_quantum_simulators.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "NoSuchSimulator"}}, "Operation"
    )
    aws_session = AwsSession(boto_session=boto_session, aqx_client=aqx_client)
    aws_session.get_simulator_metadata(AwsQuantumSimulatorArns.QS1)


def test_cancel_quantum_task(aws_session):
    arn = "foo:bar:arn"
    aws_session.aqx_client.cancel_quantum_task.return_value = {"quantumTaskArn": arn}

    assert aws_session.cancel_quantum_task(arn) is None
    aws_session.aqx_client.cancel_quantum_task.assert_called_with(quantumTaskArn=arn)


def test_create_quantum_task(aws_session):
    arn = "foo:bar:arn"
    aws_session.aqx_client.create_quantum_task.return_value = {"quantumTaskArn": arn}

    kwargs = {
        "backendArn": "arn:aws:us-west-2:abc:xyz:abc",
        "cwLogGroupArn": "arn:aws:us-west-2:abc:xyz:abc",
        "destinationUrl": "http://s3-us-west-2.amazonaws.com/task-output-derebolt-1/output.json",
        "program": {"ir": '{"instructions":[]}', "qubitCount": 4},
    }
    assert aws_session.create_quantum_task(**kwargs) == arn
    aws_session.aqx_client.create_quantum_task.assert_called_with(**kwargs)


def test_get_quantum_task(aws_session):
    arn = "foo:bar:arn"
    return_value = {"quantumTaskArn": arn}
    aws_session.aqx_client.get_quantum_task.return_value = return_value

    assert aws_session.get_quantum_task(arn) == return_value
    aws_session.aqx_client.get_quantum_task.assert_called_with(quantumTaskArn=arn)
