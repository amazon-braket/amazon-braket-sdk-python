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

from braket.experimental.autoqasm import constants, errors, program, types
from braket.experimental.autoqasm.autograph.operators.variables import UndefinedReturnValue
from braket.experimental.autoqasm.types.conversions import var_type_from_oqpy


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

    program_conversion_context = program.get_program_conversion_context()
    is_target_name_used = program_conversion_context.is_var_name_used(target_name)
    is_value_name_used = isinstance(
        value, oqpy.base.Var
    ) and program_conversion_context.is_var_name_used(value.name)

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

        if program_conversion_context.subroutines_processing and isinstance(value, list):
            raise errors.UnsupportedSubroutineReturnType(
                "Subroutine returns an array or list, which is not allowed."
            )

        value = types.wrap_value(value)

    if not isinstance(value, oqpy.base.Var):
        return value

    if is_target_name_used:
        target = _get_oqpy_program_variable(target_name)
        _validate_assignment_types(target, value)
    else:
        target = copy.copy(value)
        target.init_expression = None
        target.name = target_name

    oqpy_program = program_conversion_context.get_oqpy_program()
    if is_value_name_used or value.init_expression is None:
        # Directly assign the value to the target.
        # For example:
        #   a = b;
        # where `b` is previously declared.
        oqpy_program.set(target, value)
    elif (
        target.name not in oqpy_program.declared_vars
        and program_conversion_context.at_function_root_scope
    ):
        # Explicitly declare and initialize the variable at the root scope.
        # For example:
        #   int[32] a = 10;
        # where `a` is at the root scope of the function (not inside any if/for/while block).
        target.init_expression = value.init_expression
        oqpy_program.declare(target)
    else:
        # Set to `value.init_expression` to avoid declaring an unnecessary variable.
        # The variable will be set in the current scope and auto-declared at the root scope.
        # For example, the `a = 1` and `a = 0` statements in the following:
        #   int[32] a;
        #   if (b == True) { a = 1; }
        #   else { a = 0; }
        # where `b` is previously declared.
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


def _validate_assignment_types(var1: oqpy.base.Var, var2: oqpy.base.Var) -> None:
    """Validates that the size and type of the variables are compatible for assignment.

    Args:
        var1 (oqpy.base.Var): Variable to validate.
        var2 (oqpy.base.Var): Variable to validate.
    """
    if var_type_from_oqpy(var1) != var_type_from_oqpy(var2):
        raise errors.InvalidAssignmentStatement(
            "Variables in assignment statements must have the same type"
        )

    if isinstance(var1, oqpy.ArrayVar):
        if var1.dimensions != var2.dimensions:
            raise errors.InvalidAssignmentStatement(
                "Arrays in assignment statements must have the same dimensions"
            )
    else:
        var1_size = var1.size or 1
        var2_size = var2.size or 1
        if var1_size != var2_size:
            raise errors.InvalidAssignmentStatement(
                "Variables in assignment statements must have the same size"
            )
