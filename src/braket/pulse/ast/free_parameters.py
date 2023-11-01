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

from braket.parametric.free_parameter_expression import FreeParameterExpression
from openpulse import ast
from openqasm3.ast import DurationLiteral
from openqasm3.visitor import QASMTransformer


class _FreeParameterExpressionIdentifier(ast.Identifier):
    """Dummy AST node with FreeParameterExpression instance attached"""

    def __init__(self, expression: FreeParameterExpression):
        super().__init__(name=f"FreeParameterExpression({expression})")
        self._expression = expression

    @property
    def expression(self) -> FreeParameterExpression:
        return self._expression


class _FreeParameterTransformer(QASMTransformer):
    """Walk the AST and evaluate FreeParameterExpressions."""

    def __init__(self, param_values: dict[str, float]):
        self.param_values = param_values
        super().__init__()

    def visit__FreeParameterExpressionIdentifier(
        self, identifier: ast.Identifier
    ) -> Union[_FreeParameterExpressionIdentifier, ast.FloatLiteral]:
        """Visit a FreeParameterExpressionIdentifier.

        Args:
            identifier (ast.Identifier): The identifier.

        Returns:
            Union[_FreeParameterExpressionIdentifier, ast.FloatLiteral]: The transformed expression.
        """
        new_value = identifier.expression.subs(self.param_values)
        if isinstance(new_value, FreeParameterExpression):
            return _FreeParameterExpressionIdentifier(new_value)
        else:
            return ast.FloatLiteral(new_value)

    def visit_DurationLiteral(self, duration_literal: DurationLiteral) -> DurationLiteral:
        """Visit Duration Literal.
            node.value, node.unit (node.unit.name, node.unit.value)
            1
        Args:
            duration_literal (DurationLiteral): The duration literal.

        Returns:
            DurationLiteral: The transformed duration literal.
        """
        duration = duration_literal.value
        if not isinstance(duration, FreeParameterExpression):
            return duration_literal
        return DurationLiteral(duration.subs(self.param_values), duration_literal.unit)
