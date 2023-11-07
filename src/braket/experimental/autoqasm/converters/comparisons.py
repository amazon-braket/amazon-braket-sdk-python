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

"""Converters for comparison nodes."""

import ast

import gast

from braket.experimental.autoqasm.autograph.core import ag_ctx, converter
from braket.experimental.autoqasm.autograph.pyct import templates

COMPARISON_OPERATORS = {
    gast.Lt: "ag__.lt_",
    gast.LtE: "ag__.lteq_",
    gast.Gt: "ag__.gt_",
    gast.GtE: "ag__.gteq_",
}


class ComparisonTransformer(converter.Base):
    """Transformer for comparison nodes."""

    def visit_Compare(self, node: ast.stmt) -> ast.stmt:
        """Transforms a comparison node.

        Args:
            node (ast.stmt): AST node to transform.

        Returns:
            ast.stmt: Transformed node.
        """
        node = self.generic_visit(node)

        op_type = type(node.ops[0])
        if op_type not in COMPARISON_OPERATORS:
            return node

        template = f"{COMPARISON_OPERATORS[op_type]}(lhs_, rhs_)"

        return templates.replace(
            template,
            lhs_=node.left,
            rhs_=node.comparators[0],
            original=node,
        )[0].value


def transform(node: ast.stmt, ctx: ag_ctx.ControlStatusCtx) -> ast.stmt:
    """Transform comparison nodes.

    Args:
        node (ast.stmt): AST node to transform.
        ctx (ag_ctx.ControlStatusCtx): Transformer context.

    Returns:
        ast.stmt: Transformed node.
    """

    return ComparisonTransformer(ctx).visit(node)
