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

import gast

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm.autograph.converters import return_statements
from braket.experimental.autoqasm.autograph.core import ag_ctx, converter
from braket.experimental.autoqasm.autograph.pyct import templates


class ReturnTransformer(converter.Base):
    def visit_Return(self, node: ast.stmt) -> ast.stmt:
        """AutoQASM-specific return statement transformations.

        Args:
            node (ast.stmt): Return statement node to transform.

        Returns:
            ast.stmt: Transformed return statement node.
        """
        aq_context = program.get_program_conversion_context()
        if aq_context.subroutines_processing or node.value is None:
            return node

        template = (
            "name_ = ag__.assign_for_output(name_const_, "
            "ag__.return_output_from_main_(name_const_, value_))"
        )

        name = "retval_"
        if isinstance(node.value, gast.Name):
            name = node.value.id

        node = templates.replace(
            template,
            name_=name,
            name_const_=gast.Constant(name, None),
            value_=node.value,
            original=node,
        )
        return node


def transform(
    node: ast.stmt, ctx: ag_ctx.ControlStatusCtx, default_to_null_return: bool = True
) -> ast.stmt:
    """Handle AutoQASM-specific return statement functionality before
    passing control to AutoGraph.

    Args:
        node (ast.stmt): AST node to transform.
        ctx (ag_ctx.ControlStatusCtx): Transformer context.
        default_to_null_return (bool): Configuration option.

    Returns:
        ast.stmt: Transformed node.
    """
    node = ReturnTransformer(ctx).visit(node)
    return return_statements.transform(node, ctx)
