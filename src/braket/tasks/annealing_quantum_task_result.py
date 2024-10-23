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

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

import numpy as np

from braket.annealing import ProblemType
from braket.task_result import AdditionalMetadata, AnnealingTaskResult, TaskMetadata


@dataclass
class AnnealingQuantumTaskResult:
    """Result of an annealing problem quantum task execution. This class is intended
    to be initialized by a QuantumTask class.

    Args:
        record_array (np.recarray): numpy array with keys 'solution' (np.ndarray)
            where row is solution, column is value of the variable, 'solution_count' (numpy.ndarray)
            the number of times the solutions occurred, and 'value' (numpy.ndarray) the
            output or energy of the solutions.
        variable_count (int): the number of variables
        problem_type (ProblemType): the type of annealing problem
        task_metadata (TaskMetadata): Quantum task metadata.
        additional_metadata (AdditionalMetadata): Additional metadata about the quantum task
    """

    record_array: np.recarray
    variable_count: int
    problem_type: ProblemType
    task_metadata: TaskMetadata
    additional_metadata: AdditionalMetadata

    def data(
        self,
        selected_fields: list[str] | None = None,
        sorted_by: str = "value",
        reverse: bool = False,
    ) -> Generator[tuple]:
        """Yields the data in record_array

        Args:
            selected_fields (Optional[list[str]]): selected fields to return.
                Options are 'solution', 'value', and 'solution_count'. Default is None.
            sorted_by (str): Sorts the data by this field.
                Options are 'solution', 'value', and 'solution_count'. Default is 'value'.
            reverse (bool): If True, returns the data in reverse order. Default is False.

        Yields:
            Generator[tuple]: data in record_array
        """
        if selected_fields is None:
            selected_fields = ["solution", "value", "solution_count"]

        if sorted_by is None:
            order = np.arange(len(self.record_array))
        else:
            order = np.argsort(self.record_array[sorted_by])

        if reverse:
            order = np.flip(order)

        for i in order:
            yield tuple(self.record_array[field][i] for field in selected_fields)

    def __eq__(self, other: AnnealingQuantumTaskResult) -> bool:
        if isinstance(other, AnnealingQuantumTaskResult):
            # __eq__ on numpy arrays results in an array of booleans and therefore can't use
            # the default dataclass __eq__ implementation. Override equals to check if all
            # elements in the array are equal.
            self_fields = (
                self.variable_count,
                self.problem_type,
                self.task_metadata,
                self.additional_metadata,
            )
            other_fields = (
                other.variable_count,
                other.problem_type,
                other.task_metadata,
                other.additional_metadata,
            )
            return (self.record_array == other.record_array).all() and self_fields == other_fields
        return NotImplemented

    @staticmethod
    def from_object(result: AnnealingTaskResult) -> AnnealingQuantumTaskResult:
        """Create AnnealingQuantumTaskResult from AnnealingTaskResult object

        Args:
            result (AnnealingTaskResult): AnnealingTaskResult object

        Returns:
            AnnealingQuantumTaskResult: An AnnealingQuantumTaskResult based on the
            given result object
        """
        return AnnealingQuantumTaskResult._from_object(result)

    @staticmethod
    def from_string(result: str) -> AnnealingQuantumTaskResult:
        """Create AnnealingQuantumTaskResult from string

        Args:
            result (str): JSON object string

        Returns:
            AnnealingQuantumTaskResult: An AnnealingQuantumTaskResult based on the given string
        """
        return AnnealingQuantumTaskResult._from_object(AnnealingTaskResult.parse_raw(result))

    @classmethod
    def _from_object(cls, result: AnnealingTaskResult) -> AnnealingQuantumTaskResult:
        solutions = np.asarray(result.solutions, dtype=int)
        values = np.asarray(result.values, dtype=float)
        if not result.solutionCounts:
            solution_counts = np.ones(len(solutions), dtype=int)
        else:
            solution_counts = np.asarray(result.solutionCounts, dtype=int)
        record_array = AnnealingQuantumTaskResult._create_record_array(
            solutions, solution_counts, values
        )
        variable_count = result.variableCount
        problem_type = ProblemType[result.additionalMetadata.action.type.value]
        task_metadata = result.taskMetadata
        additional_metadata = result.additionalMetadata
        return cls(
            record_array=record_array,
            variable_count=variable_count,
            problem_type=problem_type,
            task_metadata=task_metadata,
            additional_metadata=additional_metadata,
        )

    @staticmethod
    def _create_record_array(
        solutions: np.ndarray, solution_counts: np.ndarray, values: np.ndarray
    ) -> np.recarray:
        """Create a solutions record for AnnealingQuantumTaskResult

        Args:
            solutions (np.ndarray): row is solution, column is value of the variable
            solution_counts (np.ndarray): list of number of times the solutions occurred
            values (np.ndarray): list of the output or energy of the solutions

        Returns:
            np.recarray: A record array for solutions, value, and solution_count.
        """
        num_solutions, variable_count = solutions.shape
        datatypes = [
            ("solution", solutions.dtype, (variable_count,)),
            ("value", values.dtype),
            ("solution_count", solution_counts.dtype),
        ]

        record = np.rec.array(np.zeros(num_solutions, dtype=datatypes))
        record["solution"] = solutions
        record["value"] = values
        record["solution_count"] = solution_counts
        return record
