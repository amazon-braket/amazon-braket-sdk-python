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

from braket.circuits import FreeParameter, FreeParameterExpression


@pytest.fixture
def free_parameter_expression():
    return FreeParameterExpression(FreeParameter("theta") - 1)


def test_is_free_param_expr(free_parameter_expression):
    assert isinstance(free_parameter_expression, FreeParameterExpression)


@pytest.mark.xfail(raises=NotImplementedError)
def test_constructor_bad_input():
    FreeParameterExpression("theta")


def test_equality():
    expr_1 = FreeParameterExpression(FreeParameter("theta") + 1)
    expr_2 = FreeParameterExpression(FreeParameter("theta") + 1)
    other_expr = FreeParameterExpression(FreeParameter("theta"))
    non_expr = "non circuit"

    assert expr_1 == expr_2
    assert expr_1 is not expr_2
    assert expr_1 != other_expr
    assert expr_1 != non_expr


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
