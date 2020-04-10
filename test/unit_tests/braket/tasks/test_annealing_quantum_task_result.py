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

import numpy as np
import pytest
from braket.aws.aws_qpu_arns import AwsQpuArns
from braket.tasks import AnnealingQuantumTaskResult


@pytest.fixture
def solutions():
    return [[-1, -1, -1, -1], [1, -1, 1, 1], [1, -1, -1, 1]]


@pytest.fixture
def values():
    return [0.0, 1.0, 2.0]


@pytest.fixture
def variable_count():
    return 4


@pytest.fixture
def solution_counts():
    return [3, 2, 4]


@pytest.fixture
def problem_type():
    return "ising"


@pytest.fixture
def task_metadata():
    return {"Id": "UUID_blah_1", "Status": "COMPLETED", "BackendArn": AwsQpuArns.DWAVE, "Shots": 5}


@pytest.fixture
def dwave_metadata():
    return {
        "ActiveVariables": [0],
        "Timing": {
            "QpuSamplingTime": 1575,
            "QpuAnnealTimePerSample": 20,
            "QpuReadoutTimePerSample": 274,
            "QpuAccessTime": 10917,
            "QpuAccessOverheadTime": 3382,
            "QpuProgrammingTime": 9342,
            "QpuDelayTimePerSample": 21,
            "TotalPostProcessingTime": 117,
            "PostProcessingOverheadTime": 117,
            "TotalRealTime": 10917,
            "RunTimeChip": 1575,
            "AnnealTimePerRun": 20,
            "ReadoutTimePerRun": 274,
        },
    }


@pytest.fixture
def result_str_1(
    solutions, values, solution_counts, variable_count, problem_type, dwave_metadata, task_metadata
):
    return json.dumps(
        {
            "Solutions": solutions,
            "VariableCount": variable_count,
            "Values": values,
            "SolutionCounts": solution_counts,
            "ProblemType": problem_type,
            "DWaveMetadata": dwave_metadata,
            "TaskMetadata": task_metadata,
        }
    )


@pytest.fixture
def result_str_2(solutions, values, variable_count, problem_type, dwave_metadata, task_metadata):
    return json.dumps(
        {
            "Solutions": solutions,
            "VariableCount": variable_count,
            "Values": values,
            "SolutionCounts": None,
            "ProblemType": problem_type,
            "DWaveMetadata": dwave_metadata,
            "TaskMetadata": task_metadata,
        }
    )


@pytest.fixture
def annealing_result(
    solutions, values, solution_counts, variable_count, problem_type, dwave_metadata, task_metadata
):
    solutions = np.asarray(solutions, dtype=int)
    values = np.asarray(values, dtype=float)
    solution_counts = np.asarray(solution_counts, dtype=int)
    record_array = AnnealingQuantumTaskResult._create_record_array(
        solutions, solution_counts, values
    )
    return AnnealingQuantumTaskResult(
        record_array=record_array,
        variable_count=variable_count,
        problem_type=problem_type,
        task_metadata=task_metadata,
        additional_metadata={"DWaveMetadata": dwave_metadata},
    )


def test_from_dict(
    result_str_1,
    solutions,
    values,
    solution_counts,
    variable_count,
    problem_type,
    task_metadata,
    dwave_metadata,
):
    result = AnnealingQuantumTaskResult.from_dict(json.loads(result_str_1))
    solutions = np.asarray(solutions, dtype=int)
    values = np.asarray(values, dtype=float)
    solution_counts = np.asarray(solution_counts, dtype=int)
    assert result.variable_count == variable_count
    assert result.problem_type == problem_type
    assert result.task_metadata == task_metadata
    assert result.additional_metadata == {"DWaveMetadata": dwave_metadata}
    np.testing.assert_equal(
        result.record_array,
        AnnealingQuantumTaskResult._create_record_array(solutions, solution_counts, values),
    )


def test_from_string(
    result_str_1,
    solutions,
    values,
    solution_counts,
    variable_count,
    problem_type,
    task_metadata,
    dwave_metadata,
):
    result = AnnealingQuantumTaskResult.from_string(result_str_1)
    solutions = np.asarray(solutions, dtype=int)
    values = np.asarray(values, dtype=float)
    solution_counts = np.asarray(solution_counts, dtype=int)
    assert result.variable_count == variable_count
    assert result.problem_type == problem_type
    assert result.task_metadata == task_metadata
    assert result.additional_metadata == {"DWaveMetadata": dwave_metadata}
    np.testing.assert_equal(
        result.record_array,
        AnnealingQuantumTaskResult._create_record_array(solutions, solution_counts, values),
    )


def test_from_string_solution_counts_none(result_str_2, solutions):
    result = AnnealingQuantumTaskResult.from_string(result_str_2)
    np.testing.assert_equal(result.record_array.solution_count, np.ones(len(solutions), dtype=int))


def test_data_sort_by_none(annealing_result, solutions, values, solution_counts):
    d = list(annealing_result.data(sorted_by=None))
    for i in range(len(solutions)):
        assert (d[i][0] == solutions[i]).all()
        assert d[i][1] == values[i]
        assert d[i][2] == solution_counts[i]


def test_data_selected_fields(annealing_result, solutions, values, solution_counts):
    d = list(annealing_result.data(selected_fields=["value"]))
    for i in range(len(solutions)):
        assert d[i] == tuple([values[i]])


def test_data_reverse(annealing_result, solutions, values, solution_counts):
    d = list(annealing_result.data(reverse=True))
    num_solutions = len(solutions)
    for i in range(num_solutions):
        assert (d[i][0] == solutions[num_solutions - i - 1]).all()
        assert d[i][1] == values[num_solutions - i - 1]
        assert d[i][2] == solution_counts[num_solutions - i - 1]


def test_data_sort_by(annealing_result, solutions, values, solution_counts):
    d = list(annealing_result.data(sorted_by="solution_count"))
    min_index = np.argmin(solution_counts)
    assert (d[0][0] == solutions[min_index]).all()
    assert d[0][1] == values[min_index]
    assert d[0][2] == solution_counts[min_index]


def test_from_dict_equal_to_from_string(result_str_1):
    assert AnnealingQuantumTaskResult.from_dict(
        json.loads(result_str_1)
    ) == AnnealingQuantumTaskResult.from_string(result_str_1)


def test_equality(result_str_1, result_str_2):
    result_1 = AnnealingQuantumTaskResult.from_string(result_str_1)
    result_2 = AnnealingQuantumTaskResult.from_string(result_str_1)
    other_result = AnnealingQuantumTaskResult.from_string(result_str_2)
    non_result = "not a quantum task result"

    assert result_1 == result_2
    assert result_1 is not result_2
    assert result_1 != other_result
    assert result_1 != non_result
