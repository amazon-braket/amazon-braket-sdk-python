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

from braket.parametric import FreeParameter, FreeParameterExpression
from braket.parametric.free_parameter_expression import subs_if_free_parameter


@pytest.fixture
def free_parameter_expression():
    return FreeParameterExpression(FreeParameter("theta") - 1)


def test_is_free_param_expr(free_parameter_expression):
    assert isinstance(free_parameter_expression, FreeParameterExpression)


@pytest.mark.xfail(raises=NotImplementedError)
def test_constructor_bad_input():
    FreeParameterExpression(["test"])


def test_equality():
    expr_1 = FreeParameterExpression(FreeParameter("theta") + 1)
    expr_2 = FreeParameterExpression(FreeParameter("theta") + 1)
    other_expr = FreeParameterExpression(FreeParameter("theta"))
    non_expr = "non circuit"

    assert expr_1 == expr_2
    assert expr_1 is not expr_2
    assert expr_1 != other_expr
    assert expr_1 != non_expr


def test_equality_str():
    expr_1 = FreeParameterExpression("-theta+2*theta")
    expr_2 = FreeParameterExpression(-FreeParameter("theta") + 2 * FreeParameter("theta"))
    param_values = {"theta": 1}
    assert expr_1 == expr_2
    assert expr_1.subs(param_values) == expr_2.subs(param_values)
    assert hasattr(expr_1.expression, "free_symbols") and hasattr(expr_2.expression, "free_symbols")


@pytest.mark.xfail(raises=ValueError)
def test_unsupported_bin_op_str():
    FreeParameterExpression("theta/1")


@pytest.mark.xfail(raises=ValueError)
def test_unsupported_un_op_str():
    FreeParameterExpression("~theta")


@pytest.mark.xfail(raises=ValueError)
def test_unsupported_node_str():
    FreeParameterExpression("theta , 1")


def test_commutativity():
    add_1 = 1 + FreeParameterExpression(FreeParameter("theta"))
    add_2 = FreeParameterExpression(FreeParameter("theta")) + 1
    mul_1 = FreeParameterExpression(FreeParameter("theta") * 1)
    mul_2 = FreeParameterExpression(1 * FreeParameter("theta"))

    assert add_1 == add_2
    assert mul_1 == mul_2


def test_add():
    add_expr = FreeParameter("theta") + FreeParameter("theta")
    expected = FreeParameterExpression(2 * FreeParameter("theta"))
    assert add_expr == expected


def test_sub():
    sub_expr = FreeParameter("theta") - FreeParameter("alpha")
    expected = FreeParameterExpression(FreeParameter("theta")) - FreeParameterExpression(
        FreeParameter("alpha")
    )
    assert sub_expr == expected


def test_r_sub():
    r_sub_expr = 1 - FreeParameter("theta")
    expected = FreeParameterExpression(1 - FreeParameter("theta"))
    assert r_sub_expr == expected


def test_mul():
    mul_expr = FreeParameter("theta") * FreeParameter("alpha") * 2 * FreeParameter("theta")
    expected = FreeParameterExpression(FreeParameter("theta") ** 2 * FreeParameter("alpha") * 2)
    assert mul_expr == expected


def test_truediv():
    truediv_expr = FreeParameter("theta") / FreeParameter("alpha")
    expected = FreeParameterExpression(FreeParameter("theta")) / FreeParameterExpression(
        FreeParameter("alpha")
    )
    assert truediv_expr == expected


def test_r_truediv():
    r_truediv_expr = 1 / FreeParameter("theta")
    expected = FreeParameterExpression(1 / FreeParameter("theta"))
    assert r_truediv_expr == expected


def test_pow():
    mul_expr = FreeParameter("theta") ** FreeParameter("alpha") * 2
    expected = FreeParameterExpression(FreeParameter("theta") ** FreeParameter("alpha") * 2)
    assert mul_expr == expected


def test_pow_constant():
    mul_expr = FreeParameter("theta") ** 2
    expected = FreeParameterExpression(FreeParameter("theta") ** 2)
    assert mul_expr == expected


def test_r_pow():
    mul_expr = 2 ** FreeParameter("theta")
    expected = FreeParameterExpression(2 ** FreeParameter("theta"))
    assert mul_expr == expected


def test_neg():
    expr = FreeParameter("theta") * FreeParameter("alpha") * 2
    expected_expr = -FreeParameter("theta") * -FreeParameter("alpha") * -2
    assert -expr == expected_expr and -(-expr) == expr


def test_sub_string():
    theta = FreeParameter("theta")
    expr = theta + 1
    assert expr.subs({"theta": 1}) == 2


def test_sub_free_parameter():
    theta = FreeParameter("theta")
    expr = theta + 1
    param_values = {theta: 1}
    assert expr.subs(param_values) == 2


def test_sub_return_expression():
    expr = FreeParameter("theta") + 1 + FreeParameter("alpha")
    subbed_expr = expr.subs({"alpha": 1})
    expected = FreeParameter("theta") + 2

    assert subbed_expr == expected


@pytest.mark.parametrize(
    "param, kwargs, expected_value, expected_type",
    [
        (FreeParameter("a") + 2 * FreeParameter("d"), {"a": 0.1, "d": 0.3}, 0.7, float),
        (FreeParameter("x"), {"y": 1}, FreeParameter("x"), FreeParameter),
        (FreeParameter("y"), {"y": -0.1}, -0.1, float),
        (2 * FreeParameter("i"), {"i": 1}, 2.0, float),
        (
            FreeParameter("a") + 2 * FreeParameter("x"),
            {"a": 0.4, "b": 0.4},
            0.4 + 2 * FreeParameter("x"),
            FreeParameterExpression,
        ),
    ],
)
def test_subs_if_free_parameter(param, kwargs, expected_value, expected_type):
    value = subs_if_free_parameter(param, **kwargs)
    assert value == expected_value
    assert isinstance(value, expected_type)
