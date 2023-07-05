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

from braket.experimental.autoqasm.program import ProgramOptions


class AutoQasmError(Exception):
    """Base class for all AutoQASM exceptions."""


class UnknownQubitCountError(AutoQasmError):
    """Missing declaration for the number of qubits."""

    def __init__(self):
        self.message = f"""Unspecified number of qubits.

Please declare the total number of qubits for your program. \
You can do that by calling your AutoQASM program with the \
{ProgramOptions.NUM_QUBITS.value} keyword argument. \
"""

    def __str__(self):
        return self.message
