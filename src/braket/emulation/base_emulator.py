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

from typing import Iterable, Union

from braket.passes import BasePass, ProgramType, ValidationPass


class BaseEmulator:
    def __init__(self, emulator_passes: Iterable[BasePass] = None):
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
        for emulator_pass in self._emulator_passes:
            if isinstance(emulator_pass, ValidationPass):
                emulator_pass(task_specification)

    def add_pass(self, emulator_pass: Union[Iterable[BasePass], BasePass]) -> BaseEmulator:
        """
        Append a new BasePass or a list of BasePass objects.

        Args:
            emulator_pass (Union[Iterable[BasePass], BasePass]): Either a
                single Pass object or a list of Pass objects that
                will be used in validation and program compilation passes by this
                emulator.

        Returns:
            BaseEmulator: Returns an updated self.

        Raises:
            TypeError: If the input is not an iterable or an Pass.

        """
        if isinstance(emulator_pass, Iterable):
            self._emulator_passes.extend(emulator_pass)
        elif isinstance(emulator_pass, BasePass):
            self._emulator_passes.append(emulator_pass)
        else:
            raise TypeError("emulator_pass must be an Pass or an iterable of Pass")
        return self
