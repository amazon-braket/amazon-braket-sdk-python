# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from typing import Union

from openpulse import ast
from openqasm3.visitor import QASMTransformer
from oqpy.program import Program
from oqpy.timing import OQDurationLiteral

from braket.parametric.free_parameter_expression import FreeParameterExpression


class _FreeDurationParameterExpression(FreeParameterExpression):
    def __add__(self, other):
        if isinstance(other, _FreeDurationParameterExpression):
            return _FreeDurationParameterExpression(self.expression + other.expression)
        if isinstance(other, FreeParameterExpression):
            raise TypeError(
                "Cannot add a FreeParameterExpression to a _FreeDurationParameterExpression"
            )
        else:
            return _FreeDurationParameterExpression(self.expression + other)

    def __radd__(self, other):
        return _FreeDurationParameterExpression(other + self.expression)

    def __sub__(self, other):
        if isinstance(other, _FreeDurationParameterExpression):
            return _FreeDurationParameterExpression(self.expression - other.expression)
        elif isinstance(other, FreeParameterExpression):
            raise TypeError(
                "Cannot substract a FreeParameterExpression to a _FreeDurationParameterExpression"
            )
        else:
            return _FreeDurationParameterExpression(self.expression - other)

    def __rsub__(self, other):
        return _FreeDurationParameterExpression(other - self.expression)

    def __mul__(self, other):
        if isinstance(other, _FreeDurationParameterExpression):
            raise TypeError("Cannot multiply two _FreeDurationParameterExpression")
        elif isinstance(other, FreeParameterExpression):
            return _FreeDurationParameterExpression(self.expression * other.expression)
        else:
            return FreeParameterExpression(self.expression * other)

    def __rmul__(self, other):
        return _FreeDurationParameterExpression(other * self.expression)

    def __pow__(self, other, modulo=None):
        raise TypeError("Cannot exponentiate a _FreeDurationParameterExpression")

    def __rpow__(self, other):
        raise TypeError("Cannot exponentiate a _FreeDurationParameterExpression")

    def __neg__(self):
        return _FreeDurationParameterExpression(-1 * self.expression)

    def to_ast(self, program: Program) -> ast.Expression:
        """Creates an AST node for the :class:'FreeParameterExpression'.

        Args:
            program (Program): Unused.

        Returns:
            Expression: The AST node.
        """
        # TODO (#822): capture expressions into expression ASTs rather than just an Identifier
        return ast.DurationLiteral(ast.Identifier(name=self), ast.TimeUnit.s)


class _FreeParameterTransformer(QASMTransformer):
    """Walk the AST and evaluate FreeParameterExpressions."""

    def __init__(self, param_values: dict[str, float], program: Program):
        self.param_values = param_values
        self.program = program
        super().__init__()

    def visit_Identifier(
        self, identifier: ast.Identifier
    ) -> Union[ast.Identifier, ast.FloatLiteral]:
        """Visit an Identifier.

        If the Identifier is used to hold a `FreeParameterExpression`, it will be simplified
        using the given parameter values.

        Args:
            identifier (Identifier): The identifier.

        Returns:
            Union[Identifier, FloatLiteral]: The transformed identifier.
        """
        if isinstance(identifier.name, FreeParameterExpression):
            new_value = FreeParameterExpression(identifier.name).subs(self.param_values)
            if isinstance(new_value, FreeParameterExpression):
                return ast.Identifier(new_value)
            else:
                return ast.FloatLiteral(float(new_value))
        return identifier

    def visit_DurationLiteral(self, duration_literal: ast.DurationLiteral) -> ast.DurationLiteral:
        """Visit Duration Literal.
            node.value, node.unit (node.unit.name, node.unit.value)
            1
        Args:
            duration_literal (DurationLiteral): The duration literal.
        Returns:
            DurationLiteral: The transformed duration literal.
        """
        duration = duration_literal.value
        if not isinstance(duration, ast.Identifier):
            return duration_literal
        new_duration = _FreeDurationParameterExpression(duration.name).subs(self.param_values)
        if isinstance(new_duration, _FreeDurationParameterExpression):
            return ast.DurationLiteral(ast.Identifier(str(new_duration)), duration_literal.unit)
        return OQDurationLiteral(new_duration).to_ast(self.program)
