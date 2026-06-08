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

# Shared by the parametrized tests below so the helper/SymPy pairing lives in one place.
HELPER_TO_SYMPY = {
    sin: sympy.sin,
    cos: sympy.cos,
    tan: sympy.tan,
    arcsin: sympy.asin,
    arccos: sympy.acos,
    arctan: sympy.atan,
    exp: sympy.exp,
    log: sympy.log,
    sqrt: sympy.sqrt,
    mod: sympy.Mod,
    ceiling: sympy.ceiling,
    floor: sympy.floor,
}


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
        (mod, (2,)),
        (ceiling, ()),
        (floor, ()),
    ],
)
def test_helper_constructs_expected_expression(helper, extra_args):
    alpha = FreeParameter("alpha")
    expr = helper(alpha, *extra_args)
    expected_expr = FreeParameterExpression(HELPER_TO_SYMPY[helper](alpha.expression, *extra_args))

    assert isinstance(expr, FreeParameterExpression)
    assert expr == expected_expr


def test_sqrt_constructs_expected_expression():
    # SymPy represents sqrt as a Pow expression, so it is verified separately.
    alpha = FreeParameter("alpha")
    expr = sqrt(alpha)

    assert isinstance(expr, FreeParameterExpression)
    assert expr == FreeParameterExpression(sympy.sqrt(alpha.expression))


def test_helpers_accept_numeric_inputs():
    assert isinstance(sin(0), FreeParameterExpression)
    assert isinstance(mod(5, 2), FreeParameterExpression)


@pytest.mark.parametrize(
    ("helper", "bound"),
    [
        (sin, 0),
        (cos, 0),
        (tan, 0),
        (arcsin, 0),
        (arccos, 0),
        (arctan, 0),
        (exp, 0),
        (log, 1),
        (sqrt, 4),
        (ceiling, 0),
        (floor, 0),
    ],
)
def test_unary_helper_partial_and_full_substitution(helper, bound):
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
        HELPER_TO_SYMPY[helper](sympy.Integer(bound))
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


def test_nested_helper_composition():
    alpha = FreeParameter("alpha")

    assert str(sin(cos(alpha))) == "sin(cos(alpha))"
    assert str(arcsin(sqrt(alpha))) == "arcsin(sqrt(alpha))"


def test_mixed_function_and_arithmetic_expression():
    alpha = FreeParameter("alpha")
    beta = FreeParameter("beta")
    gamma = FreeParameter("gamma")
    source = str(sin(alpha) + cos(beta) * sqrt(gamma))

    # SymPy may reorder commutative operands, so check substring containment.
    assert "sin(alpha)" in source
    assert "cos(beta)" in source
    assert "sqrt(gamma)" in source
