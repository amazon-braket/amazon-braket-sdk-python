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

from typing import Any, Optional

from openpulse import ast
from openqasm3.visitor import QASMTransformer


class _IRQASMTransformer(QASMTransformer):
    """QASMTransformer which walks the AST and makes the necessary modifications needed
    for IR generation. Currently, it performs the following operations:
      * Replaces capture_v0 function calls with assignment statements, assigning the
        readout value to a bit register element.
    """

    def __init__(self, register_identifier: Optional[str] = None):
        self._register_identifier = register_identifier
        self._capture_v0_count = 0
        super().__init__()

    def visit_ExpressionStatement(self, expression_statement: ast.ExpressionStatement) -> Any:
        """Visit an Expression.

        Args:
            expression_statement (ast.ExpressionStatement): The expression statement.

        Returns:
            Any: The expression statement.
        """
        if (
            not isinstance(expression_statement.expression, ast.FunctionCall)
            or expression_statement.expression.name.name != "capture_v0"
            or not self._register_identifier
        ):
            return expression_statement
        # For capture_v0 nodes, it replaces it with classical assignment statements
        # of the form:
        # b[0] = capture_v0(...)
        # b[1] = capture_v0(...)
        new_val = ast.ClassicalAssignment(
            # Ideally should use IndexedIdentifier here, but this works since it is just
            # for printing.
            ast.Identifier(name=f"{self._register_identifier}[{self._capture_v0_count}]"),
            ast.AssignmentOperator["="],
            expression_statement.expression,
        )
        self._capture_v0_count += 1
        return new_val
