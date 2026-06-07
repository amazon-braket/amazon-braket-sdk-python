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
from braket.parametric.free_parameter_expression import _OpenQASMPrinter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sym(name: str) -> sympy.Symbol:
    return sympy.Symbol(name)


def _fp(name: str) -> FreeParameter:
    return FreeParameter(name)


# ---------------------------------------------------------------------------
# _OpenQASMPrinter
# ---------------------------------------------------------------------------

class TestOpenQASMPrinter:
    printer = _OpenQASMPrinter()

    def test_sin(self):
        assert self.printer.doprint(sympy.sin(_sym("x"))) == "sin(x)"

    def test_cos(self):
        assert self.printer.doprint(sympy.cos(_sym("x"))) == "cos(x)"

    def test_tan(self):
        assert self.printer.doprint(sympy.tan(_sym("x"))) == "tan(x)"

    def test_asin_maps_to_arcsin(self):
        assert self.printer.doprint(sympy.asin(_sym("x"))) == "arcsin(x)"

    def test_acos_maps_to_arccos(self):
        assert self.printer.doprint(sympy.acos(_sym("x"))) == "arccos(x)"

    def test_atan_maps_to_arctan(self):
        assert self.printer.doprint(sympy.atan(_sym("x"))) == "arctan(x)"

    def test_exp(self):
        assert self.printer.doprint(sympy.exp(_sym("x"))) == "exp(x)"

    def test_log(self):
        assert self.printer.doprint(sympy.log(_sym("x"))) == "log(x)"

    def test_sqrt(self):
        assert self.printer.doprint(sympy.sqrt(_sym("x"))) == "sqrt(x)"

    def test_mod(self):
        assert self.printer.doprint(sympy.Mod(_sym("x"), 2)) == "mod(x, 2)"

    def test_ceiling(self):
        assert self.printer.doprint(sympy.ceiling(_sym("x"))) == "ceiling(x)"

    def test_floor(self):
        assert self.printer.doprint(sympy.floor(_sym("x"))) == "floor(x)"

    def test_abs_raises(self):
        with pytest.raises(ValueError, match="Abs has no OpenQASM 3 equivalent"):
            self.printer.doprint(sympy.Abs(_sym("x")))

    def test_plain_symbol(self):
        assert self.printer.doprint(_sym("alpha")) == "alpha"

    def test_arithmetic_expression(self):
        x = _sym("x")
        assert self.printer.doprint(x + 1) == "x + 1"


# ---------------------------------------------------------------------------
# FreeParameterExpression __str__ / __repr__
# ---------------------------------------------------------------------------

class TestFreeParameterExpressionStr:
    def test_str_plain_symbol(self):
        assert str(FreeParameterExpression(_fp("theta"))) == "theta"

    def test_str_arcsin(self):
        expr = FreeParameterExpression(sympy.asin(_sym("theta")))
        assert str(expr) == "arcsin(theta)"

    def test_str_arccos(self):
        expr = FreeParameterExpression(sympy.acos(_sym("theta")))
        assert str(expr) == "arccos(theta)"

    def test_str_arctan(self):
        expr = FreeParameterExpression(sympy.atan(_sym("theta")))
        assert str(expr) == "arctan(theta)"

    def test_repr_arcsin(self):
        expr = FreeParameterExpression(sympy.asin(_sym("theta")))
        assert repr(expr) == "arcsin(theta)"

    def test_str_unsupported_raises(self):
        expr = FreeParameterExpression(sympy.Abs(_sym("theta")))
        with pytest.raises(ValueError, match="Abs has no OpenQASM 3 equivalent"):
            str(expr)


# ---------------------------------------------------------------------------
# String parser with function calls
# ---------------------------------------------------------------------------

class TestStringParserFunctions:
    def test_sin_from_string(self):
        expr = FreeParameterExpression("sin(alpha)")
        assert expr == sin(_fp("alpha"))

    def test_cos_from_string(self):
        expr = FreeParameterExpression("cos(alpha)")
        assert expr == cos(_fp("alpha"))

    def test_arcsin_from_string(self):
        expr = FreeParameterExpression("arcsin(alpha)")
        assert expr == arcsin(_fp("alpha"))

    def test_asin_alias_from_string(self):
        expr = FreeParameterExpression("asin(alpha)")
        assert expr == arcsin(_fp("alpha"))

    def test_sqrt_from_string(self):
        expr = FreeParameterExpression("sqrt(alpha)")
        assert expr == sqrt(_fp("alpha"))

    def test_compound_from_string(self):
        expr = FreeParameterExpression("sin(alpha) + cos(alpha)")
        expected = sin(_fp("alpha")) + cos(_fp("alpha"))
        assert expr == expected

    def test_unknown_function_raises(self):
        with pytest.raises(ValueError, match="Unsupported function"):
            FreeParameterExpression("unknown_fn(alpha)")


# ---------------------------------------------------------------------------
# Helper functions — construction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn,sympy_fn", [
    (sin,    sympy.sin),
    (cos,    sympy.cos),
    (tan,    sympy.tan),
    (arcsin, sympy.asin),
    (arccos, sympy.acos),
    (arctan, sympy.atan),
    (exp,    sympy.exp),
    (log,    sympy.log),
    (sqrt,   sympy.sqrt),
    (ceiling, sympy.ceiling),
    (floor,  sympy.floor),
])
class TestUnaryHelpers:
    def test_from_free_parameter(self, fn, sympy_fn):
        x = _fp("x")
        result = fn(x)
        assert isinstance(result, FreeParameterExpression)
        expected = FreeParameterExpression(sympy_fn(_sym("x")))
        assert result == expected

    def test_from_number(self, fn, sympy_fn):
        result = fn(1)
        assert isinstance(result, FreeParameterExpression)

    def test_from_expression(self, fn, sympy_fn):
        expr = _fp("x") * 2
        result = fn(expr)
        assert isinstance(result, FreeParameterExpression)


# ---------------------------------------------------------------------------
# mod — two-argument helper
# ---------------------------------------------------------------------------

class TestMod:
    def test_mod_fp_number(self):
        x = _fp("x")
        result = mod(x, 2)
        expected = FreeParameterExpression(sympy.Mod(_sym("x"), 2))
        assert result == expected

    def test_mod_two_fp(self):
        x = _fp("x")
        m = _fp("m")
        result = mod(x, m)
        expected = FreeParameterExpression(sympy.Mod(_sym("x"), _sym("m")))
        assert result == expected

    def test_mod_str(self):
        assert str(mod(_fp("x"), 2)) == "mod(x, 2)"


# ---------------------------------------------------------------------------
# Substitution
# ---------------------------------------------------------------------------

class TestSubstitution:
    def test_sin_fully_bound(self):
        expr = sin(_fp("theta"))
        result = expr.subs({"theta": math.pi / 2})
        assert abs(float(result) - 1.0) < 1e-9

    def test_sin_partially_bound(self):
        expr = sin(_fp("alpha")) + _fp("beta")
        result = expr.subs({"alpha": 0.0})
        # sin(0) = 0, so result = 0 + beta = beta
        assert isinstance(result, FreeParameterExpression)

    def test_arcsin_subs(self):
        expr = arcsin(_fp("x"))
        result = expr.subs({"x": 1})
        # arcsin(1) = pi/2 which SymPy keeps symbolic, so evaluate numerically
        if isinstance(result, FreeParameterExpression):
            result = float(sympy.N(result.expression))
        assert abs(float(result) - math.pi / 2) < 1e-9

    def test_exp_subs(self):
        expr = exp(_fp("x"))
        result = expr.subs({"x": 0})
        assert float(result) == pytest.approx(1.0)

    def test_sqrt_subs(self):
        expr = sqrt(_fp("x"))
        result = expr.subs({"x": 4})
        assert float(result) == pytest.approx(2.0)

    def test_mod_subs(self):
        expr = mod(_fp("x"), 3)
        result = expr.subs({"x": 7})
        assert float(result) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# OpenQASM string emission via str()
# ---------------------------------------------------------------------------

class TestOpenQASMEmission:
    def test_sin_str(self):
        assert str(sin(_fp("alpha"))) == "sin(alpha)"

    def test_cos_str(self):
        assert str(cos(_fp("alpha"))) == "cos(alpha)"

    def test_arcsin_str(self):
        assert str(arcsin(_fp("alpha"))) == "arcsin(alpha)"

    def test_arccos_str(self):
        assert str(arccos(_fp("alpha"))) == "arccos(alpha)"

    def test_arctan_str(self):
        assert str(arctan(_fp("alpha"))) == "arctan(alpha)"

    def test_exp_str(self):
        assert str(exp(_fp("alpha"))) == "exp(alpha)"

    def test_log_str(self):
        assert str(log(_fp("alpha"))) == "log(alpha)"

    def test_sqrt_str(self):
        assert str(sqrt(_fp("alpha"))) == "sqrt(alpha)"

    def test_ceiling_str(self):
        assert str(ceiling(_fp("alpha"))) == "ceiling(alpha)"

    def test_floor_str(self):
        assert str(floor(_fp("alpha"))) == "floor(alpha)"

    def test_compound_str(self):
        alpha = _fp("alpha")
        expr = sin(alpha / 2) ** 2 + cos(alpha / 2) ** 2
        s = str(expr)
        assert "sin" in s and "cos" in s
