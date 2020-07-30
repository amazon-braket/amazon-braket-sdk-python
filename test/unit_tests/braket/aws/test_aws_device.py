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

from unittest.mock import Mock

import pytest

from braket.aws import AwsDevice
from braket.circuits import Circuit


@pytest.fixture
def arn():
    return "test_arn"


@pytest.fixture
def device(arn):
    return AwsDevice(arn, Mock())


@pytest.fixture
def s3_destination_folder():
    return "bucket-foo", "key-bar"


@pytest.fixture
def circuit():
    return Circuit().h(0)


# TODO: Unit tests for AWS device once AwsQpu and AwsQuantumSimulator are deleted
# and we have new V4 *Device APIs
