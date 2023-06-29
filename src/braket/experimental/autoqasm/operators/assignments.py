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

    if target_name == constants.RETVAL_VARIABLE_NAME:
        return types.wrap_value(value)

    if isinstance(value, oqpy.base.Var):
        # TODO: If name is defined in value, it might be different from target_name.
        #       We should probably validate that.
        oqpy_program = program.get_program_conversion_context().get_oqpy_program()

        is_target_name_used = _is_variable_used(target_name)
        is_value_used = _is_variable_used(value.name)

        if is_target_name_used:
            target = _get_oqpy_program_variable(target_name)
            _validate_variables_type_size(target, value)
            if is_value_used:
                oqpy_program.set(target, value)
            else:
                # Set to `value.init_expression` to avoid declaring an unnecessary variable.
                oqpy_program.set(target, value.init_expression)
        else:
            target = type(value)(name=target_name, size=value.size)

            if is_value_used:
                oqpy_program.declare(target)
                oqpy_program.set(target, value)
            else:
                # Set to `value.init_expression` to avoid declaring an unnecessary variable.
                target.init_expression = value.init_expression
                oqpy_program.declare(target)

        return target

    return value


def _is_variable_used(var_name: str) -> bool:
    """Check if the variable already exists in the oqpy program.

    Args:
        var_name (str): variable name

    Returns:
        bool: Return True if the variable already exists
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    return (
        var_name in oqpy_program.declared_vars.keys()
        or var_name in oqpy_program.undeclared_vars.keys()
    )


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
