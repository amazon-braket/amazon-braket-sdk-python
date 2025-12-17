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

from abc import ABC, abstractmethod

from braket.tasks.quantum_task import TaskSpecification


class ValidationPass(ABC):
    @abstractmethod
    def validate(self, task_specification: TaskSpecification) -> None:
        """
        An emulator validator is used to perform some non-modifying validation
        pass on an input program. Implementations of validate should return
        nothing if the input program passes validation and raise an error otherwise.

        Args:
            task_specification (TaskSpecification): The program to be evaluated against this
                criteria.
        """
        raise NotImplementedError

    def run(self, task_specification: TaskSpecification) -> TaskSpecification:
        """
        Validate the input program and return the program, unmodified.

        Args:
            task_specification (TaskSpecification): The program to validate.

        Returns:
            TaskSpecification: The unmodified program passed in as input.
        """
        self.validate(task_specification)
        return task_specification

    def __call__(self, task_specification: TaskSpecification) -> TaskSpecification:
        return self.run(task_specification)
