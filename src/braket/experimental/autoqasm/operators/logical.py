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


"""Operators for logical boolean operators (e.g. not, and, or)."""

from typing import Any, Callable, Union

import oqpy.base
from openpulse import ast

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm import types as aq_types

from .utils import _register_and_convert_parameters


def and_(a: Callable[[], Any], b: Callable[[], Any]) -> Union[bool, aq_types.BoolVar]:
    """Functional form of "and".

    Args:
        a (Callable[[], Any]): Callable that returns the first expression.
        b (Callable[[], Any]): Callable that returns the second expression.

    Returns:
        Union[bool, BoolVar]: Whether both expressions are true.
    """
    a = a()
    b = b()
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _oqpy_and(a, b)
    else:
        return _py_and(a, b)


def _oqpy_and(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    result = aq_types.BoolVar()
    oqpy_program.declare(result)
    oqpy_program.set(result, oqpy.base.logical_and(a, b))
    return result


def _py_and(a: Any, b: Any) -> bool:
    return a and b


def or_(a: Callable[[], Any], b: Callable[[], Any]) -> Union[bool, aq_types.BoolVar]:
    """Functional form of "or".

    Args:
        a (Callable[[], Any]): Callable that returns the first expression.
        b (Callable[[], Any]): Callable that returns the second expression.

    Returns:
        Union[bool, BoolVar]: Whether either expression is true.
    """
    a = a()
    b = b()
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _oqpy_or(a, b)
    else:
        return _py_or(a, b)


def _oqpy_or(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    result = aq_types.BoolVar()
    oqpy_program.declare(result)
    oqpy_program.set(result, oqpy.base.logical_or(a, b))
    return result


def _py_or(a: Any, b: Any) -> bool:
    return a or b


def not_(a: Any) -> Union[bool, aq_types.BoolVar]:
    """Functional form of "not".

    Args:
        a (Any): Expression to negate.

    Returns:
        Union[bool, BoolVar]: Whether the expression is false.
    """
    if aq_types.is_qasm_type(a):
        return _oqpy_not(a)
    else:
        return _py_not(a)


def _oqpy_not(a: Any) -> aq_types.BoolVar:
    a = _register_and_convert_parameters(a)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    result = aq_types.BoolVar()
    oqpy_program.declare(result)
    oqpy_program.set(result, oqpy.base.OQPyUnaryExpression(ast.UnaryOperator["!"], a))
    return result


def _py_not(a: Any) -> bool:
    return not a


def eq(a: Any, b: Any) -> Union[bool, aq_types.BoolVar]:
    """Functional form of "equal".

    Args:
        a (Any): First expression to compare.
        b (Any): Second expression to compare.

    Returns:
        Union[bool, BoolVar]: Whether the expressions are equal.
    """
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _oqpy_eq(a, b)
    else:
        return _py_eq(a, b)


def _oqpy_eq(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    is_equal = aq_types.BoolVar()
    oqpy_program.declare(is_equal)
    oqpy_program.set(is_equal, a == b)
    return is_equal


def _py_eq(a: Any, b: Any) -> bool:
    return a == b


def not_eq(a: Any, b: Any) -> Union[bool, aq_types.BoolVar]:
    """Functional form of "not equal".

    Args:
        a (Any): First expression to compare.
        b (Any): Second expression to compare.

    Returns:
        Union[bool, BoolVar]: Whether the expressions are not equal.
    """
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _oqpy_not_eq(a, b)
    else:
        return _py_not_eq(a, b)


def _oqpy_not_eq(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    is_not_equal = aq_types.BoolVar()
    oqpy_program.declare(is_not_equal)
    oqpy_program.set(is_not_equal, a != b)
    return is_not_equal


def _py_not_eq(a: Any, b: Any) -> bool:
    return a != b
