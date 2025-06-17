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

from braket.ir.blackbird import Program as BlackbirdProgram
from braket.task_result import (
    AdditionalMetadata,
    PhotonicModelTaskResult,
    TaskMetadata,
    XanaduMetadata,
)
from braket.tasks import PhotonicModelQuantumTaskResult


@pytest.fixture
def task_metadata():
    return TaskMetadata(**{"id": "task_arn", "deviceId": "arn1", "shots": 100})


@pytest.fixture
def xanadu_metadata():
    return XanaduMetadata(compiledProgram="DECLARE ro BIT[2];")


@pytest.fixture
def blackbird_program():
    return BlackbirdProgram(source="Vac | q[0]")


@pytest.fixture
def additional_metadata(blackbird_program, xanadu_metadata):
    return AdditionalMetadata(action=blackbird_program, xanaduMetadata=xanadu_metadata)


@pytest.fixture
def measurements():
    return [[[1, 2, 3, 4]], [[4, 3, 2, 1]], [[0, 0, 0, 0]]]


@pytest.fixture
def result_1(measurements, task_metadata, additional_metadata):
    return PhotonicModelTaskResult(
        measurements=measurements,
        taskMetadata=task_metadata,
        additionalMetadata=additional_metadata,
    )


@pytest.fixture
def result_1_str(result_1):
    return result_1.json()


@pytest.fixture
def empty_result(task_metadata, additional_metadata):
    updated_metadata = task_metadata.copy()
    updated_metadata.id = "empty_arn"
    return PhotonicModelTaskResult(
        taskMetadata=updated_metadata, additionalMetadata=additional_metadata
    )


def test_from_object_equals_from_string(result_1, result_1_str):
    assert PhotonicModelQuantumTaskResult.from_object(
        result_1
    ) == PhotonicModelQuantumTaskResult.from_string(result_1_str)


def test_equality(result_1, empty_result):
    quantum_result1 = PhotonicModelQuantumTaskResult.from_object(result_1)
    quantum_empty = PhotonicModelQuantumTaskResult.from_object(empty_result)
    non_result = "not a quantum task result"

    assert quantum_result1 == quantum_result1
    assert quantum_result1 != quantum_empty
    assert quantum_result1 != non_result
