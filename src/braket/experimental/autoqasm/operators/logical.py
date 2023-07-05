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

from typing import Any, Union

import oqpy.base

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm.types import is_qasm_type


def eq(a: Any, b: Any) -> Union[bool, oqpy.BoolVar]:
    """Functional form of "equal".

    Args:
        a (Any): First expression to compare.
        b (Any): Second expression to compare.

    Returns:
        Union[bool, BoolVar]: Whether the expressions are equal.
    """
    if is_qasm_type(a) or is_qasm_type(b):
        return _oqpy_eq(a, b)
    else:
        return _py_eq(a, b)


def _oqpy_eq(a: Any, b: Any) -> oqpy.BoolVar:
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    is_equal = oqpy.BoolVar(
        name=program.get_program_conversion_context().next_var_name(oqpy.BoolVar)
    )
    oqpy_program.declare(is_equal)
    oqpy_program.set(is_equal, a == b)
    return is_equal


def _py_eq(a: Any, b: Any) -> bool:
    return a == b
