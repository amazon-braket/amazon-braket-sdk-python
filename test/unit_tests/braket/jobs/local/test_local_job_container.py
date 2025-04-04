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

import base64
import subprocess
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch

import pytest

from braket.jobs.local.local_job_container import _LocalJobContainer


@pytest.fixture
def repo_uri():
    return "012345678901.dkr.ecr.us-west-2.amazonaws.com"


@pytest.fixture
def image_uri(repo_uri):
    return f"{repo_uri}/my-repo:my-tag"


@pytest.fixture
def aws_session():
    _aws_session = Mock()
    return _aws_session


@pytest.fixture
def popen_result():
    mock = Mock()
    mock.stdout.readline.side_effect = [
        str.encode("this\n"),
        str.encode("is a\n"),
        str.encode("test\n"),
    ]
    mock.poll.side_effect = [None, None, 0]
    return mock


@patch("subprocess.check_output")
@patch("subprocess.run")
def test_start_and_stop(mock_run, mock_check_output, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
    ]
    with _LocalJobContainer(image_uri, aws_session):
        pass
    mock_check_output.assert_any_call(["docker", "images", "-q", image_uri])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    assert mock_check_output.call_count == 2
    mock_run.assert_any_call(["docker", "stop", running_container_name])
    assert mock_run.call_count == 1


@pytest.mark.parametrize(
    "forced_update, check_output, local_image_name",
    [
        (
            False,
            [
                str.encode(""),  # This means that the container image does not exist locally.
                str.encode("LocalImageName"),
                str.encode("RunningContainer"),
            ],
            "LocalImageName",
        ),
        (
            True,
            [
                str.encode(""),  # This means that the container image does not exist locally.
                str.encode("LocalImageName"),
                str.encode("RunningContainer"),
            ],
            "LocalImageName",
        ),
        (
            True,  # When force update is true, we'll pull containers, even if they exist locally.
            [
                str.encode("PreUpdateName"),  # This means that the container image exists locally.
                str.encode("PostUpdateName"),  # This means that the container image exists locally.
                str.encode("RunningContainer"),
            ],
            "PostUpdateName",
        ),
    ],
)
@patch("subprocess.check_output")
@patch("subprocess.run")
def test_pull_container(
    mock_run,
    mock_check_output,
    repo_uri,
    image_uri,
    aws_session,
    forced_update,
    check_output,
    local_image_name,
):
    running_container_name = "RunningContainer"
    test_token = "Test Token"
    mock_check_output.side_effect = check_output
    aws_session.ecr_client.get_authorization_token.return_value = {
        "authorizationData": [{"authorizationToken": base64.b64encode(str.encode(test_token))}]
    }
    with _LocalJobContainer(
        image_uri=image_uri, aws_session=aws_session, force_update=forced_update
    ):
        pass
    mock_check_output.assert_any_call(["docker", "images", "-q", image_uri])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    assert mock_check_output.call_count == len(check_output)
    mock_run.assert_any_call(["docker", "login", "-u", "AWS", "-p", test_token, repo_uri])
    mock_run.assert_any_call(["docker", "pull", image_uri])
    mock_run.assert_any_call(["docker", "stop", running_container_name])
    assert mock_run.call_count == 3


@patch("subprocess.check_output")
@patch("subprocess.run")
def test_pull_container_forced_update_invalid_name(
    mock_run, mock_check_output, repo_uri, aws_session
):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    mock_logger = Mock()
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
    ]
    with _LocalJobContainer(
        image_uri=local_image_name, aws_session=aws_session, force_update=True, logger=mock_logger
    ):
        pass
    mock_logger.warning.assert_called_with(f"Unable to update {local_image_name}.")
    mock_check_output.assert_any_call(["docker", "images", "-q", local_image_name])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    assert mock_check_output.call_count == 2
    mock_run.assert_any_call(["docker", "stop", running_container_name])
    assert mock_run.call_count == 1


@patch("subprocess.check_output")
@patch("subprocess.run")
@patch("subprocess.Popen")
def test_run_job_success(
    mock_popen, mock_run, mock_check_output, repo_uri, image_uri, aws_session, popen_result
):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    env_variables = {
        "ENV0": "VALUE0",
        "ENV1": "VALUE1",
    }
    run_program_name = "Run Program Name"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        str.encode(run_program_name),
    ]
    mock_popen.return_value = popen_result
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.run_local_job(env_variables)
        assert container.run_log == "this\nis a\ntest\n"
    mock_check_output.assert_any_call(["docker", "images", "-q", image_uri])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    mock_check_output.assert_any_call([
        "docker",
        "exec",
        running_container_name,
        "printenv",
        "SAGEMAKER_PROGRAM",
    ])
    assert mock_check_output.call_count == 3
    mock_popen.assert_called_with(
        [
            "docker",
            "exec",
            "-w",
            "/opt/ml/code/",
            "-e",
            "ENV0=VALUE0",
            "-e",
            "ENV1=VALUE1",
            running_container_name,
            "python",
            run_program_name,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    mock_run.assert_called_with(["docker", "stop", running_container_name])


@patch("subprocess.check_output")
@patch("subprocess.run")
@patch("subprocess.Popen")
def test_run_customer_script_fails(
    mock_popen, mock_run, mock_check_output, repo_uri, image_uri, aws_session, popen_result
):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    env_variables = {
        "ENV0": "VALUE0",
        "ENV1": "VALUE1",
    }
    run_program_name = "Run Program Name"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        str.encode(run_program_name),
    ]
    popen_result.poll.side_effect = [None, None, 400]
    mock_popen.return_value = popen_result
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.run_local_job(env_variables)
        assert container.run_log == "this\nis a\ntest\nProcess exited with code: 400"
    mock_check_output.assert_any_call(["docker", "images", "-q", image_uri])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    mock_check_output.assert_any_call([
        "docker",
        "exec",
        running_container_name,
        "printenv",
        "SAGEMAKER_PROGRAM",
    ])
    assert mock_check_output.call_count == 3
    mock_popen.assert_called_with(
        [
            "docker",
            "exec",
            "-w",
            "/opt/ml/code/",
            "-e",
            "ENV0=VALUE0",
            "-e",
            "ENV1=VALUE1",
            running_container_name,
            "python",
            run_program_name,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    mock_run.assert_called_with(["docker", "stop", running_container_name])


@patch("subprocess.check_output")
@patch("subprocess.run")
@patch("subprocess.Popen")
def test_running_throws_exception(
    mock_popen, mock_run, mock_check_output, repo_uri, image_uri, aws_session, popen_result
):
    mock_logger = Mock()
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    env_variables = {
        "ENV0": "VALUE0",
        "ENV1": "VALUE1",
    }
    run_program_name = "Run Program Name"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        str.encode(run_program_name),
    ]
    expected_exception = Exception("Test Error")
    mock_popen.side_effect = [expected_exception, None]
    with _LocalJobContainer(image_uri, aws_session, mock_logger) as container:
        container.run_local_job(env_variables)
        assert container.run_log == expected_exception
    assert mock_check_output.call_count == 3
    mock_run.assert_called_with(["docker", "stop", running_container_name])
    mock_logger.exception.assert_called_with(expected_exception)


@patch("subprocess.check_output")
@patch("subprocess.run")
def test_make_dir(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    test_dir_path = "/test/dir/path"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        str.encode(""),
    ]
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.makedir(test_dir_path)
    mock_check_output.assert_any_call(["docker", "images", "-q", image_uri])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    mock_check_output.assert_any_call([
        "docker",
        "exec",
        running_container_name,
        "mkdir",
        "-p",
        test_dir_path,
    ])
    assert mock_check_output.call_count == 3
    mock_run.assert_any_call(["docker", "stop", running_container_name])
    assert mock_run.call_count == 1


@patch("subprocess.check_output")
@patch("subprocess.run")
def test_copy_to(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    source_path = str(Path("test", "source", "dir", "path", "srcfile.txt"))
    dest_path = str(PurePosixPath("test", "dest", "dir", "path", "dstfile.txt"))
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        str.encode(""),
        str.encode(""),
    ]
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.copy_to(source_path, dest_path)
    mock_check_output.assert_any_call(["docker", "images", "-q", image_uri])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    mock_check_output.assert_any_call([
        "docker",
        "exec",
        running_container_name,
        "mkdir",
        "-p",
        str(PurePosixPath("test", "dest", "dir", "path")),
    ])
    mock_check_output.assert_any_call([
        "docker",
        "cp",
        source_path,
        f"{running_container_name}:{dest_path}",
    ])
    assert mock_check_output.call_count == 4
    mock_run.assert_any_call(["docker", "stop", running_container_name])
    assert mock_run.call_count == 1


@patch("subprocess.check_output")
@patch("subprocess.run")
def test_copy_from(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    source_path = "/test/source/dir/path/srcfile.txt"
    dest_path = "/test/dest/dir/path/dstfile.txt"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        str.encode(""),
        str.encode(""),
    ]
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.copy_from(source_path, dest_path)
    mock_check_output.assert_any_call(["docker", "images", "-q", image_uri])
    mock_check_output.assert_any_call([
        "docker",
        "run",
        "-d",
        "--rm",
        local_image_name,
        "tail",
        "-f",
        "/dev/null",
    ])
    mock_check_output.assert_any_call([
        "docker",
        "cp",
        f"{running_container_name}:{source_path}",
        dest_path,
    ])
    assert mock_check_output.call_count == 3
    mock_run.assert_any_call(["docker", "stop", running_container_name])
    assert mock_run.call_count == 1


@patch("subprocess.check_output")
@patch("subprocess.run")
@pytest.mark.xfail(raises=ValueError)
def test_run_fails_no_program(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    env_variables = {
        "ENV0": "VALUE0",
        "ENV1": "VALUE1",
    }
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        str.encode(""),
    ]
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.run_local_job(env_variables)


@patch("subprocess.check_output")
@patch("subprocess.run")
@pytest.mark.xfail(raises=subprocess.CalledProcessError)
def test_make_dir_fails(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    test_dir_path = "/test/dir/path"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        subprocess.CalledProcessError("Test Error", "test", str.encode("test output")),
    ]
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.makedir(test_dir_path)


@patch("subprocess.check_output")
@patch("subprocess.run")
@pytest.mark.xfail(raises=subprocess.CalledProcessError)
def test_copy_to_fails(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    source_path = "/test/source/dir/path/srcfile.txt"
    dest_path = "/test/dest/dir/path/dstfile.txt"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        subprocess.CalledProcessError("Test Error", "test", str.encode("test output")),
    ]
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.copy_to(source_path, dest_path)


@patch("subprocess.check_output")
@patch("subprocess.run")
@pytest.mark.xfail(raises=subprocess.CalledProcessError)
def test_copy_from_fails(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    source_path = "/test/source/dir/path/srcfile.txt"
    dest_path = "/test/dest/dir/path/dstfile.txt"
    mock_check_output.side_effect = [
        str.encode(local_image_name),
        str.encode(running_container_name),
        subprocess.CalledProcessError("Test Error", "test", str.encode("test output")),
    ]
    with _LocalJobContainer(image_uri, aws_session) as container:
        container.copy_from(source_path, dest_path)


@patch("subprocess.check_output")
@patch("subprocess.run")
@pytest.mark.xfail(raises=ValueError)
def test_pull_fails_no_auth(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    mock_check_output.side_effect = [
        str.encode(""),
        str.encode(local_image_name),
        str.encode(running_container_name),
    ]
    aws_session.ecr_client.get_authorization_token.return_value = {}
    with _LocalJobContainer(image_uri, aws_session):
        pass


@patch("subprocess.check_output")
@patch("subprocess.run")
@pytest.mark.xfail(raises=ValueError)
def test_pull_fails_invalid_uri(mock_run, mock_check_output, aws_session):
    local_image_name = "LocalImageName"
    running_container_name = "RunningContainer"
    mock_check_output.side_effect = [
        str.encode(""),
        str.encode(local_image_name),
        str.encode(running_container_name),
    ]
    aws_session.ecr_client.get_authorization_token.return_value = {}
    with _LocalJobContainer("TestURI", aws_session):
        pass


@patch("subprocess.check_output")
@patch("subprocess.run")
@pytest.mark.xfail(raises=ValueError)
def test_pull_fails_unknown_reason(mock_run, mock_check_output, repo_uri, image_uri, aws_session):
    test_token = "Test Token"
    mock_check_output.side_effect = [
        str.encode(""),
        str.encode(""),
    ]
    aws_session.ecr_client.get_authorization_token.return_value = {
        "authorizationData": [{"authorizationToken": base64.b64encode(str.encode(test_token))}]
    }
    with _LocalJobContainer(image_uri, aws_session):
        pass
