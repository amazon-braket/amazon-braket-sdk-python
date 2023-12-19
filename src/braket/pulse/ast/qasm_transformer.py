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
    """
    QASMTransformer which walks the AST and makes the necessary modifications needed
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
            isinstance(expression_statement.expression, ast.FunctionCall)
            and expression_statement.expression.name.name == "capture_v0"
            and self._register_identifier
        ):
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
        else:
            return expression_statement

    def visit_Program(self, program: ast.Program) -> ast.Program:
        """Visit a Program.
        Args:
            program (Program): The program.
        Returns:
            Program: the modified program.
        """
        new_statement_list = []
        for statement in program.statements:
            if isinstance(statement, ast.CalibrationStatement):
                input_vars, body = self.split_input_vars(statement.body)
                new_statement_list.extend(input_vars)
                new_statement_list.append(ast.CalibrationStatement(body))
            else:
                new_statement_list.append(statement)

        program.statements = new_statement_list
        return self.generic_visit(program)

    def split_input_vars(
        self,
        body: list[ast.Statement],
    ) -> tuple[list[ast.IODeclaration], list[ast.Statement]]:
        """Split input vars out of the calibrationStatement block

        Args:
            body (list[Statement]): The list of statement in the CalibrationStatement block
        Returns:
            tuple[list[IODeclaration], list[Statement]]: A tuple of input vars and the list
            of remaining statements.
        """
        input_vars = []
        new_body = []
        for child in body:
            if isinstance(child, ast.IODeclaration) and child.io_identifier is ast.IOKeyword.input:
                input_vars.append(child)
            else:
                new_body.append(child)
        return input_vars, new_body
