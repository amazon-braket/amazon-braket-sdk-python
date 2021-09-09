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
import json
import os
import tarfile
import tempfile
import time
from collections import defaultdict
from dataclasses import asdict
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from braket.aws import AwsQuantumJob, AwsSession
from braket.jobs.config import (
    CheckpointConfig,
    DataSource,
    InputDataConfig,
    InstanceConfig,
    OutputDataConfig,
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
                "devices": ["arn:aws:braket:::device/qpu/rigetti/Aspen-9"],
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
    return "job-test-20210628140446"


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


@pytest.fixture()
def result_setup(quantum_job_name):
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        file_path = "results.json"

        with open(file_path, "w") as write_file:
            write_file.write(
                json.dumps(
                    {
                        "braketSchemaHeader": {
                            "name": "braket.jobs_data.persisted_job_data",
                            "version": "1",
                        },
                        "dataDictionary": {"converged": True, "energy": -0.2},
                        "dataFormat": "plaintext",
                    }
                )
            )

        with tarfile.open("model.tar.gz", "w:gz") as tar:
            tar.add(file_path, arcname=os.path.basename(file_path))

        yield

        result_dir = f"{os.getcwd()}/{quantum_job_name}"

        if os.path.exists(result_dir):
            os.remove(f"{result_dir}/results.json")
            os.rmdir(f"{result_dir}/")

        if os.path.isfile("model.tar.gz"):
            os.remove("model.tar.gz")

        os.chdir("..")


def test_results_when_job_is_completed(
    quantum_job, aws_session, generate_get_job_response, result_setup
):
    expected_saved_data = {"converged": True, "energy": -0.2}
    state = "COMPLETED"

    get_job_response_completed = generate_get_job_response(status=state)
    quantum_job._aws_session.get_job.return_value = get_job_response_completed
    actual_data = quantum_job.result()

    job_metadata = quantum_job.metadata(True)
    s3_path, job_name = job_metadata["outputDataConfig"]["s3Path"], job_metadata["jobName"]

    output_bucket_uri = (
        f"{s3_path}/BraketJob-{aws_session.account_id}-{job_name}/output/model.tar.gz"
    )
    quantum_job._aws_session.download_from_s3.assert_called_with(
        s3_uri=output_bucket_uri, filename="model.tar.gz"
    )
    assert actual_data == expected_saved_data


@pytest.mark.parametrize(
    "failure_reason",
    ["Validation Error", None],
)
@pytest.mark.parametrize("state", ["FAILED", "CANCELLED"])
def test_results_when_job_is_failed_or_cancelled(
    state,
    quantum_job,
    generate_get_job_response,
    result_setup,
    failure_reason,
):
    get_job_response_failed = generate_get_job_response(status=state, failureReason=failure_reason)
    quantum_job._aws_session.get_job.return_value = get_job_response_failed
    job_metadata = quantum_job.metadata(True)
    message = (
        f"Error retrieving results, your job is in {state} state. "
        "Your job has failed due to: "
        f"{job_metadata.get('failureReason', 'unknown reason')}"
        if state == "FAILED"
        else f"Error retrieving results, your job is in {state} state."
    )
    with pytest.raises(RuntimeError, match=message):
        quantum_job.result()


def test_download_result_when_job_is_running(
    quantum_job, aws_session, generate_get_job_response, result_setup
):
    poll_timeout_seconds, poll_interval_seconds, state = 1, 0.5, "RUNNING"
    get_job_response_completed = generate_get_job_response(status=state)
    aws_session.get_job.return_value = get_job_response_completed
    job_metadata = quantum_job.metadata(True)

    with pytest.raises(
        TimeoutError,
        match=f"{job_metadata['jobName']}: Polling for job completion "
        f"timed out after {poll_timeout_seconds} seconds.",
    ):
        quantum_job.download_result(
            poll_timeout_seconds=poll_timeout_seconds, poll_interval_seconds=poll_interval_seconds
        )


def test_download_result_when_extract_path_not_provided(
    quantum_job, generate_get_job_response, aws_session, result_setup
):
    state = "COMPLETED"
    expected_saved_data = {"converged": True, "energy": -0.2}
    get_job_response_completed = generate_get_job_response(status=state)
    quantum_job._aws_session.get_job.return_value = get_job_response_completed
    job_metadata = quantum_job.metadata(True)
    job_name = job_metadata["jobName"]
    quantum_job.download_result()

    with open(f"{job_name}/results.json", "r") as file:
        actual_data = json.loads(file.read())["dataDictionary"]
        assert expected_saved_data == actual_data


def test_download_result_when_extract_path_provided(
    quantum_job, generate_get_job_response, aws_session, result_setup
):
    expected_saved_data = {"converged": True, "energy": -0.2}
    state = "COMPLETED"
    get_job_response_completed = generate_get_job_response(status=state)
    aws_session.get_job.return_value = get_job_response_completed
    job_metadata = quantum_job.metadata(True)
    job_name = job_metadata["jobName"]

    with tempfile.TemporaryDirectory() as temp_dir:
        quantum_job.download_result(temp_dir)

        with open(f"{temp_dir}/{job_name}/results.json", "r") as file:
            actual_data = json.loads(file.read())["dataDictionary"]
            assert expected_saved_data == actual_data


@pytest.fixture
def entry_point():
    return "test-source-dir.entry_point:func"


@pytest.fixture
def bucket():
    return "braket-region-id"


@pytest.fixture(params=[None, "my_custom_uri"])
def image_uri(request):
    return request.param


@pytest.fixture(params=["given_job_name", "default_job_name"])
def job_name(request):
    if request.param == "given_job_name":
        return "test-job-name"


@pytest.fixture
def s3_prefix(job_name):
    return f"{job_name}/non-default"


@pytest.fixture(params=["local_source", "s3_source"])
def source_dir(request, bucket, s3_prefix):
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
def device_arn():
    return "arn:aws:braket:::device/qpu/test/device-name"


@pytest.fixture
def hyperparameters():
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


@pytest.fixture
def vpc_config():
    return VpcConfig(
        securityGroupIds=["1", "2"],
        subnets=["3", "4"],
    )


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
    device_arn,
    hyperparameters,
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
                "entry_point": entry_point,
                "source_dir": source_dir,
                "image_uri": image_uri,
                "job_name": job_name,
                "code_location": code_location,
                "role_arn": role_arn,
                "wait_until_complete": wait_until_complete,
                "device_arn": device_arn,
                "hyperparameters": hyperparameters,
                # "metric_defintions": None,
                "input_data_config": input_data_config,
                "instance_config": instance_config,
                "stopping_condition": stopping_condition,
                "output_data_config": output_data_config,
                "checkpoint_config": checkpoint_config,
                "vpc_config": vpc_config,
                "tags": tags,
                "aws_session": aws_session,
            }.items()
            if value is not None
        )
    elif request.param == "defaults":
        return {
            "entry_point": entry_point,
            "device_arn": device_arn,
            "source_dir": source_dir,
            "aws_session": aws_session,
        }
    elif request.param == "nones":
        return defaultdict(
            lambda: None,
            entry_point=entry_point,
            device_arn=device_arn,
            source_dir=source_dir,
            aws_session=aws_session,
        )


def test_str(quantum_job):
    expected = f"AwsQuantumJob('arn':'{quantum_job.arn}')"
    assert str(quantum_job) == expected


def test_arn(quantum_job_arn, aws_session):
    quantum_job = AwsQuantumJob(quantum_job_arn, aws_session)
    assert quantum_job.arn == quantum_job_arn


def test_name(quantum_job_arn, quantum_job_name, aws_session):
    quantum_job = AwsQuantumJob(quantum_job_arn, aws_session)
    assert quantum_job.name == quantum_job_name


@pytest.mark.xfail(raises=AttributeError)
def test_no_arn_setter(quantum_job):
    quantum_job.arn = 123


@patch("braket.aws.aws_quantum_job.AwsQuantumJob.logs")
@patch("braket.aws.aws_quantum_job.AwsQuantumJob._validate_entry_point")
@patch("time.time")
def test_create_job(
    mock_time,
    mock_validate_entry_point,
    mock_logs,
    aws_session,
    source_dir,
    create_job_args,
    quantum_job_arn,
    generate_get_job_response,
):
    mock_time.return_value = datetime.datetime.now().timestamp()
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        os.mkdir("test-source-dir")
        if source_dir == ".":
            os.chdir("test-source-dir")
        aws_session.get_job.side_effect = [generate_get_job_response(status="RUNNING")] * 5 + [
            generate_get_job_response(status="COMPLETED")
        ]
        job = AwsQuantumJob.create(**create_job_args)
        assert job == AwsQuantumJob(quantum_job_arn, aws_session)
        _assert_create_job_called_with(create_job_args)
        os.chdir("../..")


def _assert_create_job_called_with(
    create_job_args,
):
    aws_session = create_job_args["aws_session"]
    create_job_args = defaultdict(lambda: None, **create_job_args)
    image_uri = create_job_args["image_uri"]
    job_name = create_job_args["job_name"] or AwsQuantumJob._generate_default_job_name(
        image_uri or AwsQuantumJob.DEFAULT_IMAGE_NAME
    )
    default_bucket = aws_session.default_bucket()
    code_location = create_job_args["code_location"] or aws_session.construct_s3_uri(
        default_bucket, "jobs", job_name, "script"
    )
    role_arn = create_job_args["role_arn"] or aws_session.get_execution_role()
    devices = [create_job_args["device_arn"]]
    hyperparameters = create_job_args["hyperparameters"] or {}
    input_data_config = create_job_args["input_data_config"] or []
    instance_config = create_job_args["instance_config"] or InstanceConfig()
    output_data_config = create_job_args["output_data_config"] or OutputDataConfig(
        s3Path=aws_session.construct_s3_uri(default_bucket, "jobs", job_name, "output")
    )
    stopping_condition = create_job_args["stopping_condition"] or StoppingCondition()
    checkpoint_config = create_job_args["checkpoint_config"] or CheckpointConfig(
        s3Uri=aws_session.construct_s3_uri(default_bucket, "jobs", job_name, "checkpoints")
    )
    vpc_config = create_job_args["vpc_config"]
    algorithm_specification = {
        "scriptModeConfig": {
            "entryPoint": create_job_args["entry_point"],
            "s3Uri": f"{code_location}/source.tar.gz",
            "compressionType": "GZIP",
        }
    }
    if image_uri:
        algorithm_specification["containerImage"] = {"uri": image_uri}
    # tags = create_job_args["tags"] or {}

    test_kwargs = {
        "jobName": job_name,
        "roleArn": role_arn,
        "algorithmSpecification": algorithm_specification,
        "inputDataConfig": [asdict(input_channel) for input_channel in input_data_config],
        "instanceConfig": asdict(instance_config),
        "outputDataConfig": asdict(output_data_config),
        "checkpointConfig": asdict(checkpoint_config),
        "deviceConfig": {"devices": devices},
        "hyperParameters": hyperparameters,
        "stoppingCondition": asdict(stopping_condition),
        # "tags": tags,
    }

    if vpc_config:
        test_kwargs["vpcConfig"] = vpc_config

    aws_session.create_job.assert_called_with(**test_kwargs)


@patch("time.time")
def test_generate_default_job_name(mock_time, image_uri):
    mock_time.return_value = datetime.datetime.now().timestamp()
    assert (
        AwsQuantumJob._generate_default_job_name(image_uri)
        == f"{image_uri}-{time.time() * 1000:.0f}"
    )


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


@patch("braket.aws.aws_quantum_job.AwsQuantumJob._validate_entry_point")
def test_create_job_source_dir_not_found(
    mock_validate_entry_point,
    aws_session,
    entry_point,
    device_arn,
):
    fake_source_dir = "fake-source-dir"
    with pytest.raises(ValueError) as e:
        AwsQuantumJob.create(
            entry_point="fake-source-dir.test_script:func",
            device_arn=device_arn,
            source_dir=fake_source_dir,
            aws_session=aws_session,
        )
    assert str(e.value) == f"Source directory not found: {fake_source_dir}"


@patch("braket.aws.aws_quantum_job.AwsQuantumJob._validate_entry_point")
def test_create_job_source_dir_s3_but_not_tar(
    mock_validate_entry_point,
    aws_session,
    entry_point,
    device_arn,
):
    fake_source_dir = "s3://bucket/non-tar-file"
    with pytest.raises(ValueError) as e:
        AwsQuantumJob.create(
            entry_point=entry_point,
            device_arn=device_arn,
            source_dir=fake_source_dir,
            aws_session=aws_session,
        )

    assert str(e.value) == (
        "If source_dir is an S3 URI, it must point to a tar.gz file. "
        f"Not a valid S3 URI for parameter `source_dir`: {fake_source_dir}"
    )


def test_source_dir_not_in_entry_point_name(entry_point, aws_session, device_arn):
    source_dir = "other-source-dir"

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        os.mkdir("other-source-dir")
        with pytest.raises(ValueError) as e:
            AwsQuantumJob.create(
                entry_point=entry_point,
                device_arn=device_arn,
                source_dir=source_dir,
                aws_session=aws_session,
            )
        os.chdir("..")

    assert (
        str(e.value)
        == f"`Entrypoint`: {entry_point} should be within the `source_dir`: {source_dir}"
    )


@patch("importlib.import_module")
def test_entry_point_when_source_dir_not_provided(
    mock_import, quantum_job, code_location, aws_session, entry_point
):
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        module, _, func = entry_point.partition(":")
        dir_data = module.split(".")
        folder_path, file_name = "/".join(dir_data[:-1]), f"{dir_data[-1]}.py"

        os.mkdir(folder_path)

        with open(f"{folder_path}/__init__.py", "w") as f:
            pass

        with open(f"{folder_path}/{file_name}", "w") as f:
            f.write("def func(): \n\tpass")

        quantum_job._process_source_dir(
            aws_session=aws_session,
            entry_point=entry_point,
            code_location=code_location,
            source_dir=None,
        )

        args_list = aws_session.upload_to_s3.call_args_list
        assert "source.tar.gz" in args_list[0][0][0] and code_location in args_list[0][0][1]
        aws_session.upload_to_s3.assert_called_once()
        os.chdir("..")


@patch("braket.aws.aws_quantum_job.AwsQuantumJob._tar_and_upload_to_code_location")
@patch("importlib.import_module")
def test_entry_point_when_source_dir_not_provided_current_directory(
    mock_import, mock_tar, quantum_job, code_location, aws_session
):
    entry_point = "my_file:start_here"
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        with open("__init__.py", "w") as f:
            pass

        with open("my_file.py", "w") as f:
            f.write("def func(): \n\tpass")

        quantum_job._process_source_dir(
            aws_session=aws_session,
            entry_point=entry_point,
            code_location=code_location,
            source_dir=None,
        )

        mock_tar.assert_called_with(
            aws_session,
            "my_file.py",
            code_location,
        )
        os.chdir("..")


@patch("braket.aws.aws_quantum_job.AwsQuantumJob._validate_entry_point")
def test_copy_checkpoints(
    mock_validate_entry_point,
    aws_session,
    quantum_job_arn,
    entry_point,
    device_arn,
    checkpoint_config,
    generate_get_job_response,
):
    other_checkpoint_uri = "s3://amazon-braket-jobs/job-path/checkpoints"
    aws_session.get_job.return_value = generate_get_job_response(
        checkpointConfig={
            "s3Uri": other_checkpoint_uri,
        }
    )
    AwsQuantumJob._process_source_dir = Mock()
    aws_session.create_job.return_value = quantum_job_arn
    job = AwsQuantumJob.create(
        entry_point=entry_point,
        device_arn=device_arn,
        source_dir="source_dir",
        copy_checkpoints_from_job="other-job-arn",
        checkpoint_config=checkpoint_config,
        aws_session=aws_session,
    )
    assert job == AwsQuantumJob(quantum_job_arn, aws_session)
    aws_session.copy_s3_directory.assert_called_with(other_checkpoint_uri, checkpoint_config.s3Uri)


@patch("braket.aws.aws_quantum_job.AwsQuantumJob._validate_entry_point")
@patch(
    "braket.jobs.metrics_data.cwl_insights_metrics_fetcher."
    "CwlInsightsMetricsFetcher.get_metrics_for_job"
)
def test_metrics(
    metrics_fetcher_mock,
    mock_validate_entry_point,
    aws_session,
    quantum_job_arn,
    entry_point,
    device_arn,
    checkpoint_config,
    generate_get_job_response,
):
    expected_metrics = {"Test": [1]}
    aws_session.get_job.return_value = generate_get_job_response()
    metrics_fetcher_mock.return_value = expected_metrics
    AwsQuantumJob._process_source_dir = Mock()
    aws_session.create_job.return_value = quantum_job_arn
    job = AwsQuantumJob.create(
        entry_point=entry_point,
        device_arn=device_arn,
        source_dir="source_dir",
        aws_session=aws_session,
    )
    metrics = job.metrics()
    assert job == AwsQuantumJob(quantum_job_arn, aws_session)
    assert metrics == expected_metrics


@pytest.mark.parametrize(
    "entry_point",
    (
        "test-source-dir.entry_point:func",
        "test-source-dir.entry_point",
    ),
)
@patch("importlib.import_module")
def test_validate_entry_point(mock_import, entry_point):
    mock_module = Mock(function_name="exists")
    mock_import.return_value = mock_module
    AwsQuantumJob._validate_entry_point(entry_point)


@patch("importlib.import_module")
def test_validate_entry_point_invalid_entry_point(mock_import):
    entry_point = "source_dir.entry_point:start_here_not_found"
    error_string = (
        "Entry function 'start_here_not_found' not found in module " "'source_dir.entry_point'."
    )
    file_path, function_name = entry_point.split(":")
    mock_module = Mock(start_here="exists")
    del mock_module.start_here_not_found
    mock_module.__repr__ = lambda _: file_path
    mock_import.return_value = mock_module

    with pytest.raises(ValueError, match=error_string):
        AwsQuantumJob._validate_entry_point(entry_point)


@patch("importlib.import_module")
def test_validate_entry_point_invalid_source_dir(mock_import):
    entry_point = "fake_source_dir.entry_point:start_here_not_found"
    error_string = "Entry point module not found: 'fake_source_dir.entry_point'"
    mock_import.side_effect = ModuleNotFoundError()
    with pytest.raises(ValueError, match=error_string):
        AwsQuantumJob._validate_entry_point(entry_point)


@pytest.fixture
def log_stream_responses():
    return (
        ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "This shouldn't get raised...",
                }
            },
            "DescribeLogStreams",
        ),
        {"logStreams": []},
        {"logStreams": [{"logStreamName": "stream-1"}]},
    )


@pytest.fixture
def log_events_responses():
    return (
        {"nextForwardToken": None, "events": [{"timestamp": 1, "message": "hi there #1"}]},
        {"nextForwardToken": None, "events": []},
        {
            "nextForwardToken": None,
            "events": [
                {"timestamp": 1, "message": "hi there #1"},
                {"timestamp": 2, "message": "hi there #2"},
            ],
        },
        {"nextForwardToken": None, "events": []},
        {
            "nextForwardToken": None,
            "events": [
                {"timestamp": 2, "message": "hi there #2"},
                {"timestamp": 2, "message": "hi there #2a"},
                {"timestamp": 3, "message": "hi there #3"},
            ],
        },
        {"nextForwardToken": None, "events": []},
    )


def test_logs(
    quantum_job,
    generate_get_job_response,
    log_events_responses,
    log_stream_responses,
    capsys,
):
    quantum_job._aws_session.get_job.side_effect = (
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="COMPLETED"),
    )
    quantum_job._aws_session.describe_log_streams.side_effect = log_stream_responses
    quantum_job._aws_session.get_log_events.side_effect = log_events_responses

    quantum_job.logs(wait=True, poll=0)

    captured = capsys.readouterr()
    assert captured.out == "\n".join(
        (
            "..",
            "hi there #1",
            "hi there #2",
            "hi there #2a",
            "hi there #3",
            "",
        )
    )


@patch.dict("os.environ", {"JPY_PARENT_PID": "True"})
def test_logs_multiple_instances(
    quantum_job,
    generate_get_job_response,
    log_events_responses,
    log_stream_responses,
    capsys,
):
    quantum_job._aws_session.get_job.side_effect = (
        generate_get_job_response(status="RUNNING", instanceConfig={"instanceCount": 2}),
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="COMPLETED"),
    )
    log_stream_responses[-1]["logStreams"].append({"logStreamName": "stream-2"})
    quantum_job._aws_session.describe_log_streams.side_effect = log_stream_responses

    event_counts = {
        "stream-1": 0,
        "stream-2": 0,
    }

    def get_log_events(log_group, log_stream, start_time, start_from_head, next_token):
        log_events_dict = {
            "stream-1": log_events_responses,
            "stream-2": log_events_responses,
        }
        log_events_dict["stream-1"] += (
            {
                "nextForwardToken": None,
                "events": [],
            },
            {
                "nextForwardToken": None,
                "events": [],
            },
        )
        log_events_dict["stream-2"] += (
            {
                "nextForwardToken": None,
                "events": [
                    {"timestamp": 3, "message": "hi there #3"},
                    {"timestamp": 4, "message": "hi there #4"},
                ],
            },
            {
                "nextForwardToken": None,
                "events": [],
            },
        )
        event_counts[log_stream] += 1
        return log_events_dict[log_stream][event_counts[log_stream]]

    quantum_job._aws_session.get_log_events.side_effect = get_log_events

    quantum_job.logs(wait=True, poll=0)

    captured = capsys.readouterr()
    assert captured.out == "\n".join(
        (
            "..",
            "\x1b[34mhi there #1\x1b[0m",
            "\x1b[35mhi there #1\x1b[0m",
            "\x1b[34mhi there #2\x1b[0m",
            "\x1b[35mhi there #2\x1b[0m",
            "\x1b[34mhi there #2a\x1b[0m",
            "\x1b[35mhi there #2a\x1b[0m",
            "\x1b[34mhi there #3\x1b[0m",
            "\x1b[35mhi there #3\x1b[0m",
            "\x1b[35mhi there #4\x1b[0m",
            "",
        )
    )


def test_logs_error(quantum_job, generate_get_job_response, capsys):
    quantum_job._aws_session.get_job.side_effect = (
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="RUNNING"),
        generate_get_job_response(status="COMPLETED"),
    )
    quantum_job._aws_session.describe_log_streams.side_effect = (
        ClientError(
            {
                "Error": {
                    "Code": "UnknownCode",
                    "Message": "Some error message",
                }
            },
            "DescribeLogStreams",
        ),
    )

    with pytest.raises(ClientError, match="Some error message"):
        quantum_job.logs(wait=True, poll=1)
