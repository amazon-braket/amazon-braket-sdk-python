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

import pytest
import sympy

from braket.parametric import (
    FreeParameter,
    FreeParameterExpression,
    arccos,
    arcsin,
    arctan,
    ceiling,
    cos,
    exp,
    floor,
    log,
    mod,
    sin,
    sqrt,
    tan,
)


@pytest.mark.parametrize(
    ("helper", "sympy_function", "extra_args", "expected"),
    [
        (sin, sympy.sin, (), "sin(alpha)"),
        (cos, sympy.cos, (), "cos(alpha)"),
        (tan, sympy.tan, (), "tan(alpha)"),
        (arcsin, sympy.asin, (), "arcsin(alpha)"),
        (arccos, sympy.acos, (), "arccos(alpha)"),
        (arctan, sympy.atan, (), "arctan(alpha)"),
        (exp, sympy.exp, (), "exp(alpha)"),
        (log, sympy.log, (), "log(alpha)"),
        (mod, sympy.Mod, (2,), "mod(alpha, 2)"),
        (ceiling, sympy.ceiling, (), "ceiling(alpha)"),
        (floor, sympy.floor, (), "floor(alpha)"),
    ],
)
def test_helper_constructs_expected_expression(helper, sympy_function, extra_args, expected):
    alpha = FreeParameter("alpha")
    expr = helper(alpha, *extra_args)
    expected_expr = FreeParameterExpression(sympy_function(alpha.expression, *extra_args))

    assert isinstance(expr, FreeParameterExpression)
    assert expr == expected_expr
    assert str(expr) == expected
    assert repr(expr) == expected


def test_sqrt_constructs_expected_expression():
    # SymPy represents sqrt as a Pow expression, so it is verified separately.
    alpha = FreeParameter("alpha")
    expr = sqrt(alpha)

    assert isinstance(expr, FreeParameterExpression)
    assert expr == FreeParameterExpression(sympy.sqrt(alpha.expression))
    assert str(expr) == "sqrt(alpha)"
    assert repr(expr) == "sqrt(alpha)"


@pytest.mark.parametrize(
    ("helper", "extra_args"),
    [
        (sin, ()),
        (cos, ()),
        (tan, ()),
        (arcsin, ()),
        (arccos, ()),
        (arctan, ()),
        (exp, ()),
        (log, ()),
        (sqrt, ()),
        (mod, (2,)),
        (ceiling, ()),
        (floor, ()),
    ],
)
def test_helper_expression_round_trip(helper, extra_args):
    alpha = FreeParameter("alpha")
    expr = helper(alpha / 2, *extra_args)
    rebuilt = FreeParameterExpression(expr.expression)

    assert rebuilt == expr
    assert str(rebuilt) == str(expr)


def test_helpers_accept_numeric_inputs():
    assert isinstance(sin(0), FreeParameterExpression)
    assert isinstance(sqrt(4), FreeParameterExpression)
    assert isinstance(mod(5, 2), FreeParameterExpression)


def test_sin_partial_and_full_substitution():
    alpha = FreeParameter("alpha")
    beta = FreeParameter("beta")
    expr = sin(alpha + beta)

    partial = expr.subs({"alpha": 0})
    assert isinstance(partial, FreeParameterExpression)
    assert str(partial) == "sin(beta)"

    assert expr.subs({"alpha": 0, "beta": 0}) == 0


@pytest.mark.parametrize(
    ("helper", "sympy_function", "bound"),
    [
        (sin, sympy.sin, 0),
        (cos, sympy.cos, 0),
        (tan, sympy.tan, 0),
        (arcsin, sympy.asin, 0),
        (arccos, sympy.acos, 0),
        (arctan, sympy.atan, 0),
        (exp, sympy.exp, 0),
        (log, sympy.log, 1),
        (sqrt, sympy.sqrt, 4),
        (ceiling, sympy.ceiling, 0),
        (floor, sympy.floor, 0),
    ],
)
def test_unary_helper_partial_and_full_substitution(helper, sympy_function, bound):
    alpha = FreeParameter("alpha")
    beta = FreeParameter("beta")
    expr = helper(alpha + beta)

    partial = expr.subs({"alpha": 0})
    assert isinstance(partial, FreeParameterExpression)
    assert partial == helper(beta)

    # A fully bound result may be a Python number, a SymPy number, or an exact
    # symbolic constant (e.g. arccos(0) -> pi/2), so compare through SymPy.
    full = expr.subs({"alpha": bound, "beta": 0})
    assert FreeParameterExpression(full) == FreeParameterExpression(
        sympy_function(sympy.Integer(bound))
    )


def test_mod_substitution():
    alpha = FreeParameter("alpha")
    beta = FreeParameter("beta")
    expr = mod(alpha + beta, 2)

    partial = expr.subs({"alpha": 0})
    assert isinstance(partial, FreeParameterExpression)
    assert str(partial) == "mod(beta, 2)"

    assert expr.subs({"alpha": 1, "beta": 2}) == 1


def test_mod_unwraps_second_operand():
    alpha = FreeParameter("alpha")
    beta = FreeParameter("beta")

    assert str(mod(alpha, beta)) == "mod(alpha, beta)"
