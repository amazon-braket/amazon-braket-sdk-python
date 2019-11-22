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

import json

import pytest
from aqx.qdk.aws import AwsQpuArns

BUCKET_NAME = "simulator-output-bucket"
FILENAME = "integ-tests/test_task_reading.json"

TEST_S3_OBJ_CONTENTS = {
    "TaskMetadata": {
        "Id": "UUID_blah",
        "Status": "COMPLETED",
        "BackendArn": AwsQpuArns.RIGETTI,
        "CwLogGroupArn": "blah",
        "Program": "....",
        "CreatedAt": "02/12/22 21:23",
        "UpdatedAt": "02/13/22 21:23",
    }
}


@pytest.fixture
def setup_s3_bucket(aws_session):
    region = "us-west-2"
    s3 = aws_session.boto_session.resource("s3", region_name=region)
    obj = s3.Object(BUCKET_NAME, FILENAME)
    try:
        obj_body = obj.get()["Body"].read().decode("utf-8")
        assert obj_body == json.dumps(TEST_S3_OBJ_CONTENTS)
    except s3.meta.client.exceptions.NoSuchBucket:
        # Create s3 bucket
        s3.create_bucket(
            ACL="private",
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
        setup_s3_bucket(aws_session)
    except s3.meta.client.exceptions.NoSuchKey:
        # Put s3 object
        obj.put(ACL="private", Body=json.dumps(TEST_S3_OBJ_CONTENTS, indent=4))
    except AssertionError:
        # Put s3 object
        obj.put(ACL="private", Body=json.dumps(TEST_S3_OBJ_CONTENTS, indent=4))


@pytest.mark.usefixtures("setup_s3_bucket")
def test_retrieve_s3_object_body(aws_session):
    obj_body = aws_session.retrieve_s3_object_body(BUCKET_NAME, FILENAME)
    assert obj_body == json.dumps(TEST_S3_OBJ_CONTENTS, indent=4)
