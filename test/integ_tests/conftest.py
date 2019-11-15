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
from aqx.qdk.aws.aws_session import AwsSession


@pytest.fixture
def aws_session():
    profile_name = os.environ["AWS_PROFILE"]
    boto_session = boto3.session.Session(profile_name=profile_name)
    return AwsSession(boto_session)
