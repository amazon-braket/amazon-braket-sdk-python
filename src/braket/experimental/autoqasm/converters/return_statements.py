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


"""Converters for return statement nodes."""

import ast
import warnings

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm.autograph.converters import return_statements
from braket.experimental.autoqasm.autograph.core import ag_ctx, converter


class ReturnValidator(converter.Base):
    def visit_Return(self, node: ast.stmt) -> ast.stmt:
        aq_context = program.get_program_conversion_context()
        if not aq_context.subroutines_processing and node.value is not None:
            warnings.warn("Return value from top level function is ignored.")
        return node


def transform(
    node: ast.stmt, ctx: ag_ctx.ControlStatusCtx, default_to_null_return: bool = True
) -> ast.stmt:
    """Handle AutoQASM-specific return statement functionality before
    passing control to AutoGraph.
    """
    ReturnValidator(ctx).visit(node)
    return return_statements.transform(node, ctx)
