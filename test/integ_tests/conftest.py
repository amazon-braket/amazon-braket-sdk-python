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

import os

import boto3
import pytest
from botocore.exceptions import ClientError
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit


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
def s3_bucket(s3_resource, boto_session):
    """Create / get S3 bucket for tests"""

    region_name = boto_session.region_name
    account_id = boto_session.client("sts").get_caller_identity()["Account"]
    bucket_name = f"braket-sdk-integ-tests-{account_id}"
    bucket = s3_resource.Bucket(bucket_name)

    try:
        bucket.create(ACL="private", CreateBucketConfiguration={"LocationConstraint": region_name})
    except ClientError as e:
        if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            pass
        else:
            raise e

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
def bell_state_and_tolerances():
    return Circuit().h(0).cnot(0, 1), {"00": (0.4, 0.6), "11": (0.4, 0.6)}


@pytest.fixture(scope="session")
def state_110_and_most_common():
    return Circuit().x(0).x(1).i(2), "110"


@pytest.fixture(scope="session")
def state_001_and_most_common():
    return Circuit().i(0).i(1).x(2), "001"
