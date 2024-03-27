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


"""Operators for exception handling."""

from collections.abc import Callable

from braket.experimental.autoqasm.types import is_qasm_type


def assert_stmt(test: bool, message: Callable) -> None:
    """An assertion statement.

    Args:
        test (bool): The condition on which to assert.
        message (Callable): A function which returns the message to be used
            if the assertion fails.
    """
    if is_qasm_type(test):
        raise NotImplementedError(
            "Assertions are not supported for values that depend on "
            "measurement results or AutoQASM variables."
        )

    assert test, message()
