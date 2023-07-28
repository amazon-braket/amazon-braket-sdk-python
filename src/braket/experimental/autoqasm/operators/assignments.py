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


"""Operators for assignment statements."""

import copy
from typing import Any

import oqpy
import oqpy.base

from braket.experimental.autoqasm import constants, program, types
from braket.experimental.autoqasm.autograph.operators.variables import UndefinedReturnValue


def assign_stmt(target_name: str, value: Any) -> Any:
    """Operator declares the `oq` variable, or sets variable's value if it's
    already declared.

    Args:
        target_name (str): The name of assignment target. It is the variable
            name on the lhs of an assignment statement.
        value (Any): The value of assignment. It is the object on the rhs of
            an assignment statement.

    Returns:
        Any: Assignment value with updated name attribute if the value is an
        `oqpy` type. Otherwise, it returns unchanged assignment value.
    """
    # TODO: The logic branch for return value and measurement should be handled
    # in different converters.
    if isinstance(value, UndefinedReturnValue):
        return value

    is_target_name_used = program.get_program_conversion_context().is_var_name_used(target_name)
    is_value_name_used = isinstance(
        value, oqpy.base.Var
    ) and program.get_program_conversion_context().is_var_name_used(value.name)

    if target_name == constants.RETVAL_VARIABLE_NAME:
        # AutoGraph transpiles return statements like
        #    return <return_value>
        # into
        #    retval_ = <return_value>
        #    return retval_
        # The special logic here is to handle this case properly and avoid
        # declaring a new variable unless it is necessary.

        if is_value_name_used:
            # This is a value which already exists as a variable in the program.
            # Return it directly without wrapping it or declaring a new variable.
            return value

        value = types.wrap_value(value)

    if not isinstance(value, oqpy.base.Var):
        return value

    if is_target_name_used:
        target = _get_oqpy_program_variable(target_name)
        _validate_variables_type_size(target, value)
    else:
        target = copy.copy(value)
        target.init_expression = None
        target.name = target_name

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    if is_value_name_used or value.init_expression is None:
        oqpy_program.set(target, value)
    else:
        # Set to `value.init_expression` to avoid declaring an unnecessary variable.
        oqpy_program.set(target, value.init_expression)

    return target


def _get_oqpy_program_variable(var_name: str) -> oqpy.base.Var:
    """Return oqpy variable of the specified name used in the oqpy program.

    Args:
        var_name (str): Name of the variable

    Returns:
        oqpy.base.Var: Variable with the specified name in the oqpy program.
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    variables = {**oqpy_program.declared_vars, **oqpy_program.undeclared_vars}
    return variables[var_name]


def _validate_variables_type_size(var1: oqpy.base.Var, var2: oqpy.base.Var) -> None:
    """Raise error when the size or type of the two variables do not match.

    Args:
        var1 (oqpy.base.Var): Variable to validate.
        var2 (oqpy.base.Var): Variable to validate.
    """
    var1_size = var1.size or 1
    var2_size = var2.size or 1

    if type(var1) != type(var2):
        raise ValueError("Variables in assignment statements must have the same type")
    if var1_size != var2_size:
        raise ValueError("Variables in assignment statements must have the same size")
