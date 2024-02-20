# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
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
import os.path
import re
import sys
import tempfile
from pathlib import Path

import job_test_script
import pytest
from job_test_module.job_test_submodule.job_test_submodule_file import submodule_helper

from braket.aws import AwsSession
from braket.aws.aws_quantum_job import AwsQuantumJob
from braket.devices import Devices
from braket.jobs import Framework, get_input_data_dir, hybrid_job, retrieve_image, save_job_result


def decorator_python_version():
    aws_session = AwsSession()
    image_uri = retrieve_image(Framework.BASE, aws_session.region)
    tag = aws_session.get_full_image_tag(image_uri)
    major_version, minor_version = re.search(r"-py(\d)(\d+)-", tag).groups()
    return int(major_version), int(minor_version)


def test_failed_quantum_job(aws_session, capsys):
    """Asserts the hybrid job is failed with the output, checkpoints,
    quantum tasks not created in bucket and only input is uploaded to s3. Validate the
    results/download results have the response raising RuntimeError. Also,
    check if the logs displays the Assertion Error.
    """

    job = AwsQuantumJob.create(
        "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        source_module="test/integ_tests/job_test_script.py",
        entry_point="job_test_script:start_here",
        aws_session=aws_session,
        wait_until_complete=True,
        hyperparameters={"test_case": "failed"},
    )

    pattern = f"^arn:aws:braket:{aws_session.region}:\\d{{12}}:job/[a-z0-9-]+$"
    assert re.match(pattern=pattern, string=job.arn)

    # Check job is in failed state.
    assert job.state() == "FAILED"

    # Check whether the respective folder with files are created for script,
    # output, tasks and checkpoints.
    job_name = job.name
    s3_bucket = aws_session.default_bucket()
    subdirectory = re.match(
        rf"s3://{s3_bucket}/jobs/{job.name}/(\d+)/script/source.tar.gz",
        job.metadata()["algorithmSpecification"]["scriptModeConfig"]["s3Uri"],
    ).group(1)
    keys = aws_session.list_keys(
        bucket=s3_bucket,
        prefix=f"jobs/{job_name}/{subdirectory}/",
    )
    assert keys == [f"jobs/{job_name}/{subdirectory}/script/source.tar.gz"]

    # no results saved
    assert job.result() == {}

    job.logs()
    log_data, errors = capsys.readouterr()
    assert errors == ""
    logs_to_validate = [
        "Invoking script with the following command:",
        "braket_container.py",
        "Running Code As Process",
        "Test job started!!!!!",
        "FileNotFoundError: [Errno 2] No such file or directory: 'fake_file'",
        "Code Run Finished",
        '"user_entry_point": "braket_container.py"',
    ]

    for data in logs_to_validate:
        assert data in log_data

    assert job.metadata()["failureReason"] == (
        "AlgorithmError: FileNotFoundError: [Errno 2] "
        "No such file or directory: 'fake_file', exit code: 1"
    )


def test_completed_quantum_job(aws_session, capsys):
    """Asserts the hybrid job is completed with the output, checkpoints, quantum tasks and
    script folder created in S3 for respective hybrid job. Validate the results are
    downloaded and results are what we expect. Also, assert that logs contains all the
    necessary steps for setup and running the hybrid job and is displayed to the user.
    """

    job = AwsQuantumJob.create(
        "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        source_module="test/integ_tests/job_test_script.py",
        entry_point="job_test_script:start_here",
        wait_until_complete=True,
        aws_session=aws_session,
        hyperparameters={"test_case": "completed"},
    )

    pattern = f"^arn:aws:braket:{aws_session.region}:\\d{{12}}:job/[a-z0-9-]+$"
    assert re.match(pattern=pattern, string=job.arn)

    # check job is in completed state.
    assert job.state() == "COMPLETED"

    # Check whether the respective folder with files are created for script,
    # output, tasks and checkpoints.
    job_name = job.name
    s3_bucket = aws_session.default_bucket()
    subdirectory = re.match(
        rf"s3://{s3_bucket}/jobs/{job.name}/(\d+)/script/source.tar.gz",
        job.metadata()["algorithmSpecification"]["scriptModeConfig"]["s3Uri"],
    ).group(1)
    keys = aws_session.list_keys(
        bucket=s3_bucket,
        prefix=f"jobs/{job_name}/{subdirectory}/",
    )
    for expected_key in [
        f"jobs/{job_name}/{subdirectory}/script/source.tar.gz",
        f"jobs/{job_name}/{subdirectory}/data/output/model.tar.gz",
        f"jobs/{job_name}/{subdirectory}/checkpoints/{job_name}_plain_data.json",
        f"jobs/{job_name}/{subdirectory}/checkpoints/{job_name}.json",
    ]:
        assert any(re.match(expected_key, key) for key in keys)

    # Check that tasks exist in the correct location
    tasks_keys = aws_session.list_keys(
        bucket=s3_bucket,
        prefix=f"jobs/{job_name}/tasks/",
    )
    expected_task_location = f"jobs/{job_name}/tasks/[^/]*/results.json"
    assert any(re.match(expected_task_location, key) for key in tasks_keys)

    # Check if checkpoint is uploaded in requested format.
    for s3_key, expected_data in [
        (
            f"jobs/{job_name}/{subdirectory}/checkpoints/{job_name}_plain_data.json",
            {
                "braketSchemaHeader": {
                    "name": "braket.jobs_data.persisted_job_data",
                    "version": "1",
                },
                "dataDictionary": {"some_data": "abc"},
                "dataFormat": "plaintext",
            },
        ),
        (
            f"jobs/{job_name}/{subdirectory}/checkpoints/{job_name}.json",
            {
                "braketSchemaHeader": {
                    "name": "braket.jobs_data.persisted_job_data",
                    "version": "1",
                },
                "dataDictionary": {"some_data": "gASVBwAAAAAAAACMA2FiY5Qu\n"},
                "dataFormat": "pickled_v4",
            },
        ),
    ]:
        assert (
            json.loads(
                aws_session.retrieve_s3_object_body(s3_bucket=s3_bucket, s3_object_key=s3_key)
            )
            == expected_data
        )

    # Check downloaded results exists in the file system after the call.
    downloaded_result = f"{job_name}/{AwsQuantumJob.RESULTS_FILENAME}"
    current_dir = Path.cwd()

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        try:
            job.download_result()
            assert (
                Path(AwsQuantumJob.RESULTS_TAR_FILENAME).exists()
                and Path(downloaded_result).exists()
            )

            # Check results match the expectations.
            assert job.result() == {"converged": True, "energy": -0.2}
        finally:
            os.chdir(current_dir)

    # Check the logs and validate it contains required output.
    job.logs(wait=True)
    log_data, errors = capsys.readouterr()
    assert errors == ""
    logs_to_validate = [
        "Invoking script with the following command:",
        "braket_container.py",
        "Running Code As Process",
        "Test job started!!!!!",
        "Test job completed!!!!!",
        "Code Run Finished",
        '"user_entry_point": "braket_container.py"',
        "Reporting training SUCCESS",
    ]

    for data in logs_to_validate:
        assert data in log_data


@pytest.mark.xfail(
    (sys.version_info.major, sys.version_info.minor) != decorator_python_version(),
    raises=RuntimeError,
    reason="Python version mismatch",
)
def test_decorator_job():
    class MyClass:
        attribute = "value"

        def __str__(self):
            return f"MyClass({self.attribute})"

    @hybrid_job(
        device=Devices.Amazon.SV1,
        include_modules="job_test_script",
        dependencies=str(Path("test", "integ_tests", "requirements.txt")),
        input_data=str(Path("test", "integ_tests", "requirements")),
    )
    def decorator_job(a, b: int, c=0, d: float = 1.0, **extras):
        with open(Path(get_input_data_dir()) / "requirements.txt", "r") as f:
            assert f.readlines() == ["pytest\n"]
        with open(Path("test", "integ_tests", "requirements.txt"), "r") as f:
            assert f.readlines() == ["pytest\n"]
        assert dir(pytest)
        assert a.attribute == "value"
        assert b == 2
        assert c == 0
        assert d == 5
        assert extras["extra_arg"] == "extra_value"

        hp_file = os.environ["AMZN_BRAKET_HP_FILE"]
        with open(hp_file, "r") as f:
            hyperparameters = json.load(f)
        assert hyperparameters == {
            "a": "MyClass{value}",
            "b": "2",
            "c": "0",
            "d": "5",
            "extra_arg": "extra_value",
        }

        with open("test/output_file.txt", "w") as f:
            f.write("hello")

        return job_test_script.job_helper()

    job = decorator_job(MyClass(), 2, d=5, extra_arg="extra_value")
    assert job.result()["status"] == "SUCCESS"

    current_dir = Path.cwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        try:
            job.download_result()
            with open(Path(job.name, "test", "output_file.txt"), "r") as f:
                assert f.read() == "hello"
            assert (
                Path(job.name, "results.json").exists()
                and Path(job.name, "test").exists()
                and not Path(job.name, "test", "integ_tests").exists()
            )
        finally:
            os.chdir(current_dir)


@pytest.mark.xfail(
    (sys.version_info.major, sys.version_info.minor) != decorator_python_version(),
    raises=RuntimeError,
    reason="Python version mismatch",
)
def test_decorator_job_submodule():
    @hybrid_job(
        device=Devices.Amazon.SV1,
        include_modules=[
            "job_test_module",
        ],
        dependencies=Path(
            "test", "integ_tests", "job_test_module", "job_test_submodule", "requirements.txt"
        ),
        input_data={
            "my_input": str(Path("test", "integ_tests", "requirements.txt")),
            "my_dir": str(Path("test", "integ_tests", "job_test_module")),
        },
    )
    def decorator_job_submodule():
        with open(Path(get_input_data_dir("my_input")) / "requirements.txt", "r") as f:
            assert f.readlines() == ["pytest\n"]
        with open(Path("test", "integ_tests", "requirements.txt"), "r") as f:
            assert f.readlines() == ["pytest\n"]
        with open(
            Path(get_input_data_dir("my_dir")) / "job_test_submodule" / "requirements.txt", "r"
        ) as f:
            assert f.readlines() == ["pytest\n"]
        with open(
            Path(
                "test",
                "integ_tests",
                "job_test_module",
                "job_test_submodule",
                "requirements.txt",
            ),
            "r",
        ) as f:
            assert f.readlines() == ["pytest\n"]
        assert dir(pytest)
        save_job_result(submodule_helper())

    job = decorator_job_submodule()
    assert job.result()["status"] == "SUCCESS"
