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

from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.experimental.autoqasm import program
from braket.experimental.autoqasm import types as aq_types


def return_output_from_main(name: str, value: Any) -> Any:
    """Registers an output variable in the program with the given name that matches the type
    of the value. The value is assigned to the output variable.

    Args:
        name (str): The symbol name for the return variable.
        value (Any): The value of the returned variable.
    Returns:
        Any: Returns the same value that is being returned in the statement.
    """
    aq_context = program.get_program_conversion_context()
    input = aq_context.get_input_parameter(name)

    if input is None:
        if isinstance(value, FreeParameterExpression):
            aq_context.register_output_parameter(name, aq_types.FloatVar)
        else:
            aq_context.register_output_parameter(name, type(value))
    else:
        # Handle name collisions with input variables
        name = name + "_"
        value_type = type(input)
        aq_context.register_output_parameter(name, value_type)
        # Add `val_ = val;` at the end of the program to equate these parameters
        oqpy_program = aq_context.get_oqpy_program()
        output = aq_context.get_output_parameter(name)
        oqpy_program.set(output, input)

    return aq_types.wrap_value(value)
