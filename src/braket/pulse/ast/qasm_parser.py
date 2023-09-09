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
import io

from openpulse import ast
from openpulse.printer import Printer
from openqasm3.ast import DurationLiteral
from openqasm3.printer import PrinterState

from braket.pulse.ast.free_parameters import _FreeParameterExpressionIdentifier


class _PulsePrinter(Printer):
    """Walks the AST and prints it to an OpenQASM3 string."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def visit__FreeParameterExpressionIdentifier(
        self, node: ast.Identifier, context: PrinterState
    ) -> None:
        """Visit a FreeParameterExpressionIdentifier.
        Args:
            node (ast.Identifier): The identifier.
            context (PrinterState): The printer state context.
        """
        self.stream.write(str(node.expression.expression))

    def visit_DurationLiteral(self, node: DurationLiteral, context: PrinterState) -> None:
        """Visit Duration Literal.
            node.value, node.unit (node.unit.name, node.unit.value)
            1
        Args:
            node (ast.DurationLiteral): The duration literal.
            context (PrinterState): The printer state context.
        """
        duration = node.value
        if isinstance(duration, _FreeParameterExpressionIdentifier):
            self.stream.write(f"({duration.expression}) * 1{node.unit.name}")
        else:
            super().visit_DurationLiteral(node, context)

    def visit_ClassicalDeclaration(
        self, node: ast.ClassicalDeclaration, context: PrinterState
    ) -> None:
        """Visit a Classical Declaration.
            node.type, node.identifier, node.init_expression
            angle[20] a = 1+2;
            waveform wf = [];
            port a;
        Args:
            node (ast.ClassicalDeclaration): The classical declaration.
            context (PrinterState): The printer state context.
        """
        # Skip port declarations in output
        if not isinstance(node.type, ast.PortType):
            super().visit_ClassicalDeclaration(node, context)


def ast_to_qasm(ast: ast.Program) -> str:
    """Converts an AST program to OpenQASM

    Args:
        ast (Program): The AST program.

    Returns:
        str: a str representing the OpenPulse program encoding the program.
    """
    out = io.StringIO()
    _PulsePrinter(out, indent="    ").visit(ast)
    return out.getvalue().strip()
