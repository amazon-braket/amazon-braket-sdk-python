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


"""Operators for conditional expressions (e.g. the ternary if statement)."""

from collections.abc import Callable
from typing import Any, Optional

import oqpy.base

from braket.experimental.autoqasm import program as aq_program
from braket.experimental.autoqasm import types as aq_types
from braket.experimental.autoqasm.errors import UnsupportedConditionalExpressionError


def if_exp(
    cond: Any, if_true: Callable[[], Any], if_false: Callable[[], Any], expr_repr: Optional[str]
) -> Any:
    """Implements a conditional if expression.

    Args:
        cond (Any): The condition of the if clause.
        if_true (Callable[[], Any]): The function to run if the condition is true.
        if_false (Callable[[], Any]): The function to run if the condition is false.
        expr_repr (Optional[str]): The conditional expression represented as a string.

    Returns:
        Any: The value returned from the conditional expression.
    """
    if aq_types.is_qasm_type(cond):
        return _oqpy_if_exp(cond, if_true, if_false, expr_repr)
    else:
        return _py_if_exp(cond, if_true, if_false)


def _oqpy_if_exp(
    cond: Any,
    if_true: Callable[[None], Any],
    if_false: Callable[[None], Any],
    expr_repr: Optional[str],
) -> Optional[oqpy.base.Var]:
    """Overload of if_exp that stages an oqpy conditional."""
    result_var = None
    oqpy_program = aq_program.get_program_conversion_context().get_oqpy_program()
    with oqpy.If(oqpy_program, cond):
        true_result = aq_types.wrap_value(if_true())
        true_result_type = aq_types.var_type_from_oqpy(true_result)
        if true_result is not None:
            result_var = true_result_type()
            oqpy_program.set(result_var, true_result)
    with oqpy.Else(oqpy_program):
        false_result = aq_types.wrap_value(if_false())
        false_result_type = aq_types.var_type_from_oqpy(false_result)
        if false_result_type != true_result_type:
            raise UnsupportedConditionalExpressionError(true_result_type, false_result_type)
        if false_result is not None:
            oqpy_program.set(result_var, false_result)

    return result_var


def _py_if_exp(cond: Any, if_true: Callable[[None], Any], if_false: Callable[[None], Any]) -> Any:
    return if_true() if cond else if_false()
