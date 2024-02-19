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

from typing import Any

import braket.ir.jaqcd as ir
from braket.circuits.compiler_directive import CompilerDirective


class StartVerbatimBox(CompilerDirective):
    """Prevents the compiler from modifying any ensuing instructions
    until the appearance of a corresponding ``EndVerbatimBox``.
    """

    def __init__(self):
        super().__init__(["StartVerbatim"])

    def counterpart(self) -> CompilerDirective:
        return EndVerbatimBox()

    def _to_jaqcd(self, *args, **kwargs) -> Any:
        return ir.StartVerbatimBox.construct()

    def _to_openqasm(self) -> str:
        return "#pragma braket verbatim\nbox{"


class EndVerbatimBox(CompilerDirective):
    """Marks the end of a portion of code following a StartVerbatimBox that prevents the enclosed
    instructions from being modified by the compiler.
    """

    def __init__(self):
        super().__init__(["EndVerbatim"])

    def counterpart(self) -> CompilerDirective:
        return StartVerbatimBox()

    def _to_jaqcd(self, *args, **kwargs) -> Any:
        return ir.EndVerbatimBox.construct()

    def _to_openqasm(self) -> str:
        return "}"
