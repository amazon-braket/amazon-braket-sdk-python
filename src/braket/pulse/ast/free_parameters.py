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

from braket.parametric.free_parameter_expression import (
    FreeParameterExpression,
    _FreeParameterExpressionIdentifier,
)


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
            return _FreeParameterExpressionIdentifier(new_value)
        else:
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
            return ast.DurationLiteral(
                _FreeParameterExpressionIdentifier(new_duration), duration_literal.unit
            )
        return OQDurationLiteral(new_duration).to_ast(self.program)
