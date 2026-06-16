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

"""Math helper functions for free parameter expressions.

These helpers let you build symbolic OpenQASM math expressions without importing
SymPy or touching the internal expression attribute.

Examples:
    >>> from braket.circuits import Circuit
    >>> from braket.parametric import FreeParameter, arcsin
    >>> alpha = FreeParameter("alpha")
    >>> circuit = Circuit().rx(0, arcsin(alpha))
    >>> source = circuit.to_ir("OPENQASM").source
    >>> "rx(arcsin(alpha)) q[0];" in source
    True
"""

from __future__ import annotations

from collections.abc import Callable
from numbers import Number

import sympy

from braket.parametric.free_parameter_expression import FreeParameterExpression


def _expression(value: FreeParameterExpression | Number) -> Number | sympy.Expr:
    return value.expression if isinstance(value, FreeParameterExpression) else value


def _wrap(
    function: Callable[..., Number | sympy.Expr],
    *args: FreeParameterExpression | Number,
) -> FreeParameterExpression:
    sympy_args = [_expression(arg) for arg in args]
    return FreeParameterExpression(function(*sympy_args))


def sin(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the sine of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic sine expression.
    """
    return _wrap(sympy.sin, x)


def cos(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the cosine of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic cosine expression.
    """
    return _wrap(sympy.cos, x)


def tan(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the tangent of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic tangent expression.
    """
    return _wrap(sympy.tan, x)


def arcsin(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the arcsine (inverse sine) of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic arcsine expression.
    """
    return _wrap(sympy.asin, x)


def arccos(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the arccosine (inverse cosine) of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic arccosine expression.
    """
    return _wrap(sympy.acos, x)


def arctan(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the arctangent (inverse tangent) of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic arctangent expression.
    """
    return _wrap(sympy.atan, x)


def exp(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the exponential of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic exponential expression.
    """
    return _wrap(sympy.exp, x)


def log(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the natural logarithm of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic natural logarithm expression.
    """
    return _wrap(sympy.log, x)


def sqrt(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the square root of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic square root expression.
    """
    return _wrap(sympy.sqrt, x)


def mod(
    x: FreeParameterExpression | Number,
    m: FreeParameterExpression | Number,
) -> FreeParameterExpression:
    """Returns the remainder of a free parameter expression divided by ``m``.

    Args:
        x (FreeParameterExpression | Number): The dividend expression.
        m (FreeParameterExpression | Number): The divisor expression.

    Returns:
        FreeParameterExpression: The symbolic modulo expression.
    """
    return _wrap(sympy.Mod, x, m)


def ceiling(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the ceiling of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic ceiling expression.
    """
    return _wrap(sympy.ceiling, x)


def floor(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Returns the floor of a free parameter expression.

    Args:
        x (FreeParameterExpression | Number): The expression.

    Returns:
        FreeParameterExpression: The symbolic floor expression.
    """
    return _wrap(sympy.floor, x)
