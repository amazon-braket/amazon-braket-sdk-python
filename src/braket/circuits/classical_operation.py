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

from typing import Optional, Any
from braket.circuits.operator import Operator

class ClassicalOperation(Operator):
    """A classical operation"""

    def __init__(self):
        self._qubit_count = 0
    
    @property
    def qubit_count(self) -> Optional[int]:
        """int: Returns number of qubits this quantum operator interacts with."""
        return self._qubit_count

    @property
    def name(self) -> str:
        """
        Returns the name of the quantum operator

        Returns:
            The name of the quantum operator as a string
        """
        return self.__class__.__name__

    def to_ir(self, *args, **kwargs) -> Any:
        """Returns IR representation of quantum operator

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        raise NotImplementedError("to_ir has not been implemented yet.")

    @classmethod
    def register_operation(cls, operation: "Operation"):
        """Register a gate implementation by adding it into the Gate class.

        Args:
            operation (Operation): Operation class to register.
        """
        setattr(cls, operation.__name__, operation)

    def __repr__(self):
        return f"{self.name}('qubit_count': {self.qubit_count})"
