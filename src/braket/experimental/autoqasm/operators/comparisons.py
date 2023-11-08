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


"""Operators for comparison operators: <, <=, >, and >=."""

from typing import Any, Union

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm import types as aq_types

from .utils import _register_and_convert_parameters


def lt_(a: Any, b: Any) -> Union[bool, aq_types.BoolVar]:
    """Functional form of "<".

    Args:
        a (Any): Callable that returns the first expression.
        b (Any): Callable that returns the second expression.

    Returns:
        Union[bool, BoolVar]: Whether the first expression is less than the second.
    """
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _aq_lt(a, b)
    else:
        return a < b


def _aq_lt(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    result = aq_types.BoolVar()
    oqpy_program.declare(result)
    oqpy_program.set(result, a < b)
    return result


def lteq_(a: Any, b: Any) -> Union[bool, aq_types.BoolVar]:
    """Functional form of "<=".

    Args:
        a (Any): Callable that returns the first expression.
        b (Any): Callable that returns the second expression.

    Returns:
        Union[bool, BoolVar]: Whether the first expression is less than or equal to the second.
    """
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _aq_lteq(a, b)
    else:
        return a <= b


def _aq_lteq(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    result = aq_types.BoolVar()
    oqpy_program.declare(result)
    oqpy_program.set(result, a <= b)
    return result


def gt_(a: Any, b: Any) -> Union[bool, aq_types.BoolVar]:
    """Functional form of ">".

    Args:
        a (Any): Callable that returns the first expression.
        b (Any): Callable that returns the second expression.

    Returns:
        Union[bool, BoolVar]: Whether the first expression greater than the second.
    """
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _aq_gt(a, b)
    else:
        return a > b


def _aq_gt(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    result = aq_types.BoolVar()
    oqpy_program.declare(result)
    oqpy_program.set(result, a > b)
    return result


def gteq_(a: Any, b: Any) -> Union[bool, aq_types.BoolVar]:
    """Functional form of ">=".

    Args:
        a (Any): Callable that returns the first expression.
        b (Any): Callable that returns the second expression.

    Returns:
        Union[bool, BoolVar]: Whether the first expression greater than or equal to the second.
    """
    if aq_types.is_qasm_type(a) or aq_types.is_qasm_type(b):
        return _aq_gteq(a, b)
    else:
        return a >= b


def _aq_gteq(a: Any, b: Any) -> aq_types.BoolVar:
    a, b = _register_and_convert_parameters(a, b)

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    result = aq_types.BoolVar()
    oqpy_program.declare(result)
    oqpy_program.set(result, a >= b)
    return result
