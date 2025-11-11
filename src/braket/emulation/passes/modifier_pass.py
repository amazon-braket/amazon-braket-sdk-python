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


class ModifierPass(ABC):
    _supported_specifications: TaskSpecification

    @abstractmethod
    def modify(self, task_specification: TaskSpecification) -> TaskSpecification:
        """
        An emulator modifier is used to perform some potentially modifying validation
        pass on an input program. Implementations of modify should return the same
        specification if the input program passes validation and raise an error otherwise.

        Args:
            task_specification (TaskSpecification): The program to be evaluated against this
                criteria.

        Returns:
            task_specificaiton (TaskSpecification): The (potentially) modified program
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
        if isinstance(task_specification, self.supported_specifications):
            self.modify(task_specification)
        return task_specification

    def __call__(self, task_specification: TaskSpecification) -> TaskSpecification:
        return self.run(task_specification)

    @property
    def supported_specifications(self) -> TaskSpecification:
        """List of supported specifications for a ValidationPass

        Returns:
            TaskSpecification:
                tuple, single, or union of supported specifications
        """
        return self._supported_specifications
