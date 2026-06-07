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

"""Module-level math helper functions for FreeParameterExpression.

These helpers mirror the mathematical functions available in OpenQASM 3,
allowing users to construct symbolic expressions without importing sympy
directly or touching internal ``.expression`` attributes.

Example::

    from braket.parametric import FreeParameter, sin, cos

    alpha = FreeParameter("alpha")
    expr = sin(alpha / 2) ** 2 + cos(alpha / 2) ** 2
"""

from __future__ import annotations

from numbers import Number

import sympy

from braket.parametric.free_parameter_expression import FreeParameterExpression


def _wrap(sympy_fn: type, arg: FreeParameterExpression | Number, *extra_args) -> FreeParameterExpression:
    """Wrap *arg* in *sympy_fn* and return a new :class:`FreeParameterExpression`.

    Args:
        sympy_fn: The SymPy function to apply.
        arg: The argument — either a :class:`FreeParameterExpression` or a plain number.
        *extra_args: Any additional arguments forwarded to *sympy_fn* (e.g. the modulus for mod).

    Returns:
        FreeParameterExpression: The wrapped expression.
    """
    inner = arg.expression if isinstance(arg, FreeParameterExpression) else arg
    return FreeParameterExpression(sympy_fn(inner, *extra_args))


def sin(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the sine of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``sin(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, sin
        >>> sin(FreeParameter("theta"))
        sin(theta)
    """
    return _wrap(sympy.sin, x)


def cos(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the cosine of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``cos(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, cos
        >>> cos(FreeParameter("theta"))
        cos(theta)
    """
    return _wrap(sympy.cos, x)


def tan(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the tangent of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``tan(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, tan
        >>> tan(FreeParameter("theta"))
        tan(theta)
    """
    return _wrap(sympy.tan, x)


def arcsin(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the arcsine of *x*.

    Serializes to ``arcsin(x)`` in OpenQASM 3 (not ``asin``).

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``arcsin(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, arcsin
        >>> arcsin(FreeParameter("theta"))
        arcsin(theta)
    """
    return _wrap(sympy.asin, x)


def arccos(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the arccosine of *x*.

    Serializes to ``arccos(x)`` in OpenQASM 3 (not ``acos``).

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``arccos(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, arccos
        >>> arccos(FreeParameter("theta"))
        arccos(theta)
    """
    return _wrap(sympy.acos, x)


def arctan(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the arctangent of *x*.

    Serializes to ``arctan(x)`` in OpenQASM 3 (not ``atan``).

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``arctan(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, arctan
        >>> arctan(FreeParameter("theta"))
        arctan(theta)
    """
    return _wrap(sympy.atan, x)


def exp(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the natural exponential of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``exp(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, exp
        >>> exp(FreeParameter("theta"))
        exp(theta)
    """
    return _wrap(sympy.exp, x)


def log(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the natural logarithm of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``log(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, log
        >>> log(FreeParameter("theta"))
        log(theta)
    """
    return _wrap(sympy.log, x)


def sqrt(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the square root of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``sqrt(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, sqrt
        >>> sqrt(FreeParameter("theta"))
        sqrt(theta)
    """
    return _wrap(sympy.sqrt, x)


def mod(x: FreeParameterExpression | Number, m: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return *x* modulo *m*.

    Args:
        x (FreeParameterExpression | Number): The dividend.
        m (FreeParameterExpression | Number): The modulus.

    Returns:
        FreeParameterExpression: ``mod(x, m)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, mod
        >>> mod(FreeParameter("theta"), 2)
        mod(theta, 2)
    """
    m_inner = m.expression if isinstance(m, FreeParameterExpression) else m
    return _wrap(sympy.Mod, x, m_inner)


def ceiling(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the ceiling of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``ceiling(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, ceiling
        >>> ceiling(FreeParameter("theta"))
        ceiling(theta)
    """
    return _wrap(sympy.ceiling, x)


def floor(x: FreeParameterExpression | Number) -> FreeParameterExpression:
    """Return the floor of *x*.

    Args:
        x (FreeParameterExpression | Number): The argument.

    Returns:
        FreeParameterExpression: ``floor(x)`` as a symbolic expression.

    Example::

        >>> from braket.parametric import FreeParameter, floor
        >>> floor(FreeParameter("theta"))
        floor(theta)
    """
    return _wrap(sympy.floor, x)
