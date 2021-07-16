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
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from braket.aws.aws_quantum_job import AwsQuantumJob
from braket.aws.aws_session import AwsSession
from braket.jobs.config import (
    CheckpointConfig,
    DataSource,
    InputDataConfig,
    InstanceConfig,
    OutputDataConfig,
    PollingConfig,
    S3DataSource,
    StoppingCondition,
)

S3_TARGET = AwsSession.S3DestinationFolder("foo", "bar")


@pytest.fixture
def aws_session():
    mock = Mock()
    mock.create_job.return_value = "test-job-arn"
    mock.default_bucket.return_value = "default-bucket-name"
    mock.get_execution_role.return_value = "default-role-arn"
    mock.get_job.side_effect = [{"status": "RUNNING"}] * 5 + [{"status": "COMPLETED"}]
    mock.construct_s3_uri.side_effect = lambda bucket, *dirs: f"s3://{bucket}/{'/'.join(dirs)}"
    return mock


@pytest.fixture
def quantum_job(aws_session, arn):
    return AwsQuantumJob(arn, aws_session)


@pytest.fixture
def arn(image_uri):
    return f"arn:aws:braket:us-west-2:0000000000:job/{image_uri}-00000000000000"


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
    if request.param == "given_job_name-nah":
        return "test-job-name"


@pytest.fixture
def s3_prefix(job_name):
    return f"{job_name}/non-default"


@pytest.fixture(params=["local_source", "s3_source"])
def source_dir(request, bucket, s3_prefix):
    if request.param == "local_source":
        return "test-source-dir"
    elif request.param == "s3_source":
        return AwsSession.construct_s3_uri(bucket, "test-source-prefix", "source")


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
        maximumTaskLimit=10,
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
    return None


@pytest.fixture
def tags():
    return {"tagKey": "tagValue"}


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
                # "copy_checkpoints_from_job": None,
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


def test_equality(arn, aws_session):
    quantum_job_1 = AwsQuantumJob(arn, aws_session)
    quantum_job_2 = AwsQuantumJob(arn, aws_session)
    other_quantum_job = AwsQuantumJob("different:arn", aws_session)
    non_quantum_job = quantum_job_1.id

    assert quantum_job_1 == quantum_job_2
    assert quantum_job_1 is not quantum_job_2
    assert quantum_job_1 != other_quantum_job
    assert quantum_job_1 != non_quantum_job


def test_str(quantum_job):
    expected = f"AwsQuantumJob('id/jobArn':'{quantum_job.id}')"
    assert str(quantum_job) == expected


def test_hash(quantum_job):
    assert hash(quantum_job) == hash(quantum_job.id)


def test_id_getter(arn, aws_session):
    quantum_job = AwsQuantumJob(arn, aws_session)
    assert quantum_job.id == arn
    assert quantum_job.arn == arn


@pytest.mark.xfail(raises=AttributeError)
def test_no_id_setter(quantum_job):
    quantum_job.id = 123


@patch.object(AwsQuantumJob, "_generate_default_job_name", return_value="default_job_name-000000")
def test_create_job(
    mock_generate_default_job_name,
    aws_session,
    create_job_args,
):
    job = AwsQuantumJob.create(**create_job_args)
    assert job == AwsQuantumJob("test-job-arn", aws_session)

    _assert_create_job_called_with(create_job_args)


@patch.object(AwsQuantumJob, "_generate_default_job_name", return_value="default_job_name-000000")
def _assert_create_job_called_with(
    create_job_args,
    mock_default_job_name,
):
    aws_session = create_job_args["aws_session"]
    source_dir_name = create_job_args["source_dir"].split("/")[-1]
    create_job_args = defaultdict(lambda: None, **create_job_args)
    image_uri = create_job_args["image_uri"] or "Base-Image-URI"
    job_name = create_job_args["job_name"] or AwsQuantumJob._generate_default_job_name(image_uri)
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
    # vpc_config = create_job_args["vpc_config"]
    # tags = create_job_args["tags"] or {}

    test_kwargs = {
        "jobName": job_name,
        "roleArn": role_arn,
        "algorithmSpecification": {
            "scriptModeConfig": {
                "entryPoint": create_job_args["entry_point"],
                "s3Uri": f"{code_location}/{source_dir_name}.tar.gz",
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
        # "vpcConfig": vpc_config,
        # "tags": tags,
    }
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
    assert (
        AwsQuantumJob._generate_default_job_name(image_uri)
        == f"{image_uri}-{datetime.now(timezone.utc).timestamp() * 1000:.0f}"
    )


def test_state(arn, aws_session):
    job = AwsQuantumJob(
        arn,
        aws_session,
    )
    for _ in range(5):
        assert job.state == "RUNNING"
    assert job.state == "COMPLETED"
