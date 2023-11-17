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

"""Tests for pragmas."""

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.instructions import cnot, h


def test_basic_box() -> None:
    """Tests the box statement without a pragma."""
    with aq.build_program() as program_conversion_context:
        with program_conversion_context.box():
            pass

    expected = """OPENQASM 3.0;
box {
}"""

    program = program_conversion_context.make_program()
    assert program.to_ir() == expected


def test_with_verbatim_box() -> None:
    """Tests the with statement with verbatim box `Verbatim`."""

    @aq.main
    def program_func() -> None:
        """User program to test."""
        h(0)
        with aq.verbatim():
            cnot("$1", "$2")

    expected = """OPENQASM 3.0;
qubit[1] __qubits__;
h __qubits__[0];
pragma braket verbatim
box {
    cnot $1, $2;
}"""

    assert program_func.to_ir() == expected


def test_nested_verbatim_box() -> None:
    with pytest.raises(errors.VerbatimBlockNotAllowed):

        @aq.main
        def program_func() -> None:
            with aq.verbatim():
                with aq.verbatim():
                    h(0)


def test_verbatim_box_invalid_target_qubit() -> None:
    with pytest.raises(errors.InvalidTargetQubit):

        @aq.main
        def program_func() -> None:
            with aq.verbatim():
                h(0)
