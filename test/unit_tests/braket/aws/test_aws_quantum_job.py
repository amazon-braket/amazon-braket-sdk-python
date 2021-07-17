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

import datetime
from unittest.mock import Mock, patch

import pytest

from braket.aws import AwsQuantumJob


@pytest.fixture
def aws_session(job_region):
    _aws_session = Mock()
    _braket_client_mock = Mock(meta=Mock(region_name=job_region))
    _aws_session.braket_client = _braket_client_mock
    return _aws_session


@pytest.fixture
def generate_get_job_response():
    def _get_job_response(**kwargs):
        response = {
            "ResponseMetadata": {
                "RequestId": "d223b1a0-ee5c-4c75-afa7-3c29d5338b62",
                "HTTPStatusCode": 200,
            },
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
            "createdAt": datetime.datetime(2021, 6, 28, 21, 4, 51),
            "deviceConfig": {
                "priorityAccess": {"devices": ["arn:aws:braket:::device/qpu/rigetti/Aspen-9"]}
            },
            "hyperParameters": {
                "foo": "bar",
            },
            "inputDataConfig": [
                {
                    "channelName": "training_input",
                    "compressionType": "NONE",
                    "dataSource": {
                        "s3DataSource": {
                            "s3DataType": "S3_PREFIX",
                            "s3Uri": "s3://amazon-braket-jobs/job-path/input",
                        }
                    },
                }
            ],
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
            "stoppingCondition": {"maxRuntimeInSeconds": 1200},
        }
        response.update(kwargs)

        return response

    return _get_job_response


@pytest.fixture
def quantum_job_name():
    return "job-test-20210625121626"


@pytest.fixture
def job_region():
    return "us-west-2"


@pytest.fixture
def quantum_job_arn(quantum_job_name, job_region):
    return f"arn:aws:braket:{job_region}:875981177017:job/{quantum_job_name}"


@pytest.fixture
def quantum_job(quantum_job_arn, aws_session):
    return AwsQuantumJob(quantum_job_arn, aws_session)


def test_equality(quantum_job_arn, aws_session, job_region):
    new_aws_session = Mock(braket_client=Mock(meta=Mock(region_name=job_region)))
    quantum_job_1 = AwsQuantumJob(quantum_job_arn, aws_session)
    quantum_job_2 = AwsQuantumJob(quantum_job_arn, aws_session)
    quantum_job_3 = AwsQuantumJob(quantum_job_arn, new_aws_session)
    other_quantum_job = AwsQuantumJob(
        "arn:aws:braket:us-west-2:875981177017:job/other-job", aws_session
    )
    non_quantum_job = quantum_job_1.arn

    assert quantum_job_1 == quantum_job_2
    assert quantum_job_1 == quantum_job_3
    assert quantum_job_1 is not quantum_job_2
    assert quantum_job_1 is not quantum_job_3
    assert quantum_job_1 is quantum_job_1
    assert quantum_job_1 != other_quantum_job
    assert quantum_job_1 != non_quantum_job


def test_hash(quantum_job):
    assert hash(quantum_job) == hash(quantum_job.arn)


@pytest.mark.parametrize(
    "arn, expected_region",
    [
        ("arn:aws:braket:us-west-2:875981177017:job/job-name", "us-west-2"),
        ("arn:aws:braket:us-west-1:1234567890:job/job-name", "us-west-1"),
    ],
)
@patch("braket.aws.aws_quantum_job.boto3.Session")
@patch("braket.aws.aws_quantum_job.AwsSession")
def test_quantum_job_constructor_default_session(
    aws_session_mock, mock_session, arn, expected_region
):
    mock_boto_session = Mock()
    aws_session_mock.return_value = Mock()
    mock_session.return_value = mock_boto_session
    job = AwsQuantumJob(arn)
    mock_session.assert_called_with(region_name=expected_region)
    aws_session_mock.assert_called_with(boto_session=mock_boto_session)
    assert job.arn == arn
    assert job._aws_session == aws_session_mock.return_value


@pytest.mark.xfail(raises=ValueError)
def test_quantum_job_constructor_invalid_region(aws_session):
    arn = "arn:aws:braket:unknown-region:875981177017:job/quantum_job_name"
    AwsQuantumJob(arn, aws_session)


@patch("braket.aws.aws_quantum_job.boto3.Session")
def test_quantum_job_constructor_explicit_session(mock_session, quantum_job_arn, job_region):
    aws_session_mock = Mock(braket_client=Mock(meta=Mock(region_name=job_region)))
    job = AwsQuantumJob(quantum_job_arn, aws_session_mock)
    assert job._aws_session == aws_session_mock
    assert job.arn == quantum_job_arn
    mock_session.assert_not_called()


def test_metadata(quantum_job, aws_session, generate_get_job_response, quantum_job_arn):
    get_job_response_running = generate_get_job_response(status="RUNNING")
    aws_session.get_job.return_value = get_job_response_running
    assert quantum_job.metadata() == get_job_response_running
    aws_session.get_job.assert_called_with(quantum_job_arn)

    get_job_response_completed = generate_get_job_response(status="COMPLETED")
    aws_session.get_job.return_value = get_job_response_completed
    assert quantum_job.metadata() == get_job_response_completed
    aws_session.get_job.assert_called_with(quantum_job_arn)
    assert aws_session.get_job.call_count == 2


def test_metadata_caching(quantum_job, aws_session, generate_get_job_response, quantum_job_arn):
    get_job_response_running = generate_get_job_response(status="RUNNING")
    aws_session.get_job.return_value = get_job_response_running
    assert quantum_job.metadata(True) == get_job_response_running

    get_job_response_completed = generate_get_job_response(status="COMPLETED")
    aws_session.get_job.return_value = get_job_response_completed
    assert quantum_job.metadata(True) == get_job_response_running
    aws_session.get_job.assert_called_with(quantum_job_arn)
    assert aws_session.get_job.call_count == 1


def test_state(quantum_job, aws_session, generate_get_job_response, quantum_job_arn):
    state_1 = "RUNNING"
    get_job_response_running = generate_get_job_response(status=state_1)
    aws_session.get_job.return_value = get_job_response_running
    assert quantum_job.state() == state_1
    aws_session.get_job.assert_called_with(quantum_job_arn)

    state_2 = "COMPLETED"
    get_job_response_completed = generate_get_job_response(status=state_2)
    aws_session.get_job.return_value = get_job_response_completed
    assert quantum_job.state() == state_2
    aws_session.get_job.assert_called_with(quantum_job_arn)
    assert aws_session.get_job.call_count == 2


def test_state_caching(quantum_job, aws_session, generate_get_job_response, quantum_job_arn):
    state_1 = "RUNNING"
    get_job_response_running = generate_get_job_response(status=state_1)
    aws_session.get_job.return_value = get_job_response_running
    assert quantum_job.state(True) == state_1

    state_2 = "COMPLETED"
    get_job_response_completed = generate_get_job_response(status=state_2)
    aws_session.get_job.return_value = get_job_response_completed
    assert quantum_job.state(True) == state_1
    aws_session.get_job.assert_called_with(quantum_job_arn)
    assert aws_session.get_job.call_count == 1
