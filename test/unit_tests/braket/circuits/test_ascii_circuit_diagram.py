# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from braket.circuits import AsciiCircuitDiagram, Circuit, Gate, Instruction, Operator


def test_empty_circuit():
    assert AsciiCircuitDiagram.build_diagram(Circuit()) == ""


def test_qubit_width():
    circ = Circuit().h(0).h(100)
    expected = (
        "T    : |0|",
        "          ",
        "q0   : -H-",
        "          ",
        "q100 : -H-",
        "",
        "T    : |0|",
    )
    expected = "\n".join(expected)
    assert AsciiCircuitDiagram.build_diagram(circ) == expected


def test_gate_width():
    class Foo(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["FOO"])

        def to_ir(self, target):
            return "foo"

    circ = Circuit().h(0).h(1).add_instruction(Instruction(Foo(), 0))
    expected = (
        "T  : |0|1  |",
        "            ",
        "q0 : -H-FOO-",
        "            ",
        "q1 : -H-----",
        "",
        "T  : |0|1  |",
    )
    expected = "\n".join(expected)
    assert AsciiCircuitDiagram.build_diagram(circ) == expected


def test_connector_across_two_qubits():
    circ = Circuit().cnot(3, 4).h(range(2, 6))
    expected = (
        "T  : |0|1|",
        "          ",
        "q2 : -H---",
        "          ",
        "q3 : -C-H-",
        "      |   ",
        "q4 : -X-H-",
        "          ",
        "q5 : -H---",
        "",
        "T  : |0|1|",
    )
    expected = "\n".join(expected)
    assert AsciiCircuitDiagram.build_diagram(circ) == expected


def test_connector_across_gt_two_qubits():
    circ = Circuit().h(4).cnot(3, 5).h(4).h(2)
    expected = (
        "T  : |0|1|2|",
        "            ",
        "q2 : -H-----",
        "            ",
        "q3 : ---C---",
        "        |   ",
        "q4 : -H-|-H-",
        "        |   ",
        "q5 : ---X---",
        "",
        "T  : |0|1|2|",
    )
    expected = "\n".join(expected)
    assert AsciiCircuitDiagram.build_diagram(circ) == expected


def test_connector_across_non_used_qubits():
    circ = Circuit().h(4).cnot(3, 100).h(4).h(101)
    expected = (
        "T    : |0|1|2|",
        "              ",
        "q3   : ---C---",
        "          |   ",
        "q4   : -H-|-H-",
        "          |   ",
        "q100 : ---X---",
        "              ",
        "q101 : -H-----",
        "",
        "T    : |0|1|2|",
    )
    expected = "\n".join(expected)
    assert AsciiCircuitDiagram.build_diagram(circ) == expected


def test_ignore_non_gates():
    class Foo(Operator):
        @property
        def name(self) -> str:
            return "foo"

        def to_ir(self, target):
            return "foo"

    circ = Circuit().h(0).h(1).cnot(1, 2).add_instruction(Instruction(Foo(), 0))
    expected = (
        "T  : |0|1|",
        "          ",
        "q0 : -H---",
        "          ",
        "q1 : -H-C-",
        "        | ",
        "q2 : ---X-",
        "",
        "T  : |0|1|",
    )
    expected = "\n".join(expected)
    assert AsciiCircuitDiagram.build_diagram(circ) == expected
