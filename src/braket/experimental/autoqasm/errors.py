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

"""Errors raised in the AutoQASM build process."""


from typing import Optional


class AutoQasmError(Exception):
    """Base class for all AutoQASM exceptions."""


class UnsupportedFeatureError(AutoQasmError):
    """AutoQASM unsupported feature."""


class ParameterTypeError(AutoQasmError):
    """AutoQASM parameter type error."""


class MissingParameterTypeError(AutoQasmError):
    """AutoQASM requires type hints for subroutine parameters."""


class InvalidGateDefinition(AutoQasmError):
    """Gate definition does not meet the necessary requirements."""


class UnknownQubitCountError(AutoQasmError):
    """Missing declaration for the number of qubits."""

    def __init__(self):
        self.message = """Unspecified number of qubits.

Specify the number of qubits used by your program by supplying the \
`num_qubits` argument to `autoqasm.function`. For example:

    @autoqasm.function(num_qubits=5)
    def my_autoqasm_function():
        ...
"""

    def __str__(self):
        return self.message


class UnsupportedConditionalExpressionError(AutoQasmError):
    """Conditional expressions which return values are not supported."""

    def __init__(self, true_type: Optional[type], false_type: Optional[type]):
        if_type = true_type.__name__ if true_type else "None"
        else_type = false_type.__name__ if false_type else "None"
        self.message = """\
`if` clause resolves to {}, but `else` clause resolves to {}. \
Both the `if` and `else` clauses of an inline conditional expression \
must resolve to the same type.""".format(
            if_type, else_type
        )

    def __str__(self):
        return self.message
