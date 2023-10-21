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

"""Mock transpiler for testing converters."""

from typing import Union

import gast

from braket.experimental.autoqasm.autograph.core import ag_ctx
from braket.experimental.autoqasm.transpiler import PyToOqpy

# TODO: Implement a converter abstract class for better type hinting.


class MockTranspiler(PyToOqpy):
    def __init__(self, converters: list):
        """A custom transpiler based on `transpiler.PyToOqpy` for unit testing
        converters.
        Args:
            converters (list): List of converters to test.
        """
        super(MockTranspiler, self).__init__()
        if isinstance(converters, (list, tuple)):
            self._converters = converters
        else:
            self._converters = (converters,)

    def transform_ast(
        self, node: Union[gast.Lambda, gast.FunctionDef], ctx: ag_ctx.ControlStatusCtx
    ) -> Union[gast.Lambda, gast.FunctionDef]:
        """Transform AST from a node using the provided converters.
        Args:
            node (Union[Lambda, FunctionDef]): One or more ast.AST nodes
                representing the AST to be transformed.
            ctx (ControlStatusCtx): transformer context.

        Returns:
            Union[Lambda, FunctionDef]: The root of the transformed AST.
        """
        node = self._initial_analysis(node, ctx)

        for c in self._converters:
            node = c.transform(node, ctx)

        return node
