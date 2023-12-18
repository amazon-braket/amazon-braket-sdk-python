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

"""Tests for annotations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Optional

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import cnot, h


@pytest.mark.parametrize(
    "var_type, var_value, qasm_type, qasm_value",
    [
        (aq.IntVar, 0, "int[32]", "0"),
        (aq.FloatVar, 0.0, "float[64]", "0.0"),
        (aq.BoolVar, False, "bool", "false"),
    ],
)
def test_variable_annotations(
    var_type: type, var_value: Any, qasm_type: str, qasm_value: str
) -> None:
    """Test annotations on variable declarations."""

    @aq.main
    def main():
        a = var_type(var_value, annotations="foo")  # noqa: F841
        b = var_type(var_value, annotations=["foo", "bar baz"])  # noqa: F841

    expected = (
        """OPENQASM 3.0;
@foo
"""
        + f"{qasm_type} a = {qasm_value};"
        + """
@foo
@bar baz
"""
        + f"{qasm_type} b = {qasm_value};"
    )
    assert main.to_ir() == expected


@pytest.mark.parametrize(
    "annotations, output_annotations",
    [
        (None, ""),
        ([], ""),
        ("foo", "@foo\n"),
        (["foo"], "@foo\n"),
        (["foo", "bar baz"], "@foo\n@bar baz\n"),
    ],
)
def test_subroutine_annotations(
    annotations: Optional[str | Iterable[str]], output_annotations: str
):
    """Test annotations on subroutine declarations."""

    @aq.subroutine(annotations=annotations)
    def subroutine_test():
        pass

    @aq.main
    def main():
        subroutine_test()

    expected = (
        """OPENQASM 3.0;\n"""
        + output_annotations
        + """def subroutine_test() {
}
subroutine_test();"""
    )

    assert main.to_ir() == expected


def test_range_annotations():
    """Test annotations on ranges."""

    @aq.main(num_qubits=5)
    def main():
        for i in aq.range(5, annotations="foo"):
            h(i)
        for i in aq.range(5, annotations=["foo", "bar baz"]):
            h(i)

    expected = """OPENQASM 3.0;
qubit[5] __qubits__;
@foo
for int i in [0:5 - 1] {
    h __qubits__[i];
}
@foo
@bar baz
for int i in [0:5 - 1] {
    h __qubits__[i];
}"""

    assert main.to_ir() == expected


def test_verbatim_box_annotations():
    """Test annotations on verbatim boxes."""

    @aq.main
    def main():
        with aq.verbatim(annotations="foo"):
            h("$0")
        with aq.verbatim(annotations=["foo", "bar baz"]):
            cnot("$0", "$1")

    expected = """OPENQASM 3.0;
pragma braket verbatim
@foo
box {
    h $0;
}
pragma braket verbatim
@foo
@bar baz
box {
    cnot $0, $1;
}"""

    assert main.to_ir() == expected
