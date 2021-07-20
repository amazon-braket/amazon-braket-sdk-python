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
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

import braket._schemas as braket_schemas
import braket._sdk as braket_sdk
from braket.aws import AwsSession

TEST_S3_OBJ_CONTENTS = {
    "TaskMetadata": {
        "Id": "blah",
    }
}


@pytest.fixture
def boto_session():
    _boto_session = Mock()
    _boto_session.region_name = "us-west-2"
    return _boto_session


@pytest.fixture
def aws_session(boto_session):
    return AwsSession(boto_session=boto_session, braket_client=Mock())


@pytest.fixture
def get_job_response():
    return {
        "algorithmSpecification": {
            "scriptModeConfig": {
                "entryPoint": "my_file:start_here",
                "s3Uri": "s3://amazon-braket-jobs/job-path/my_file.py",
            }
        },
        "checkpointConfig": {
            "localPath": "/opt/omega/checkpoints",
            "s3Uri": "s3://amazon-braket-jobs/job-path/checkpoints",
        },
        "instanceConfig": {
            "instanceCount": 1,
            "instanceType": "ml.m5.large",
            "volumeSizeInGb": 1,
        },
        "jobArn": "arn:aws:braket:us-west-2:875981177017:job/job-test-20210628140446",
        "jobName": "job-test-20210628140446",
        "outputDataConfig": {"s3Path": "s3://amazon-braket-jobs/job-path/output"},
        "roleArn": "arn:aws:iam::875981177017:role/AmazonBraketJobRole",
        "status": "RUNNING",
    }


@pytest.fixture
def resource_not_found_response():
    return {
        "Error": {
            "Code": "ResourceNotFoundException",
            "Message": "unit-test-error",
        }
    }


@pytest.fixture
def throttling_response():
    return {
        "Error": {
            "Code": "ThrottlingException",
            "Message": "unit-test-error",
        }
    }


def test_initializes_boto_client_if_required(boto_session):
    AwsSession(boto_session=boto_session)
    boto_session.client.assert_called_with("braket", config=None)


def test_uses_supplied_braket_client():
    boto_session = Mock()
    boto_session.region_name = "foobar"
    braket_client = Mock()
    aws_session = AwsSession(boto_session=boto_session, braket_client=braket_client)
    assert aws_session.braket_client == braket_client


def test_config(boto_session):
    config = Mock()
    AwsSession(boto_session=boto_session, config=config)
    boto_session.client.assert_called_with("braket", config=config)


@patch("os.path.exists")
@pytest.mark.parametrize(
    "metadata_file_exists, initial_user_agent",
    [
        (True, None),
        (False, None),
        (True, ""),
        (False, ""),
        (True, "Boto3/1.17.18 Python/3.7.10"),
        (False, "Boto3/1.17.18 Python/3.7.10 exec-env/AWS_Lambda_python3.7"),
    ],
)
def test_populates_user_agent(os_path_exists_mock, metadata_file_exists, initial_user_agent):
    boto_session = Mock()
    boto_session.region_name = "foobar"
    braket_client = Mock()
    braket_client._client_config.user_agent = initial_user_agent
    nbi_metadata_path = "/opt/ml/metadata/resource-metadata.json"
    os_path_exists_mock.return_value = metadata_file_exists
    aws_session = AwsSession(boto_session=boto_session, braket_client=braket_client)
    expected_user_agent = (
        f"{initial_user_agent} BraketSdk/{braket_sdk.__version__} "
        f"BraketSchemas/{braket_schemas.__version__} "
        f"NotebookInstance/{0 if metadata_file_exists else None}"
    )
    os_path_exists_mock.assert_called_with(nbi_metadata_path)
    assert aws_session.braket_client._client_config.user_agent == expected_user_agent


def test_retrieve_s3_object_body_success(boto_session):
    bucket_name = "braket-integ-test"
    filename = "tasks/test_task_1.json"

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
    boto_session.resource.assert_called_with("s3", config=None)

    config = Mock()
    AwsSession(boto_session=boto_session, config=config).retrieve_s3_object_body(
        bucket_name, filename
    )
    boto_session.resource.assert_called_with("s3", config=config)


@pytest.mark.xfail(raises=ClientError)
def test_retrieve_s3_object_body_client_error(boto_session):
    bucket_name = "braket-integ-test"
    filename = "tasks/test_task_1.json"

    mock_resource = Mock()
    boto_session.resource.return_value = mock_resource
    mock_object = Mock()
    mock_resource.Object.return_value = mock_object
    mock_object.get.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "NoSuchKey"}}, "Operation"
    )
    aws_session = AwsSession(boto_session=boto_session)
    aws_session.retrieve_s3_object_body(bucket_name, filename)


def test_create_logs_client(boto_session):
    config = Mock()
    aws_session = AwsSession(boto_session=boto_session, config=config)
    aws_session.create_logs_client()
    boto_session.client.assert_called_with("logs", config=config)


def test_get_device(boto_session):
    braket_client = Mock()
    return_val = {"deviceArn": "arn1", "deviceName": "name1"}
    braket_client.get_device.return_value = return_val
    aws_session = AwsSession(boto_session=boto_session, braket_client=braket_client)
    metadata = aws_session.get_device("arn1")
    assert return_val == metadata


def test_cancel_quantum_task(aws_session):
    arn = "foo:bar:arn"
    aws_session.braket_client.cancel_quantum_task.return_value = {"quantumTaskArn": arn}

    assert aws_session.cancel_quantum_task(arn) is None
    aws_session.braket_client.cancel_quantum_task.assert_called_with(quantumTaskArn=arn)


def test_create_quantum_task(aws_session):
    arn = "foo:bar:arn"
    aws_session.braket_client.create_quantum_task.return_value = {"quantumTaskArn": arn}

    kwargs = {
        "backendArn": "arn:aws:us-west-2:abc:xyz:abc",
        "cwLogGroupArn": "arn:aws:us-west-2:abc:xyz:abc",
        "destinationUrl": "http://s3-us-west-2.amazonaws.com/task-output-derebolt-1/output.json",
        "program": {"ir": '{"instructions":[]}', "qubitCount": 4},
    }
    assert aws_session.create_quantum_task(**kwargs) == arn
    aws_session.braket_client.create_quantum_task.assert_called_with(**kwargs)


def test_get_quantum_task(aws_session):
    arn = "foo:bar:arn"
    return_value = {"quantumTaskArn": arn}
    aws_session.braket_client.get_quantum_task.return_value = return_value

    assert aws_session.get_quantum_task(arn) == return_value
    aws_session.braket_client.get_quantum_task.assert_called_with(quantumTaskArn=arn)


def test_get_quantum_task_retry(aws_session, throttling_response, resource_not_found_response):
    arn = "foo:bar:arn"
    return_value = {"quantumTaskArn": arn}

    aws_session.braket_client.get_quantum_task.side_effect = [
        ClientError(resource_not_found_response, "unit-test"),
        ClientError(throttling_response, "unit-test"),
        return_value,
    ]

    assert aws_session.get_quantum_task(arn) == return_value
    aws_session.braket_client.get_quantum_task.assert_called_with(quantumTaskArn=arn)
    aws_session.braket_client.get_quantum_task.call_count == 3


def test_get_quantum_task_fail_after_retries(
    aws_session, throttling_response, resource_not_found_response
):
    aws_session.braket_client.get_quantum_task.side_effect = [
        ClientError(resource_not_found_response, "unit-test"),
        ClientError(throttling_response, "unit-test"),
        ClientError(throttling_response, "unit-test"),
    ]

    with pytest.raises(ClientError):
        aws_session.get_quantum_task("some-arn")
    aws_session.braket_client.get_quantum_task.call_count == 3


def test_get_quantum_task_does_not_retry_other_exceptions(aws_session):
    exception_response = {
        "Error": {
            "Code": "SomeOtherException",
            "Message": "unit-test-error",
        }
    }

    aws_session.braket_client.get_quantum_task.side_effect = [
        ClientError(exception_response, "unit-test"),
    ]

    with pytest.raises(ClientError):
        aws_session.get_quantum_task("some-arn")
    aws_session.braket_client.get_quantum_task.call_count == 1


def test_get_job(aws_session, get_job_response):
    arn = "arn:aws:braket:us-west-2:1234567890:job/job-name"
    aws_session.braket_client.get_job.return_value = get_job_response

    assert aws_session.get_job(arn) == get_job_response
    aws_session.braket_client.get_job.assert_called_with(jobArn=arn)


def test_get_job_retry(
    aws_session, get_job_response, throttling_response, resource_not_found_response
):
    arn = "arn:aws:braket:us-west-2:1234567890:job/job-name"

    aws_session.braket_client.get_job.side_effect = [
        ClientError(resource_not_found_response, "unit-test"),
        ClientError(throttling_response, "unit-test"),
        get_job_response,
    ]

    assert aws_session.get_job(arn) == get_job_response
    aws_session.braket_client.get_job.assert_called_with(jobArn=arn)
    assert aws_session.braket_client.get_job.call_count == 3


def test_get_job_fail_after_retries(aws_session, throttling_response, resource_not_found_response):
    arn = "arn:aws:braket:us-west-2:1234567890:job/job-name"

    aws_session.braket_client.get_job.side_effect = [
        ClientError(resource_not_found_response, "unit-test"),
        ClientError(throttling_response, "unit-test"),
        ClientError(throttling_response, "unit-test"),
    ]

    with pytest.raises(ClientError):
        aws_session.get_job(arn)
    aws_session.braket_client.get_job.assert_called_with(jobArn=arn)
    assert aws_session.braket_client.get_job.call_count == 3


def test_get_job_does_not_retry_other_exceptions(aws_session):
    arn = "arn:aws:braket:us-west-2:1234567890:job/job-name"
    exception_response = {
        "Error": {
            "Code": "SomeOtherException",
            "Message": "unit-test-error",
        }
    }

    aws_session.braket_client.get_job.side_effect = [
        ClientError(exception_response, "unit-test"),
    ]

    with pytest.raises(ClientError):
        aws_session.get_job(arn)
    aws_session.braket_client.get_job.assert_called_with(jobArn=arn)
    assert aws_session.braket_client.get_job.call_count == 1


def test_cancel_job(aws_session):
    arn = "arn:aws:braket:us-west-2:1234567890:job/job-name"
    cancel_job_response = {
        "ResponseMetadata": {
            "RequestId": "857b0893-2073-4ad6-b828-744af8400dfe",
            "HTTPStatusCode": 200,
        },
        "cancellationStatus": "CANCELLING",
        "jobArn": "arn:aws:braket:us-west-2:1234567890:job/job-name",
    }
    aws_session.braket_client.cancel_job.return_value = cancel_job_response

    assert aws_session.cancel_job(arn) == cancel_job_response
    aws_session.braket_client.cancel_job.assert_called_with(jobArn=arn)


@pytest.mark.parametrize(
    "exception_type",
    [
        "ResourceNotFoundException",
        "ValidationException",
        "AccessDeniedException",
        "ThrottlingException",
        "InternalServiceException",
        "ConflictException",
    ],
)
def test_cancel_job_surfaces_errors(exception_type, aws_session):
    arn = "arn:aws:braket:us-west-2:1234567890:job/job-name"
    exception_response = {
        "Error": {
            "Code": "SomeOtherException",
            "Message": "unit-test-error",
        }
    }

    aws_session.braket_client.cancel_job.side_effect = [
        ClientError(exception_response, "unit-test"),
    ]

    with pytest.raises(ClientError):
        aws_session.cancel_job(arn)
    aws_session.braket_client.cancel_job.assert_called_with(jobArn=arn)
    assert aws_session.braket_client.cancel_job.call_count == 1


@pytest.mark.parametrize(
    "input,output",
    [
        (
            {},
            [
                {
                    "deviceArn": "arn1",
                    "deviceName": "name1",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname1",
                },
                {
                    "deviceArn": "arn2",
                    "deviceName": "name2",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "OFFLINE",
                    "providerName": "pname1",
                },
                {
                    "deviceArn": "arn3",
                    "deviceName": "name3",
                    "deviceType": "QPU",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname2",
                },
            ],
        ),
        (
            {"names": ["name1"]},
            [
                {
                    "deviceArn": "arn1",
                    "deviceName": "name1",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname1",
                },
            ],
        ),
        (
            {"types": ["SIMULATOR"]},
            [
                {
                    "deviceArn": "arn1",
                    "deviceName": "name1",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname1",
                },
                {
                    "deviceArn": "arn2",
                    "deviceName": "name2",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "OFFLINE",
                    "providerName": "pname1",
                },
            ],
        ),
        (
            {"statuses": ["ONLINE"]},
            [
                {
                    "deviceArn": "arn1",
                    "deviceName": "name1",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname1",
                },
                {
                    "deviceArn": "arn3",
                    "deviceName": "name3",
                    "deviceType": "QPU",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname2",
                },
            ],
        ),
        (
            {"provider_names": ["pname2"]},
            [
                {
                    "deviceArn": "arn3",
                    "deviceName": "name3",
                    "deviceType": "QPU",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname2",
                },
            ],
        ),
        (
            {
                "provider_names": ["pname2"],
                "types": ["QPU"],
                "statuses": ["ONLINE"],
                "names": ["name3"],
            },
            [
                {
                    "deviceArn": "arn3",
                    "deviceName": "name3",
                    "deviceType": "QPU",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname2",
                },
            ],
        ),
        (
            {
                "provider_names": ["pname1"],
                "types": ["SIMULATOR"],
                "statuses": ["ONLINE"],
            },
            [
                {
                    "deviceArn": "arn1",
                    "deviceName": "name1",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname1",
                },
            ],
        ),
    ],
)
def test_search_devices(input, output, aws_session):
    return_value = [
        {
            "devices": [
                {
                    "deviceArn": "arn1",
                    "deviceName": "name1",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname1",
                },
                {
                    "deviceArn": "arn2",
                    "deviceName": "name2",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "OFFLINE",
                    "providerName": "pname1",
                },
                {
                    "deviceArn": "arn3",
                    "deviceName": "name3",
                    "deviceType": "QPU",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname2",
                },
            ]
        }
    ]
    mock_paginator = Mock()
    mock_iterator = MagicMock()
    aws_session.braket_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = mock_iterator
    mock_iterator.__iter__.return_value = return_value

    assert aws_session.search_devices(**input) == output


def test_search_devices_arns(aws_session):
    return_value = [
        {
            "devices": [
                {
                    "deviceArn": "arn1",
                    "deviceName": "name1",
                    "deviceType": "SIMULATOR",
                    "deviceStatus": "ONLINE",
                    "providerName": "pname1",
                }
            ]
        }
    ]
    mock_paginator = Mock()
    mock_iterator = MagicMock()
    aws_session.braket_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = mock_iterator
    mock_iterator.__iter__.return_value = return_value

    assert aws_session.search_devices(arns=["arn1"]) == return_value[0]["devices"]
    mock_paginator.paginate.assert_called_with(
        filters=[
            {"name": "deviceArn", "values": ["arn1"]},
        ],
        PaginationConfig={"MaxItems": 100},
    )
