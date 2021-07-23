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
from collections import defaultdict
from dataclasses import asdict
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from freezegun import freeze_time

from braket.aws import AwsQuantumJob, AwsSession
from braket.jobs.config import (
    CheckpointConfig,
    DataSource,
    InputDataConfig,
    InstanceConfig,
    OutputDataConfig,
    PollingConfig,
    S3DataSource,
    StoppingCondition,
    VpcConfig,
)


@pytest.fixture
def aws_session(quantum_job_arn, job_region):
    _aws_session = Mock()
    _aws_session.create_job.return_value = quantum_job_arn
    _aws_session.default_bucket.return_value = "default-bucket-name"
    _aws_session.get_execution_role.return_value = "default-role-arn"
    _aws_session.construct_s3_uri.side_effect = (
        lambda bucket, *dirs: f"s3://{bucket}/{'/'.join(dirs)}"
    )

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
def generate_cancel_job_response():
    def _cancel_job_response(**kwargs):
        response = {
            "ResponseMetadata": {
                "RequestId": "857b0893-2073-4ad6-b828-744af8400dfe",
                "HTTPStatusCode": 200,
            },
            "cancellationStatus": "CANCELLING",
            "jobArn": "arn:aws:braket:us-west-2:875981177017:job/job-test-20210628140446",
        }
        response.update(kwargs)
        return response

    return _cancel_job_response


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


@pytest.fixture
def entry_point():
    return "entry_point:func"


@pytest.fixture
def bucket():
    return "braket-region-id"


@pytest.fixture
def image_uri():
    return "Test-Image-URI"


@pytest.fixture(params=["given_job_name", "default_job_name"])
def job_name(request):
    if request.param == "given_job_nameh":
        return "test-job-name"


@pytest.fixture
def s3_prefix(job_name):
    return f"{job_name}/non-default"


@pytest.fixture(params=["local_source", "s3_source", "working_directory"])
def source_dir(request, bucket, s3_prefix):
    if request.param == "working_directory":
        return "."
    if request.param == "local_source":
        return "test-source-dir"
    elif request.param == "s3_source":
        return AwsSession.construct_s3_uri(bucket, "test-source-prefix", "source.tar.gz")


@pytest.fixture
def code_location(bucket, s3_prefix):
    return AwsSession.construct_s3_uri(bucket, s3_prefix, "script")


@pytest.fixture
def role_arn():
    return "arn:aws:iam::0000000000:role/AmazonBraketInternalSLR"


@pytest.fixture
def priority_access_device_arn():
    return "arn:aws:braket:::device/qpu/test/device-name"


@pytest.fixture
def hyper_parameters():
    return {
        "param": "value",
        "other-param": 100,
    }


@pytest.fixture
def input_data_config(bucket, s3_prefix):
    return [
        InputDataConfig(
            channelName="testinput",
            dataSource=DataSource(
                s3DataSource=S3DataSource(
                    s3Uri=AwsSession.construct_s3_uri(bucket, s3_prefix, "input"),
                ),
            ),
        ),
    ]


@pytest.fixture
def instance_config():
    return InstanceConfig(
        instanceType="ml.m5.large",
        instanceCount=1,
        volumeSizeInGb=1,
    )


@pytest.fixture
def stopping_condition():
    return StoppingCondition(
        maxRuntimeInSeconds=1200,
    )


@pytest.fixture
def output_data_config(bucket, s3_prefix):
    return OutputDataConfig(
        s3Path=AwsSession.construct_s3_uri(bucket, s3_prefix, "output"),
    )


@pytest.fixture
def checkpoint_config(bucket, s3_prefix):
    return CheckpointConfig(
        localPath="/opt/omega/checkpoints",
        s3Uri=AwsSession.construct_s3_uri(bucket, s3_prefix, "checkpoints"),
    )


@pytest.fixture(params=["wait", "dont_wait"])
def wait_until_complete(request):
    return request.param == "wait"


@pytest.fixture(params=["job_completes", "job_times_out"])
def polling_config(request):
    timeout = 1 if request.param == "job_completes" else 0.1
    return PollingConfig(timeout, 0.05)


@pytest.fixture
def vpc_config():
    return VpcConfig(
        securityGroupIds=["1", "2"],
        subnets=["3", "4"],
    )


@pytest.fixture
def tags():
    return {"tagKey": "tagValue"}


@pytest.fixture
def job_time():
    return "1997-08-13 12:12:12"


@pytest.fixture(params=["fixtures", "defaults", "nones"])
def create_job_args(
    request,
    aws_session,
    entry_point,
    image_uri,
    source_dir,
    job_name,
    code_location,
    role_arn,
    wait_until_complete,
    polling_config,
    priority_access_device_arn,
    hyper_parameters,
    input_data_config,
    instance_config,
    stopping_condition,
    output_data_config,
    checkpoint_config,
    vpc_config,
    tags,
):
    if request.param == "fixtures":
        return dict(
            (key, value)
            for key, value in {
                "aws_session": aws_session,
                "entry_point": entry_point,
                "source_dir": source_dir,
                "image_uri": image_uri,
                "job_name": job_name,
                "code_location": code_location,
                "role_arn": role_arn,
                "wait_until_complete": wait_until_complete,
                "polling_config": polling_config,
                "priority_access_device_arn": priority_access_device_arn,
                "hyper_parameters": hyper_parameters,
                # "metric_defintions": None,
                "input_data_config": input_data_config,
                "instance_config": instance_config,
                "stopping_condition": stopping_condition,
                "output_data_config": output_data_config,
                "checkpoint_config": checkpoint_config,
                "vpc_config": vpc_config,
                "tags": tags,
            }.items()
            if value is not None
        )
    elif request.param == "defaults":
        return {
            "aws_session": aws_session,
            "entry_point": entry_point,
            "source_dir": source_dir,
        }
    elif request.param == "nones":
        return defaultdict(
            lambda: None,
            aws_session=aws_session,
            entry_point=entry_point,
            source_dir=source_dir,
        )


def test_str(quantum_job):
    expected = f"AwsQuantumJob('arn':'{quantum_job.arn}')"
    assert str(quantum_job) == expected


def test_arn(quantum_job_arn, aws_session):
    quantum_job = AwsQuantumJob(quantum_job_arn, aws_session)
    assert quantum_job.arn == quantum_job_arn


@pytest.mark.xfail(raises=AttributeError)
def test_no_arn_setter(quantum_job):
    quantum_job.arn = 123


def test_create_job(
    # mock_generate_default_job_name,
    aws_session,
    create_job_args,
    quantum_job_arn,
    generate_get_job_response,
    job_time,
):
    aws_session.get_job.side_effect = [generate_get_job_response(status="RUNNING")] * 5 + [
        generate_get_job_response(status="COMPLETED")
    ]
    with freeze_time(job_time):
        job = AwsQuantumJob.create(**create_job_args)
    assert job == AwsQuantumJob(quantum_job_arn, aws_session)

    _assert_create_job_called_with(create_job_args, job_time)


def _assert_create_job_called_with(
    create_job_args,
    job_time,
):
    aws_session = create_job_args["aws_session"]
    source_dir_name = create_job_args["source_dir"].split("/")[-1]
    tarred_source_dir_name = (
        f"{source_dir_name.split('/')[-1]}"
        f"{'.tar.gz' if not source_dir_name.endswith('.tar.gz') else ''}"
    )
    if source_dir_name in [".", ".."]:
        tarred_source_dir_name = "source.tar.gz"
    create_job_args = defaultdict(lambda: None, **create_job_args)
    image_uri = create_job_args["image_uri"] or "Base-Image-URI"
    with freeze_time(job_time):
        job_name = create_job_args["job_name"] or AwsQuantumJob._generate_default_job_name(
            image_uri
        )
    default_bucket = aws_session.default_bucket()
    code_location = create_job_args["code_location"] or aws_session.construct_s3_uri(
        default_bucket, job_name, "script"
    )
    role_arn = create_job_args["role_arn"] or aws_session.get_execution_role()
    priority_access_devices = [
        arn for arn in [create_job_args["priority_access_device_arn"]] if arn
    ]
    hyper_parameters = create_job_args["hyper_parameters"] or {}
    input_data_config = create_job_args["input_data_config"] or []
    instance_config = create_job_args["instance_config"] or InstanceConfig()
    output_data_config = create_job_args["output_data_config"] or OutputDataConfig(
        s3Path=aws_session.construct_s3_uri(default_bucket, job_name, "output")
    )
    stopping_condition = create_job_args["stopping_condition"] or StoppingCondition()
    checkpoint_config = create_job_args["checkpoint_config"] or CheckpointConfig(
        s3Uri=aws_session.construct_s3_uri(default_bucket, job_name, "checkpoints")
    )
    vpc_config = create_job_args["vpc_config"]
    # tags = create_job_args["tags"] or {}

    test_kwargs = {
        "jobName": job_name,
        "roleArn": role_arn,
        "algorithmSpecification": {
            "scriptModeConfig": {
                "entryPoint": create_job_args["entry_point"],
                "s3Uri": f"{code_location}/{tarred_source_dir_name}",
                "compressionType": "GZIP",
            }
        },
        "inputDataConfig": [asdict(input_channel) for input_channel in input_data_config],
        "instanceConfig": asdict(instance_config),
        "outputDataConfig": asdict(output_data_config),
        "checkpointConfig": asdict(checkpoint_config),
        "deviceConfig": {"priorityAccess": {"devices": priority_access_devices}},
        "hyperParameters": hyper_parameters,
        "stoppingCondition": asdict(stopping_condition),
        # "tags": tags,
    }

    if vpc_config:
        test_kwargs["vpcConfig"] = vpc_config

    aws_session.create_job.assert_called_with(**test_kwargs)


def setup_function(test_create_job):
    """setup any state tied to the execution of the given function.
    Invoked for every test function in the module.
    """
    import os

    try:
        os.mkdir("test-source-dir")
    except FileExistsError:
        pass


def teardown_function(test_create_job):
    """teardown any state that was previously setup with a setup_function
    call.
    """
    import os

    os.rmdir("test-source-dir")


def test_generate_default_job_name(image_uri):
    with freeze_time("1997-08-13 12:12:12"):
        assert (
            AwsQuantumJob._generate_default_job_name(image_uri)
            == f"{image_uri}-{datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000:.0f}"
        )


def test_copy_checkpoints_from_job(
    aws_session,
    entry_point,
    source_dir,
    checkpoint_config,
    job_name,
    quantum_job_arn,
    generate_get_job_response,
):
    other_job_arn = f"{quantum_job_arn}-other"
    checkpoint_s3_uri = "s3://other-bucket/checkpoint/path"
    aws_session.get_job.return_value = generate_get_job_response(
        checkpointConfig={"s3Uri": checkpoint_s3_uri}
    )
    job = AwsQuantumJob.create(
        aws_session=aws_session,
        entry_point=entry_point,
        source_dir=source_dir,
        job_name=job_name,
        checkpoint_config=checkpoint_config,
        copy_checkpoints_from_job=other_job_arn,
    )
    assert job == AwsQuantumJob(quantum_job_arn, aws_session)
    checkpoint_config = checkpoint_config or CheckpointConfig(
        s3Uri=aws_session.construct_s3_uri(aws_session.default_bucket(), job_name, "checkpoints")
    )
    aws_session.copy_s3.assert_any_call(checkpoint_s3_uri, checkpoint_config.s3Uri)


def test_cancel_job(quantum_job_arn, aws_session, generate_cancel_job_response):
    cancellation_status = "CANCELLING"
    aws_session.cancel_job.return_value = generate_cancel_job_response(
        cancellationStatus=cancellation_status
    )
    quantum_job = AwsQuantumJob(quantum_job_arn, aws_session)
    status = quantum_job.cancel()
    aws_session.cancel_job.assert_called_with(quantum_job_arn)
    assert status == cancellation_status


@pytest.mark.xfail(raises=ClientError)
def test_cancel_job_surfaces_exception(quantum_job, aws_session):
    exception_response = {
        "Error": {
            "Code": "ValidationException",
            "Message": "unit-test-error",
        }
    }
    aws_session.cancel_job.side_effect = ClientError(exception_response, "cancel_job")
    quantum_job.cancel()


def test_create_job_source_dir_not_found(
    aws_session,
    entry_point,
):
    fake_source_dir = "fake-source-dir"
    with pytest.raises(ValueError) as e:
        AwsQuantumJob.create(
            aws_session=aws_session,
            entry_point=entry_point,
            source_dir=fake_source_dir,
        )

    assert str(e.value) == f"Source directory not found: {fake_source_dir}"
