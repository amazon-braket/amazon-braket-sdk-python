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


"""Converters for break statement nodes."""

import ast

from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.autograph.converters import break_statements
from braket.experimental.autoqasm.autograph.core import ag_ctx, converter


class BreakValidator(converter.Base):
    def visit_Break(self, node: ast.stmt) -> ast.stmt:
        """Break statements are currently unsupported."""
        raise errors.UnsupportedFeature("Break statements are currently unsupported.")


def transform(
    node: ast.stmt, ctx: ag_ctx.ControlStatusCtx, default_to_null_return: bool = True
) -> ast.stmt:
    node = BreakValidator(ctx).visit(node)
    # When break statements are supported, we may want to fall back on default behavior
    return break_statements.transform(node, ctx)  # pragma: no cover
