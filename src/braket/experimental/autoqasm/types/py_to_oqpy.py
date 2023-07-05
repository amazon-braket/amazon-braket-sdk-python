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

"""Type conversions between Python and the internal oqpy representation for types."""

import ast as python_ast
import typing
from collections.abc import Iterable
from functools import singledispatch
from typing import Any, Union

import numpy as np
import openqasm3.ast as qasm_ast
import oqpy

from braket.experimental.autoqasm import program


def map_type(python_type: type) -> type:
    """Maps a given Python type to the corresponding oqpy type.

    Args:
        python_type (type): The Python type to be mapped.

    Returns:
        type: The corresponding oqpy type.
    """
    origin_type = typing.get_origin(python_type) or python_type
    type_args = typing.get_args(python_type)

    if issubclass(origin_type, bool):
        return oqpy.BoolVar
    if issubclass(origin_type, (int, np.integer)):
        return oqpy.IntVar
    if issubclass(origin_type, (float, np.floating)):
        return oqpy.FloatVar
    if issubclass(origin_type, list) and issubclass(type_args[0], (int, np.integer)):
        return oqpy.ArrayVar[oqpy.IntVar, 10]  # TODO don't use fixed length 10

    # TODO add all supported types
    return python_type


@singledispatch
def wrap_value(node: Any, **kwargs: dict) -> Any:
    """Wraps an object in an oqpy variable.

    Args:
        node (Any): The object to be wrapped.

    Raises:
        NotImplementedError: If logic for wrapping the given object
        type does not exist.

    Returns:
        Any: The oqpy variable wrapping the given object.
    """
    if node is None:
        return None

    # TODO add any missing cases
    raise NotImplementedError(node)


@wrap_value.register(bool)
def _(node: bool, **kwargs: dict):
    return oqpy.BoolVar(
        node, name=program.get_program_conversion_context().next_var_name(oqpy.BoolVar)
    )


@wrap_value.register(int)
@wrap_value.register(np.integer)
def _(node: Union[int, np.integer], **kwargs: dict):
    return oqpy.IntVar(
        node, name=program.get_program_conversion_context().next_var_name(oqpy.IntVar)
    )


@wrap_value.register(float)
@wrap_value.register(np.floating)
def _(node: Union[float, np.floating], **kwargs: dict):
    return oqpy.FloatVar(
        node, name=program.get_program_conversion_context().next_var_name(oqpy.FloatVar)
    )


@wrap_value.register
def _(node: Iterable, **kwargs: dict):
    # TODO: pass base_type to ArrayVar constructor
    return oqpy.ArrayVar(
        node,
        dimensions=list(np.shape(node)),
        name=program.get_program_conversion_context().next_var_name(oqpy.ArrayVar),
    )


@wrap_value.register
def _(node: oqpy.base.Var, **kwargs: dict):
    return node


@wrap_value.register
def _(node: oqpy.base.OQPyExpression, **kwargs: dict):
    return node


@wrap_value.register
def _(node: python_ast.Constant, **kwargs: dict):
    return node.value


@wrap_value.register
def _(node: python_ast.Name, **kwargs: dict):
    return oqpy.classical_types.Identifier(node.id)


@wrap_value.register
def _(node: python_ast.BinOp, **kwargs: dict):
    return wrap_value(node.op, left=node.left, right=node.right)


@wrap_value.register
def _(node: python_ast.Add, **kwargs: dict):
    left = kwargs["left"]
    right = kwargs["right"]
    return oqpy.base.OQPyBinaryExpression(
        getattr(qasm_ast.BinaryOperator, "+"),
        wrap_value(left),
        wrap_value(right),
    )


@wrap_value.register
def _(node: python_ast.Sub, **kwargs: dict):
    left = kwargs["left"]
    right = kwargs["right"]
    return oqpy.base.OQPyBinaryExpression(
        getattr(qasm_ast.BinaryOperator, "-"),
        wrap_value(left),
        wrap_value(right),
    )


@wrap_value.register
def _(node: python_ast.Call, **kwargs: dict):
    if node.func.id == "range":
        arg_values = [wrap_value(arg) for arg in node.args]
        return range(*arg_values)


@wrap_value.register
def _(node: python_ast.Compare, **kwargs: dict):
    if len(node.ops) > 1:
        raise NotImplementedError(node)
    op = node.ops[0]
    op_map = {
        python_ast.Eq: "==",
        python_ast.NotEq: "!=",
        python_ast.Lt: "<",
        python_ast.LtE: "<=",
        python_ast.Gt: ">",
        python_ast.GtE: ">=",
    }
    return oqpy.base.OQPyBinaryExpression(
        getattr(qasm_ast.BinaryOperator, op_map[type(op)]),
        wrap_value(node.left),
        wrap_value(node.comparators[0]),
    )
