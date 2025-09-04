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

import braket.ir.jaqcd as ir
from braket.circuits import compiler_directives
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.serialization import IRType
from braket.circuits.serialization import OpenQASMSerializationProperties, QubitReferenceType


@pytest.mark.parametrize(
    "testclass,irclass,openqasm_str,counterpart",
    [
        (
            compiler_directives.StartVerbatimBox,
            ir.StartVerbatimBox,
            "#pragma braket verbatim\nbox{",
            compiler_directives.EndVerbatimBox,
        ),
        (
            compiler_directives.EndVerbatimBox,
            ir.EndVerbatimBox,
            "}",
            compiler_directives.StartVerbatimBox,
        ),
    ],
)
def test_verbatim(testclass, irclass, openqasm_str, counterpart):
    directive = testclass()
    assert directive.counterpart() == counterpart()
    assert directive.requires_physical_qubits

    assert directive.to_ir(ir_type=IRType.JAQCD) == irclass()
    assert directive.to_ir(ir_type=IRType.OPENQASM) == openqasm_str

    op = testclass()
    assert directive == op
    assert directive is not op
    assert directive != CompilerDirective(ascii_symbols=["foo"])
    assert directive != "not a directive"


def test_barrier():
    barrier = compiler_directives.Barrier([0, 1, 2])
    assert barrier.qubit_indices == [0, 1, 2]
    assert barrier.qubit_count == 3
    assert barrier.ascii_symbols == ("||",)
    assert repr(barrier) == "Barrier"

    with pytest.raises(NotImplementedError, match="Barrier is not supported in JAQCD"):
        barrier._to_jaqcd()

    props = OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL)
    result = barrier.to_ir([0, 1, 2], IRType.OPENQASM, props)
    assert result == "barrier q[0], q[1], q[2];"

    result = barrier.to_ir([], IRType.OPENQASM, props)
    assert result == "barrier;"
