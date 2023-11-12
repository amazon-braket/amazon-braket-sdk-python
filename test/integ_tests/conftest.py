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

import os

import boto3
import pytest
from botocore.exceptions import ClientError

from braket.aws.aws_device import AwsDevice
from braket.aws.aws_quantum_job import AwsQuantumJob
from braket.aws.aws_session import AwsSession

SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
DM1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/dm1"
TN1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/tn1"
SIMULATOR_ARNS = [SV1_ARN, DM1_ARN, TN1_ARN]


@pytest.fixture(scope="session")
def boto_session():
    profile_name = os.environ["AWS_PROFILE"]
    return boto3.session.Session(profile_name=profile_name)


@pytest.fixture(scope="session")
def aws_session(boto_session):
    return AwsSession(boto_session)


@pytest.fixture(scope="session")
def s3_resource(boto_session):
    return boto_session.resource("s3")


@pytest.fixture(scope="session")
def s3_client(boto_session):
    return boto_session.client("s3")


@pytest.fixture(scope="session")
def account_id(boto_session):
    return boto_session.client("sts").get_caller_identity()["Account"]


@pytest.fixture(scope="session")
def s3_bucket(s3_resource, s3_client, account_id, boto_session):
    """Create / get S3 bucket for tests"""

    region_name = boto_session.region_name
    bucket_name = f"amazon-braket-sdk-integ-tests-{account_id}"
    bucket = s3_resource.Bucket(bucket_name)

    try:
        # Determine if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            bucket.create(
                ACL="private", CreateBucketConfiguration={"LocationConstraint": region_name}
            )

    return bucket_name


@pytest.fixture(scope="module")
def s3_prefix():
    """Returns the module path of the test, e.g. integ_tests/test_simulator_quantum_task"""

    # current test path, e.g. ...
    # test/integ_tests/test_simulator_quantum_task.py::test_simulator_quantum_task (setup)
    current_test_path = os.environ.get("PYTEST_CURRENT_TEST")

    # strip off the filename extension and test/
    return current_test_path.rsplit(".py")[0].replace("test/", "")


@pytest.fixture(scope="module")
def s3_destination_folder(s3_bucket, s3_prefix):
    return AwsSession.S3DestinationFolder(s3_bucket, s3_prefix)


@pytest.fixture(scope="session")
def braket_simulators(aws_session):
    return {
        simulator_arn: AwsDevice(simulator_arn, aws_session) for simulator_arn in SIMULATOR_ARNS
    }


@pytest.fixture(scope="session")
def braket_devices():
    return AwsDevice.get_devices()


@pytest.fixture(scope="session")
def created_braket_devices(aws_session, braket_devices):
    return {
        device.arn: AwsDevice(device.arn, aws_session) for device in braket_devices
    }


@pytest.fixture(scope="session")
def completed_quantum_job(aws_session):
    job = AwsQuantumJob.create(
        "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        source_module="test/integ_tests/job_test_script.py",
        entry_point="job_test_script:start_here",
        aws_session=aws_session,
        wait_until_complete=True,
        hyperparameters={"test_case": "completed"},
    )
    return job

@pytest.fixture(scope="session")
def failed_quantum_job(aws_session):
    job = AwsQuantumJob.create(
        "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        source_module="test/integ_tests/job_test_script.py",
        entry_point="job_test_script:start_here",
        aws_session=aws_session,
        wait_until_complete=False,
        hyperparameters={"test_case": "failed"},
    )
    return job


