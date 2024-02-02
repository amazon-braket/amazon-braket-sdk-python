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

"""Type conversions between Python and the autoqasm representation for types."""

import typing
from functools import singledispatch
from typing import Any, Union

import numpy as np
import oqpy
from openpulse import ast

from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.experimental.autoqasm import errors, program
from braket.experimental.autoqasm import types as aq_types


def map_parameter_type(python_type: type) -> type:
    """Maps a given Python function parameter type to the corresponding oqpy
    subroutine parameter type.

    Args:
        python_type (type): The Python type to be mapped.

    Returns:
        type: The corresponding oqpy type.
    """
    origin_type = typing.get_origin(python_type) or python_type

    if issubclass(origin_type, bool):
        return oqpy.BoolVar
    if issubclass(origin_type, (int, np.integer)):
        return oqpy.IntVar
    if issubclass(origin_type, (float, np.floating)):
        return oqpy.FloatVar
    if issubclass(origin_type, tuple) or issubclass(origin_type, list):
        raise errors.ParameterTypeError(
            "Lists and tuples are not supported as parameters to AutoQASM functions; "
            "consider passing the values as multiple separate parameters."
        )

    return python_type


def var_type_from_ast_type(ast_type: ast.ClassicalType) -> type:
    """Converts an OpenQASM AST type to the corresponding AutoQASM variable type.

    Args:
        ast_type (ast.ClassicalType): The OpenQASM AST type to be converted.

    Returns:
        type: The corresponding AutoQASM variable type.
    """
    if isinstance(ast_type, ast.IntType):
        return aq_types.IntVar
    if isinstance(ast_type, ast.FloatType):
        return aq_types.FloatVar
    if isinstance(ast_type, ast.BoolType):
        return aq_types.BoolVar
    if isinstance(ast_type, ast.BitType):
        return aq_types.BitVar
    if isinstance(ast_type, ast.ArrayType):
        return aq_types.ArrayVar

    raise NotImplementedError


def var_type_from_oqpy(expr_or_var: Union[oqpy.base.OQPyExpression, oqpy.base.Var]) -> type:
    """Returns the AutoQASM variable type corresponding to the provided OQPy object.

    Args:
        expr_or_var (Union[OQPyExpression, Var]): An OQPy expression or variable.

    Returns:
        type: The corresponding AutoQASM variable type.
    """
    if isinstance(expr_or_var, oqpy.base.OQPyExpression):
        return var_type_from_ast_type(expr_or_var.type)
    return type(expr_or_var)


@singledispatch
def wrap_value(node: Any) -> Any:
    """Wraps an object in an autoqasm variable.

    Args:
        node (Any): The object to be wrapped.

    Raises:
        NotImplementedError: If logic for wrapping the given object
        type does not exist.

    Returns:
        Any: The autoqasm variable wrapping the given object.
    """
    if node is None:
        return None

    # TODO add any missing cases
    raise NotImplementedError(node)


@wrap_value.register(bool)
def _(node: bool):
    return aq_types.BoolVar(node)


@wrap_value.register(int)
@wrap_value.register(np.integer)
def _(node: Union[int, np.integer]):
    return aq_types.IntVar(node)


@wrap_value.register(float)
@wrap_value.register(np.floating)
def _(node: Union[float, np.floating]):
    return aq_types.FloatVar(node)


@wrap_value.register(FreeParameterExpression)
def _(node: FreeParameterExpression):
    aq_context = program.get_program_conversion_context()
    existing_param = aq_context.get_free_parameter(node.name)
    if existing_param is not None:
        return existing_param
    else:
        return aq_types.FloatVar(node.name)


@wrap_value.register
def _(node: oqpy.base.Var):
    return node


@wrap_value.register
def _(node: oqpy.base.OQPyExpression):
    return node
