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

from collections.abc import Iterable

from braket.emulation.passes import ValidationPass
from braket.tasks.quantum_task import TaskSpecification


class EmulatorValidationError(Exception):
    """Custom exception validation errors from emulators."""


class PassManager:
    def __init__(self, passes: Iterable[ValidationPass] | None = None):
        self._passes = passes if passes is not None else []

    def transform(self, task_specification: TaskSpecification) -> TaskSpecification:
        """
        This method passes the input program through the Passes contained
        within this pass manager. A pass may simply validate a program or may
        modify or entirely transform the program (to an equivalent quantum program).

        Args:
            task_specification (TaskSpecification): The program to run the emulator passes on.

        Returns:
            TaskSpecification: A "compiled" program of the same type as the input.

        """
        for emulator_pass in self._passes:
            task_specification = emulator_pass(task_specification)
        return task_specification

    def validate(self, task_specification: TaskSpecification) -> None:
        """
        This method passes the input program through Passes that perform
        only validation, without modifying the input program.

        Args:
            task_specification (TaskSpecification): The program to validate with this
                emulator's validation passes.
        """

        try:
            for emulator_pass in self._passes:
                emulator_pass(task_specification)
        except Exception as e:
            self._raise_exception(e)

    def _raise_exception(self, exception: Exception) -> None:
        """
        Wrapper for exceptions enable modifyint the exception message if needed.

        Args:
            exception (Exception): The exception to modify and raise.
        """
        raise EmulatorValidationError(str(exception)) from exception
