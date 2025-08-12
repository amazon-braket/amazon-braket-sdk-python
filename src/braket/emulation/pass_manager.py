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
from typing import Optional, Union

from braket.emulation.passes import ProgramType, ValidationPass


class EmulatorValidationError(Exception):
    """Custom exception validation errors from emulators."""


class PassManager:
    def __init__(self, emulator_passes: Optional[Iterable[ValidationPass]] = None):
        self._emulator_passes = emulator_passes if emulator_passes is not None else []

    def transform(self, task_specification: ProgramType) -> ProgramType:
        """
        This method passes the input program through the Passes contained
        within this emulator. An emulator pass may simply validate a program or may
        modify or entirely transform the program (to an equivalent quantum program).

        Args:
            task_specification (ProgramType): The program to run the emulator passes on.

        Returns:
            ProgramType: A "compiled" program of the same type as the input.

        """
        for emulator_pass in self._emulator_passes:
            task_specification = emulator_pass(task_specification)
        return task_specification

    def validate(self, task_specification: ProgramType) -> None:
        """
        This method passes the input program through Passes that perform
        only validation, without modifying the input program.

        Args:
            task_specification (ProgramType): The program to validate with this
                emulator's validation passes.
        """

        try:
            for emulator_pass in self._emulator_passes:
                emulator_pass(task_specification)
        except Exception as e:
            self._raise_exception(e)

    def add_pass(
        self, emulator_pass: Union[Iterable[ValidationPass], ValidationPass]
    ) -> PassManager:
        """
        Append a new ValidationPass or a list of ValidationPass objects.

        Args:
            emulator_pass (Union[Iterable[ValidationPass], ValidationPass]): Either a
                single Pass object or a list of Pass objects that
                will be used in validation and program compilation passes by this
                emulator.

        Returns:
            PassManager: Returns an updated self.

        Raises:
            TypeError: If the input is not an iterable or an Pass.

        """
        if isinstance(emulator_pass, Iterable):
            self._emulator_passes.extend(emulator_pass)
        elif isinstance(emulator_pass, ValidationPass):
            self._emulator_passes.append(emulator_pass)
        else:
            raise TypeError("emulator_pass must be an Pass or an iterable of Pass")
        return self

    def _raise_exception(self, exception: Exception) -> None:
        """
        Wrapper for exceptions, appends the emulator's name to the exception
        note.

        Args:
            exception (Exception): The exception to modify and raise.
        """
        raise EmulatorValidationError(str(exception)) from exception
