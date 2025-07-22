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

from collections.abc import Iterable
from typing import Optional

from braket.circuits import Circuit
from braket.passes import ValidationPass


class ResultTypeValidator(ValidationPass[Circuit]):
    def __init__(self, supported_result_types: Optional[Iterable[str]] = None):
        """
        Args:
            supported_result_types (Optional[Iterable[str]]): A list of result types supported
                by the emulator. A result type is a Braket result type name.

        Raises:
            ValueError: If supported_result_types is empty or None.
        """
        if not supported_result_types:
            raise ValueError("Supported result types must be provided.")

        self._supported_result_types = frozenset(supported_result_types)

    def validate(self, program: Circuit) -> None:
        """
        Checks that all result types used in the circuit are in this validator's
        supported result types set.

        Args:
            program (Circuit): The Braket circuit whose result types to validate.

        Raises:
            ValueError: If a result type is not in this validator's supported result types set.
        """
        for result_type in program.result_types:
            if result_type.name not in self._supported_result_types:
                raise ValueError(
                    f"Result type {result_type.name} is not a supported result type "
                    f"for this device."
                )

    def __eq__(self, other: ValidationPass) -> bool:
        return (
            isinstance(other, ResultTypeValidator)
            and self._supported_result_types == other._supported_result_types
        )
