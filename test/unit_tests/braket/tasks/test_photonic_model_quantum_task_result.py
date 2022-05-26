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

import pytest

from braket.task_result import AdditionalMetadata, TaskMetadata
from braket.tasks import PhotonicModelQuantumTaskResult


@pytest.fixture
def task_metadata():
    return TaskMetadata(**{"id": "task_arn", "deviceId": "arn1", "shots": 100})


# @pytest.fixture
# def additional_metadata

# def test_equality(str1, str2):
#     result1 = PhotonicModelQuantumTaskResult.from_string(str1)
