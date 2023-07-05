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


"""Converters for assignment nodes."""

import ast

import gast

from braket.experimental.autoqasm.autograph.core import ag_ctx, converter
from braket.experimental.autoqasm.autograph.pyct import templates


class AssignTransformer(converter.Base):
    def visit_Assign(self, node: ast.stmt) -> ast.stmt:
        """Converts assignment operations to their AutoQASM counterpart.
        Supports assignment to a single variable. Operator declares the
        ``oq`` variable, or sets variable's value if it's already declared.

        Args:
            node (ast.stmt): AST node to transform.

        Returns:
            ast.stmt: Transformed node.
        """
        template = """
        tar_ = ag__.assign_stmt(tar_name_, val_)
        """
        node = self.generic_visit(node)

        # TODO: implement when target has multiple variable
        if len(node.targets) > 1:
            raise NotImplementedError

        if isinstance(node.targets[0], gast.Name):
            target_name = gast.Constant(node.targets[0].id, None)
            new_node = templates.replace(
                template,
                tar_name_=target_name,
                tar_=node.targets[0],
                val_=node.value,
                original=node,
            )
        else:
            new_node = node

        return new_node


def transform(node: ast.stmt, ctx: ag_ctx.ControlStatusCtx) -> ast.stmt:
    """Transform assignment nodes.

    Args:
        node (ast.stmt): AST node to transform.
        ctx (ag_ctx.ControlStatusCtx): Transformer context.

    Returns:
        ast.stmt: Transformed node.
    """

    return AssignTransformer(ctx).visit(node)
