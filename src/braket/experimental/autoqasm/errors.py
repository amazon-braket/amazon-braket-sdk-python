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


class AutoQasmError(Exception):
    """Base class for all AutoQASM exceptions."""


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


class InconsistentNumQubits(AutoQasmError):
    """Num qubits supplied to main function does not match subroutine."""

    def __init__(self):
        self.message = """\
The number of qubits specified by one of your subroutines does not match the \
arguments supplied to your main function. Remove the num_qubits decorator \
argument to all AutoQASM decorated functions except the one you wish to call."""

    def __str__(self):
        return self.message
