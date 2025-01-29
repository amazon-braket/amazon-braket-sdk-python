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

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ProgramType = TypeVar("ProgramType")


class BasePass(ABC, Generic[ProgramType]):
    @abstractmethod
    def run(self, program: ProgramType) -> ProgramType:
        """
        Runs a pass on the provided program.

        Args:
            program (ProgramType): The program to run the pass on.

        Returns:
            ProgramType: The program after the pass has been applied. Same type as the input
            program.

        Raises:
            NotImplementedError: Method not implemented.
        """
        raise NotImplementedError

    def __call__(self, program: ProgramType) -> ProgramType:
        return self.run(program)
