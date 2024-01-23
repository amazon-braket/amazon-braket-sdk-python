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


"""Operations to override return statement behavior."""

from typing import Any

from braket.experimental.autoqasm import program, types


def return_output_from_main_(name: str, value: Any) -> Any:
    """TODO

    Args:
        name (str): The symbol name for the return variable.
        value (Any): The value of the returned variable.
    Returns:
        Any: Returns the same value that is being returned in the statement.
    """
    # if not aq_context.subroutines_processing:
    # if not isinstance(value, (tuple, list)):
    aq_context = program.get_program_conversion_context()
    aq_context.register_parameter(name, type(value), "output")
    return types.wrap_value(value)
