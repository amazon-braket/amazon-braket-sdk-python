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

"""Abstract base classes for AutoQASM objects."""


from abc import ABC, abstractmethod

from braket.circuits.serialization import IRType


class AutoQasmProgram(ABC):
    @abstractmethod
    def to_ir(
        self,
        ir_type: IRType = IRType.OPENQASM,
    ) -> str:
        """Serializes the program into an intermediate representation.

        Args:
            ir_type (IRType): The IRType to use for converting the program to its
                IR representation. Defaults to IRType.OPENQASM.

        Raises:
            ValueError: If the supplied `ir_type` is not supported.

        Returns:
            str: A representation of the program in the `ir_type` format.
        """
