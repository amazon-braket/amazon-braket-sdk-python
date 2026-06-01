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

import math

import pytest
import sympy

from braket.parametric import FreeParameter, FreeParameterExpression


@pytest.fixture
def theta():
    return FreeParameter("theta")


@pytest.fixture
def phi():
    return FreeParameter("phi")


def _to_float(value):
    """Convert a subs result (sympy numeric or FreeParameterExpression) to float."""
    if isinstance(value, FreeParameterExpression):
        return float(value.expression)
    return float(value)


class TestSin:
    def test_sin_free_parameter(self, theta):
        result = theta.sin()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.sin(theta.expression)

    def test_sin_expression(self, theta):
        expr = (theta + 1).sin()
        assert expr.expression == sympy.sin(theta.expression + 1)

    def test_sin_subs(self, theta):
        result = theta.sin().subs({"theta": 0})
        assert float(result) == 0.0

    def test_sin_subs_pi_over_2(self, theta):
        result = theta.sin().subs({"theta": math.pi / 2})
        assert abs(float(result) - 1.0) < 1e-10


class TestCos:
    def test_cos_free_parameter(self, theta):
        result = theta.cos()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.cos(theta.expression)

    def test_cos_expression(self, theta):
        expr = (theta + 1).cos()
        assert expr.expression == sympy.cos(theta.expression + 1)

    def test_cos_subs(self, theta):
        result = theta.cos().subs({"theta": 0})
        assert float(result) == 1.0


class TestTan:
    def test_tan_free_parameter(self, theta):
        result = theta.tan()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.tan(theta.expression)

    def test_tan_subs(self, theta):
        result = theta.tan().subs({"theta": 0})
        assert float(result) == 0.0

    def test_tan_subs_pi_over_4(self, theta):
        result = theta.tan().subs({"theta": math.pi / 4})
        assert abs(float(result) - 1.0) < 1e-10


class TestArcsin:
    def test_arcsin_free_parameter(self, theta):
        result = theta.arcsin()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.asin(theta.expression)

    def test_arcsin_subs(self, theta):
        result = theta.arcsin().subs({"theta": 0})
        assert float(result) == 0.0

    def test_arcsin_subs_one(self, theta):
        result = theta.arcsin().subs({"theta": 1})
        assert isinstance(result, FreeParameterExpression)
        assert abs(float(result.expression.evalf()) - math.pi / 2) < 1e-10


class TestArccos:
    def test_arccos_free_parameter(self, theta):
        result = theta.arccos()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.acos(theta.expression)

    def test_arccos_subs(self, theta):
        result = theta.arccos().subs({"theta": 1})
        assert float(result) == 0.0


class TestArctan:
    def test_arctan_free_parameter(self, theta):
        result = theta.arctan()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.atan(theta.expression)

    def test_arctan_subs(self, theta):
        result = theta.arctan().subs({"theta": 0})
        assert float(result) == 0.0

    def test_arctan_subs_one(self, theta):
        result = theta.arctan().subs({"theta": 1})
        assert isinstance(result, FreeParameterExpression)
        assert abs(float(result.expression.evalf()) - math.pi / 4) < 1e-10


class TestExp:
    def test_exp_free_parameter(self, theta):
        result = theta.exp()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.exp(theta.expression)

    def test_exp_subs(self, theta):
        result = theta.exp().subs({"theta": 0})
        assert float(result) == 1.0

    def test_exp_subs_one(self, theta):
        result = theta.exp().subs({"theta": 1})
        assert isinstance(result, FreeParameterExpression)
        assert abs(float(result.expression.evalf()) - math.e) < 1e-10


class TestLog:
    def test_log_free_parameter(self, theta):
        result = theta.log()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.log(theta.expression)

    def test_log_subs(self, theta):
        result = theta.log().subs({"theta": 1})
        assert float(result) == 0.0

    def test_log_subs_e(self, theta):
        result = theta.log().subs({"theta": math.e})
        assert abs(float(result) - 1.0) < 1e-10


class TestSqrt:
    def test_sqrt_free_parameter(self, theta):
        result = theta.sqrt()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.sqrt(theta.expression)

    def test_sqrt_subs(self, theta):
        result = theta.sqrt().subs({"theta": 4})
        assert float(result) == 2.0

    def test_sqrt_subs_zero(self, theta):
        result = theta.sqrt().subs({"theta": 0})
        assert float(result) == 0.0


class TestMod:
    def test_mod_free_parameter(self, theta):
        result = theta.mod(3)
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.Mod(theta.expression, 3)

    def test_mod_free_parameter_expression(self, theta, phi):
        result = theta.mod(phi)
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.Mod(theta.expression, phi.expression)

    def test_mod_subs(self, theta):
        result = theta.mod(3).subs({"theta": 7})
        assert result == 1

    def test_mod_subs_zero(self, theta):
        result = theta.mod(2).subs({"theta": 4})
        assert result == 0


class TestCeiling:
    def test_ceiling_free_parameter(self, theta):
        result = theta.ceiling()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.ceiling(theta.expression)

    def test_ceiling_subs(self, theta):
        result = theta.ceiling().subs({"theta": 3.2})
        assert result == 4

    def test_ceiling_subs_integer(self, theta):
        result = theta.ceiling().subs({"theta": 5})
        assert result == 5


class TestFloor:
    def test_floor_free_parameter(self, theta):
        result = theta.floor()
        assert isinstance(result, FreeParameterExpression)
        assert result.expression == sympy.floor(theta.expression)

    def test_floor_subs(self, theta):
        result = theta.floor().subs({"theta": 3.2})
        assert result == 3

    def test_floor_subs_integer(self, theta):
        result = theta.floor().subs({"theta": 5})
        assert result == 5


class TestComposition:
    def test_sin_cos(self, theta):
        """Test chaining math functions."""
        result = theta.sin().cos()
        assert result.expression == sympy.cos(sympy.sin(theta.expression))

    def test_exp_sin(self, theta):
        result = theta.sin().exp()
        assert result.expression == sympy.exp(sympy.sin(theta.expression))

    def test_complex_expression(self, theta, phi):
        """Test math functions on complex expressions."""
        expr = (theta + phi * 2).sin()
        assert expr.expression == sympy.sin(theta.expression + phi.expression * 2)

    def test_nested_with_arithmetic(self, theta):
        """Test mixing math functions with arithmetic."""
        expr = theta.sin() + 1
        assert expr.expression == sympy.sin(theta.expression) + 1

    def test_subs_after_chaining(self, theta):
        result = theta.sin().cos().subs({"theta": 0})
        expr = result.expression if isinstance(result, FreeParameterExpression) else result
        assert abs(float(expr.evalf()) - math.cos(math.sin(0))) < 1e-10

    def test_sqrt_exp(self, theta):
        result = theta.exp().sqrt()
        assert result.expression == sympy.sqrt(sympy.exp(theta.expression))

    def test_log_exp(self, theta):
        result = theta.exp().log()
        assert result.expression == sympy.log(sympy.exp(theta.expression))


class TestOQASMFunctionMap:
    def test_oqasm_function_map_import(self):
        from braket.parametric.free_parameter_expression import OQASM_FUNCTION_MAP

        assert sympy.sin in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.sin] == "sin"
        assert sympy.cos in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.cos] == "cos"
        assert sympy.tan in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.tan] == "tan"
        assert sympy.asin in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.asin] == "arcsin"
        assert sympy.acos in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.acos] == "arccos"
        assert sympy.atan in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.atan] == "arctan"
        assert sympy.exp in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.exp] == "exp"
        assert sympy.log in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.log] == "log"
        assert sympy.sqrt in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.sqrt] == "sqrt"
        assert sympy.ceiling in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.ceiling] == "ceiling"
        assert sympy.floor in OQASM_FUNCTION_MAP
        assert OQASM_FUNCTION_MAP[sympy.floor] == "floor"


class TestRepr:
    def test_sin_repr(self, theta):
        expr = theta.sin()
        assert "sin" in repr(expr).lower() or "sin" in repr(expr.expression).lower()

    def test_exp_repr(self, theta):
        expr = theta.exp()
        assert "exp" in repr(expr).lower() or "exp" in repr(expr.expression).lower()
