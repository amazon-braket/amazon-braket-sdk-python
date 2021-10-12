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

import json
from unittest.mock import Mock, mock_open, patch

import pytest

from braket.jobs.local.local_job import LocalQuantumJob


@pytest.fixture
def aws_session():
    _aws_session = Mock()
    return _aws_session


@pytest.fixture
def job_results():
    return {"dataFormat": "plaintext", "dataDictionary": {"some_results": {"excellent": "here"}}}


@pytest.fixture
def run_log():
    test_log = (
        "This is a multi-line log.\n"
        "This is the next line.\n"
        "Metrics - timestamp=1633027264.5406773; Cost=-4.034; iteration_number=0;\n"
        "Metrics - timestamp=1633027288.6284382; Cost=-3.957; iteration_number=1;\n"
    )
    return test_log


@pytest.fixture
def test_envs():
    return {"Test": "Env"}


@pytest.mark.parametrize(
    "creation_kwargs",
    [
        (
            {
                "jobName": "Test-Job-Name",
                "algorithmSpecification": {"containerImage": {"uri": "file://test-URI"}},
                "checkpointConfig": {"localPath": "test/local/path/"},
            }
        ),
        (
            {
                "jobName": "Test-Job-Name",
                "algorithmSpecification": {"containerImage": {"uri": "file://test-URI"}},
                "checkpointConfig": {},
            }
        ),
        (
            {
                "jobName": "Test-Job-Name",
                "algorithmSpecification": {"containerImage": {"uri": "file://test-URI"}},
            }
        ),
        (
            {
                "jobName": "Test-Job-Name",
                "algorithmSpecification": {},
            }
        ),
    ],
)
@patch("braket.jobs.local.local_job.prepare_quantum_job")
@patch("braket.jobs.local.local_job.retrieve_image")
@patch("braket.jobs.local.local_job.setup_container")
@patch("braket.jobs.local.local_job._LocalJobContainer")
@patch("os.path.isdir")
def test_create(
    mock_dir,
    mock_container,
    mock_setup,
    mock_retrieve_image,
    mock_prepare_job,
    aws_session,
    creation_kwargs,
    job_results,
    run_log,
    test_envs,
):
    with patch("builtins.open", mock_open()) as file_open:
        mock_dir.return_value = False
        mock_prepare_job.return_value = creation_kwargs

        mock_container_open = mock_container.return_value.__enter__.return_value
        mock_container_open.run_log = run_log
        file_read = file_open()
        file_read.read.return_value = json.dumps(job_results)
        mock_setup.return_value = test_envs

        job = LocalQuantumJob.create(
            device_arn=Mock(),
            source_module=Mock(),
            entry_point=Mock(),
            image_uri=Mock(),
            job_name=Mock(),
            code_locatio=Mock(),
            role_arn=Mock(),
            hyperparameters=Mock(),
            input_data_config=Mock(),
            instance_config=Mock(),
            stopping_condition=Mock(),
            output_data_config=Mock(),
            copy_checkpoints_from_job=Mock(),
            checkpoint_config=Mock(),
            vpc_config=Mock(),
            aws_session=aws_session,
        )
        assert job.name == "Test-Job-Name"
        assert job.arn == "local:job/Test-Job-Name"
        assert job.state() == "COMPLETE"
        assert job.run_log == run_log
        assert job.metadata() is None
        assert job.cancel() is None
        assert job.download_result() is None
        assert job.logs() is None
        assert job.result() == job_results["dataDictionary"]
        assert job.metrics() == {
            "Cost": [-4.034, -3.957],
            "iteration_number": [0.0, 1.0],
            "timestamp": [1633027264.5406773, 1633027288.6284382],
        }
        mock_setup.assert_called_with(mock_container_open, aws_session, **creation_kwargs)
        mock_container_open.run_local_job.assert_called_with(test_envs)


@patch("os.path.isdir")
def test_read_runlog_file(mock_dir):
    mock_dir.return_value = True
    with patch("builtins.open", mock_open()) as file_open:
        file_read = file_open()
        file_read.read.return_value = "Test Log"
        job = LocalQuantumJob("local:job/Fake-Job")
        assert job.run_log == "Test Log"


@pytest.mark.xfail(raises=ValueError)
@patch("braket.jobs.local.local_job.prepare_quantum_job")
@patch("os.path.isdir")
def test_create_existing_job(mock_dir, mock_prepare_job, aws_session):
    mock_dir.return_value = True
    mock_prepare_job.return_value = {
        "jobName": "Test-Job-Name",
        "algorithmSpecification": {"containerImage": {"uri": "file://test-URI"}},
        "checkpointConfig": {"localPath": "test/local/path/"},
    }
    LocalQuantumJob.create(
        device_arn=Mock(),
        source_module=Mock(),
        entry_point=Mock(),
        image_uri=Mock(),
        job_name=Mock(),
        code_locatio=Mock(),
        role_arn=Mock(),
        hyperparameters=Mock(),
        input_data_config=Mock(),
        instance_config=Mock(),
        stopping_condition=Mock(),
        output_data_config=Mock(),
        copy_checkpoints_from_job=Mock(),
        checkpoint_config=Mock(),
        vpc_config=Mock(),
        aws_session=aws_session,
    )


@pytest.mark.xfail(raises=ValueError)
def test_invalid_arn():
    LocalQuantumJob("Invalid-Arn")


@pytest.mark.xfail(raises=ValueError)
def test_missing_job_dir():
    LocalQuantumJob("local:job/Missing-Dir")


@pytest.mark.xfail(raises=ValueError)
@patch("os.path.isdir")
def test_missing_runlog_file(mock_dir):
    mock_dir.return_value = True
    job = LocalQuantumJob("local:job/Fake-Dir")
    job.run_log


@pytest.mark.xfail(raises=ValueError)
@patch("os.path.isdir")
def test_missing_results_file(mock_dir):
    mock_dir.return_value = True
    job = LocalQuantumJob("local:job/Fake-Dir")
    job.result()
