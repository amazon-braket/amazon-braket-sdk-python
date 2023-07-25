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

from typing import Any, Callable, Optional

import oqpy.base

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm.types import is_qasm_type


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
    if is_qasm_type(cond):
        return _oqpy_if_exp(cond, if_true, if_false, expr_repr)
    else:
        return _py_if_exp(cond, if_true, if_false)


def _oqpy_if_exp(
    cond: Any,
    if_true: Callable[[None], Any],
    if_false: Callable[[None], Any],
    expr_repr: Optional[str],
) -> None:
    """Overload of if_exp that stages an oqpy conditional."""
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    if isinstance(cond, oqpy.base.Var) and cond.name not in oqpy_program.declared_vars.keys():
        oqpy_program.declare(cond)
    with oqpy.If(oqpy_program, cond):
        if_true()
    with oqpy.Else(oqpy_program):
        if_false()


def _py_if_exp(cond: Any, if_true: Callable[[None], Any], if_false: Callable[[None], Any]) -> Any:
    return if_true() if cond else if_false()
