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
from typing import Generic, TypeVar

ProgramType = TypeVar("ProgramType")


class ValidationPass(ABC, Generic[ProgramType]):
    @abstractmethod
    def validate(self, program: ProgramType) -> None:
        """
        An emulator validator is used to perform some non-modifying validation
        pass on an input program. Implementations of validate should return
        nothing if the input program passes validation and raise an error otherwise.

        Args:
            program (ProgramType): The program to be evaluated against this criteria.
        """
        raise NotImplementedError

    def run(self, program: ProgramType) -> ProgramType:
        """
        Validate the input program and return the program, unmodified.

        Args:
            program (ProgramType): The program to validate.

        Returns:
            ProgramType: The unmodified progam passed in as input.
        """
        self.validate(program)
        return program
        
    def __call__(self, program: ProgramType) -> ProgramType:
        return self.run(program)
