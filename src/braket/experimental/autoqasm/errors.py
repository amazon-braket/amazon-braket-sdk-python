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


class AutoQasmTypeError(AutoQasmError):
    """Generic type error."""


class UnsupportedFeatureError(AutoQasmError):
    """AutoQASM unsupported feature."""


class ParameterTypeError(AutoQasmError):
    """AutoQASM parameter type error."""


class MissingParameterTypeError(AutoQasmError):
    """AutoQASM requires type hints for subroutine parameters."""


class InvalidGateDefinition(AutoQasmError):
    """Gate definition does not meet the necessary requirements."""


class UnsupportedGate(AutoQasmError):
    """Gate is not supported by the target device."""


class UnsupportedNativeGate(AutoQasmError):
    """Native gate is not supported by the target device."""


class VerbatimBlockNotAllowed(AutoQasmError):
    """Verbatim block is not supported by the target device."""


class UnknownQubitCountError(AutoQasmError):
    """Missing declaration for the number of qubits."""

    def __init__(self):
        self.message = """Unspecified number of qubits.

Specify the number of qubits used by your program by supplying the \
`num_qubits` argument to `aq.main`. For example:

    @aq.main(num_qubits=5)
    def my_autoqasm_program():
        ...
"""

    def __str__(self):
        return self.message


class InsufficientQubitCountError(AutoQasmError):
    """Target device does not have enough qubits for the program."""


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
