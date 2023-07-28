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

import pytest

from braket.circuits import Operator
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.serialization import IRType


@pytest.fixture
def ascii_symbols():
    return ["foo"]


@pytest.fixture
def compiler_directive(ascii_symbols):
    return CompilerDirective(ascii_symbols=ascii_symbols)


def test_is_operator(compiler_directive):
    assert isinstance(compiler_directive, Operator)


def test_ascii_symbols(compiler_directive, ascii_symbols):
    assert compiler_directive.ascii_symbols == tuple(ascii_symbols)


def test_none_ascii():
    with pytest.raises(ValueError):
        CompilerDirective(ascii_symbols=None)


def test_name(compiler_directive):
    expected = compiler_directive.__class__.__name__
    assert compiler_directive.name == expected


def test_counterpart_not_implemented_by_default(compiler_directive):
    with pytest.raises(NotImplementedError):
        compiler_directive.counterpart()


def test_str(compiler_directive):
    assert str(compiler_directive) == compiler_directive.name


@pytest.mark.parametrize(
    "ir_type, serialization_properties, expected_exception, expected_message",
    [
        (IRType.JAQCD, None, NotImplementedError, "to_jaqcd has not been implemented yet."),
        (IRType.OPENQASM, None, NotImplementedError, "to_openqasm has not been implemented yet."),
        ("invalid-ir-type", None, ValueError, "Supplied ir_type invalid-ir-type is not supported."),
    ],
)
def test_compiler_directive_to_ir(
    ir_type, serialization_properties, expected_exception, expected_message, compiler_directive
):
    with pytest.raises(expected_exception) as exc:
        compiler_directive.to_ir(0, ir_type, serialization_properties=serialization_properties)
    assert exc.value.args[0] == expected_message
