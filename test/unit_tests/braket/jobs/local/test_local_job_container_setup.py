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

import os
from unittest.mock import Mock, mock_open, patch

import pytest

from braket.jobs.local.local_job_container_setup import setup_container


@pytest.fixture
def aws_session():
    _aws_session = Mock()
    _aws_session.boto_session.get_credentials.return_value.access_key = "Test Access Key"
    _aws_session.boto_session.get_credentials.return_value.secret_key = "Test Secret Key"
    _aws_session.boto_session.get_credentials.return_value.token = None
    _aws_session.region = "Test Region"
    return _aws_session


@pytest.fixture
def container():
    _container = Mock()
    return _container


@pytest.fixture
def creation_kwargs():
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
        "outputDataConfig": {"s3Path": "s3://test_bucket/test_location/"},
        "deviceConfig": {"devices": ["test device ARN"]},
        "jobName": "Test-Job-Name",
        "roleArn": "arn:aws:iam::875981177017:role/AmazonBraketJobRole",
    }


@pytest.fixture
def compressed_script_mode_config():
    return {
        "scriptModeConfig": {
            "entryPoint": "my_file:start_here",
            "s3Uri": "s3://amazon-braket-jobs/job-path/my_archive.gzip",
            "compressionType": "gzip",
        }
    }


@pytest.fixture
def expected_envs():
    return {
        "AMZN_BRAKET_CHECKPOINT_DIR": "/opt/omega/checkpoints",
        "AMZN_BRAKET_DEVICE_ARN": "test device ARN",
        "AMZN_BRAKET_IMAGE_SETUP_SCRIPT": "s3://braket-external-assets-preview-us-west-2/"
        "HybridJobsAccess/scripts/setup-container.sh",
        "AMZN_BRAKET_JOB_NAME": "Test-Job-Name",
        "AMZN_BRAKET_JOB_RESULTS_DIR": "/opt/braket/model",
        "AMZN_BRAKET_JOB_RESULTS_S3_PATH": "test_location/Test-Job-Name/output",
        "AMZN_BRAKET_OUT_S3_BUCKET": "test_bucket",
        "AMZN_BRAKET_SCRIPT_ENTRY_POINT": "my_file:start_here",
        "AMZN_BRAKET_SCRIPT_S3_URI": "s3://amazon-braket-jobs/job-path/my_file.py",
        "AMZN_BRAKET_TASK_RESULTS_S3_URI": "s3://test_bucket/jobs/Test-Job-Name/tasks",
        "AWS_ACCESS_KEY_ID": "Test Access Key",
        "AWS_DEFAULT_REGION": "Test Region",
        "AWS_SECRET_ACCESS_KEY": "Test Secret Key",
    }


@pytest.fixture
def input_data_config():
    return [
        # This is a valid data source.
        {
            "compressionType": "NONE",
            "dataSource": {"s3DataSource": {"s3Uri": "s3://input_bucket/input_location/b/f.txt"}},
        },
        # This is a another valid data source.
        {
            "compressionType": "NONE",
            "dataSource": {"s3DataSource": {"s3Uri": "s3://input_bucket/input_location/c/f2.txt"}},
        },
        # This is a GZipped data source. Not supported.
        {
            "compressionType": "GZIP",
            "dataSource": {"s3DataSource": {"s3Uri": "s3://input_bucket/input_location/b/f3.txt"}},
        },
        # This is a local data source. Not supported.
        {
            "compressionType": "NONE",
            "dataSource": {
                "fileSystemDataSource": {
                    "directoryPath": "/some/temp/dir",
                    "fileSystemAccessMode": "RO",
                    "fileSystemId": "SystemId",
                    "fileSystemType": "type",
                }
            },
        },
    ]


@pytest.fixture
def input_s3_list_results():
    return [
        {
            "Contents": [
                {
                    "Key": "test_key",
                }
            ],
            "IsTruncated": True,
            "NextContinuationToken": "ContToken",
        },
        {
            "Contents": [
                {
                    "Key": "test_key2",
                }
            ],
            "IsTruncated": False,
        },
        {
            "Contents": [
                {
                    "Key": "test_key3",
                }
            ],
            "IsTruncated": False,
        },
    ]


def test_basic_setup(container, aws_session, creation_kwargs, expected_envs):
    aws_session.parse_s3_uri.return_value = ["test_bucket", "test_location"]
    envs = setup_container(container, aws_session, **creation_kwargs)
    assert envs == expected_envs
    container.makedir.assert_any_call("/opt/ml/model")
    container.makedir.assert_any_call(expected_envs["AMZN_BRAKET_CHECKPOINT_DIR"])
    assert container.makedir.call_count == 2


def test_compressed_script_mode(
    container, aws_session, creation_kwargs, expected_envs, compressed_script_mode_config
):
    creation_kwargs["algorithmSpecification"] = compressed_script_mode_config
    expected_envs["AMZN_BRAKET_SCRIPT_S3_URI"] = "s3://amazon-braket-jobs/job-path/my_archive.gzip"
    expected_envs["AMZN_BRAKET_SCRIPT_COMPRESSION_TYPE"] = "gzip"
    aws_session.parse_s3_uri.return_value = ["test_bucket", "test_location"]
    envs = setup_container(container, aws_session, **creation_kwargs)
    assert envs == expected_envs
    container.makedir.assert_any_call("/opt/ml/model")
    container.makedir.assert_any_call(expected_envs["AMZN_BRAKET_CHECKPOINT_DIR"])
    assert container.makedir.call_count == 2


@patch("json.dump")
@patch("tempfile.TemporaryDirectory")
def test_hyperparameters(tempfile, json, container, aws_session, creation_kwargs, expected_envs):
    with patch("builtins.open", mock_open()):
        tempfile.return_value.__enter__.return_value = "temporaryDir"
        creation_kwargs["hyperParameters"] = {"test": "hyper"}
        expected_envs["AMZN_BRAKET_HP_FILE"] = "/opt/braket/input/config/hyperparameters.json"
        aws_session.parse_s3_uri.return_value = ["test_bucket", "test_location"]
        envs = setup_container(container, aws_session, **creation_kwargs)
        assert envs == expected_envs
        container.makedir.assert_any_call("/opt/ml/model")
        container.makedir.assert_any_call(expected_envs["AMZN_BRAKET_CHECKPOINT_DIR"])
        assert container.makedir.call_count == 2
        container.copy_to.assert_called_with(
            os.path.join("temporaryDir", "hyperparameters.json"),
            "/opt/ml/input/config/hyperparameters.json",
        )


@patch("braket.jobs.local.local_job_container_setup.Path")
@patch("os.listdir")
@patch("tempfile.TemporaryDirectory")
def test_inputs(
    mock_tempfile,
    mock_listdir,
    mock_path,
    container,
    aws_session,
    creation_kwargs,
    expected_envs,
    input_data_config,
    input_s3_list_results,
):
    with patch("builtins.open", mock_open()):
        mock_tempfile.return_value.__enter__.return_value = "temporaryDir"
        mock_listdir.return_value = ["input_file0.txt", "input_file1.txt"]
        creation_kwargs["inputDataConfig"] = input_data_config
        expected_envs["AMZN_BRAKET_INPUT_DIR"] = "/opt/braket/input/data"
        aws_session.parse_s3_uri.return_value = ["test_bucket", "test_location"]
        aws_session.s3_client.list_objects_v2.side_effect = input_s3_list_results
        envs = setup_container(container, aws_session, **creation_kwargs)
        assert envs == expected_envs
        container.makedir.assert_any_call("/opt/ml/model")
        container.makedir.assert_any_call(expected_envs["AMZN_BRAKET_CHECKPOINT_DIR"])
        assert container.makedir.call_count == 2
        container.copy_to.assert_any_call(
            os.path.join("temporaryDir", "input_file0.txt"), "/opt/ml/input/data/"
        )
        container.copy_to.assert_any_call(
            os.path.join("temporaryDir", "input_file1.txt"), "/opt/ml/input/data/"
        )
        assert container.copy_to.call_count == 2
        aws_session.parse_s3_uri.assert_any_call("s3://test_bucket/test_location/")
        aws_session.parse_s3_uri.assert_any_call("s3://input_bucket/input_location/b/f.txt")
        aws_session.parse_s3_uri.assert_any_call("s3://input_bucket/input_location/c/f2.txt")
        assert aws_session.parse_s3_uri.call_count == 3


@patch("os.listdir")
@patch("tempfile.TemporaryDirectory")
def test_not_supported_inputs(
    mock_tempfile, mock_listdir, container, aws_session, creation_kwargs, expected_envs
):
    with patch("builtins.open", mock_open()):
        mock_tempfile.return_value.__enter__.return_value = "temporaryDir"
        mock_listdir.return_value = []
        creation_kwargs["inputDataConfig"] = []
        aws_session.parse_s3_uri.return_value = ["test_bucket", "test_location"]
        aws_session.s3_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "test_key",
                }
            ],
            "IsTruncated": False,
        }
        envs = setup_container(container, aws_session, **creation_kwargs)
        assert envs == expected_envs
        container.makedir.assert_any_call("/opt/ml/model")
        container.makedir.assert_any_call(expected_envs["AMZN_BRAKET_CHECKPOINT_DIR"])
        assert container.makedir.call_count == 2
        assert container.copy_to.call_count == 0
        aws_session.parse_s3_uri.assert_any_call("s3://test_bucket/test_location/")
        assert aws_session.parse_s3_uri.call_count == 1


def test_temporary_credentials(container, aws_session, creation_kwargs, expected_envs):
    aws_session.boto_session.get_credentials.return_value.token = "Test Token"
    expected_envs["AWS_SESSION_TOKEN"] = "Test Token"
    aws_session.parse_s3_uri.return_value = ["test_bucket", "test_location"]
    envs = setup_container(container, aws_session, **creation_kwargs)
    assert envs == expected_envs
    container.makedir.assert_any_call("/opt/ml/model")
    container.makedir.assert_any_call(expected_envs["AMZN_BRAKET_CHECKPOINT_DIR"])
    assert container.makedir.call_count == 2
