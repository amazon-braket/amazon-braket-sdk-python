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

import operator
from typing import Union

from openpulse import ast
from openqasm3.visitor import QASMTransformer
from oqpy.program import Program
from oqpy.timing import OQDurationLiteral


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
        if identifier.name in self.param_values:
            return ast.FloatLiteral(float(self.param_values[identifier.name]))
        return identifier

    def visit_BinaryExpression(
        self, node: ast.BinaryExpression
    ) -> Union[ast.BinaryExpression, ast.FloatLiteral]:
        """Visit a BinaryExpression.

        Visit the operands and simplify if they are literals.

        Args:
            node (BinaryExpression): The node.

        Returns:
            Union[BinaryExpression, FloatLiteral]: The transformed identifier.
        """
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        if isinstance(lhs, ast.FloatLiteral):
            ops = {
                ast.BinaryOperator["+"]: operator.add,
                ast.BinaryOperator["*"]: operator.mul,
                ast.BinaryOperator["**"]: operator.pow,
            }
            if isinstance(rhs, ast.FloatLiteral):
                return ast.FloatLiteral(ops[node.op](lhs.value, rhs.value))
            if isinstance(rhs, ast.DurationLiteral) and node.op == ast.BinaryOperator["*"]:
                return OQDurationLiteral(lhs.value * rhs.value).to_ast(self.program)
        return ast.BinaryExpression(op=node.op, lhs=lhs, rhs=rhs)

    def visit_UnaryExpression(
        self, node: ast.UnaryExpression
    ) -> Union[ast.UnaryExpression, ast.FloatLiteral]:
        """Visit an UnaryExpression.

        Visit the operand and simplify if it is a literal.

        Args:
            node (UnaryExpression): The node.

        Returns:
            Union[UnaryExpression, FloatLiteral]: The transformed identifier.
        """
        expression = self.visit(node.expression)
        if (
            isinstance(expression, (ast.FloatLiteral, ast.DurationLiteral))
            and node.op == ast.UnaryOperator["-"]
        ):
            return type(expression)(-expression.value)
        return ast.UnaryExpression(op=node.op, expression=node.expression)  # pragma: no cover
