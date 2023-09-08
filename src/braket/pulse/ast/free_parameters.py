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
from typing import Dict, Union

from openpulse import ast
from openqasm3.visitor import QASMTransformer
from oqpy.program import Program
from oqpy.timing import OQDurationLiteral

from braket.parametric.free_parameter_expression import FreeParameterExpression


class _FreeParameterExpressionIdentifier(ast.QASMNode):
    """Dummy AST node with FreeParameterExpression instance attached"""

    def __init__(
        self, expression: FreeParameterExpression, type_: ast.ClassicalType = ast.FloatType()
    ):
        self.name = f"FreeParameterExpression({expression})"
        self._expression = expression
        self.type_ = type_

    @property
    def expression(self) -> FreeParameterExpression:
        return self._expression

    def __repr__(self) -> str:
        return f"_FreeParameterExpressionIdentifier(name={self.name})"

    def to_ast(self, program: Program) -> ast.Expression:
        if isinstance(self.type_, ast.DurationType):
            return ast.DurationLiteral(self, ast.TimeUnit.s)
        return self


class _FreeParameterTransformer(QASMTransformer):
    """Walk the AST and evaluate FreeParameterExpressions."""

    def __init__(self, param_values: Dict[str, float], program: Program):
        self.param_values = param_values
        self.program = program
        super().__init__()

    def visit__FreeParameterExpressionIdentifier(
        self, identifier: _FreeParameterExpressionIdentifier
    ) -> Union[_FreeParameterExpressionIdentifier, ast.FloatLiteral]:
        """Visit a FreeParameterExpressionIdentifier.
        Args:
            identifier (_FreeParameterExpressionIdentifier): The identifier.

        Returns:
            Union[_FreeParameterExpressionIdentifier, FloatLiteral]: The transformed expression.
        """
        new_value = identifier.expression.subs(self.param_values)
        if isinstance(new_value, FreeParameterExpression):
            return _FreeParameterExpressionIdentifier(new_value, identifier.type_)
        return ast.FloatLiteral(new_value)

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
        if not isinstance(duration, _FreeParameterExpressionIdentifier):
            return duration_literal
        new_duration = duration.expression.subs(self.param_values)
        if isinstance(new_duration, FreeParameterExpression):
            return _FreeParameterExpressionIdentifier(new_duration, duration.type_).to_ast(
                self.program
            )
        return OQDurationLiteral(new_duration).to_ast(self.program)
