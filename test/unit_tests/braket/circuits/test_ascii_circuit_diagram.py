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

import numpy as np
import pytest

from braket.circuits import (
    AsciiCircuitDiagram,
    Circuit,
    FreeParameter,
    Gate,
    Instruction,
    Noise,
    Observable,
    Operator,
)
from braket.pulse import Frame, Port, PulseSequence


def _assert_correct_diagram(circ, expected):
    assert AsciiCircuitDiagram.build_diagram(circ) == "\n".join(expected)


def test_empty_circuit():
    assert AsciiCircuitDiagram.build_diagram(Circuit()) == ""


def test_only_gphase_circuit():
    assert AsciiCircuitDiagram.build_diagram(Circuit().gphase(0.1)) == "Global phase: 0.1"


def test_one_gate_one_qubit():
    circ = Circuit().h(0)
    expected = ("T  : |0|", "        ", "q0 : -H-", "", "T  : |0|")
    _assert_correct_diagram(circ, expected)


def test_one_gate_one_qubit_rotation():
    circ = Circuit().rx(angle=3.14, target=0)
    # Column formats to length of the gate plus the ascii representation for the angle.
    expected = ("T  : |   0    |", "               ", "q0 : -Rx(3.14)-", "", "T  : |   0    |")
    _assert_correct_diagram(circ, expected)


def test_one_gate_one_qubit_rotation_with_parameter():
    theta = FreeParameter("theta")
    circ = Circuit().rx(angle=theta, target=0)
    # Column formats to length of the gate plus the ascii representation for the angle.
    expected = (
        "T  : |    0    |",
        "                ",
        "q0 : -Rx(theta)-",
        "",
        "T  : |    0    |",
        "",
        "Unassigned parameters: [theta].",
    )
    _assert_correct_diagram(circ, expected)


@pytest.mark.parametrize("target", [0, 1])
def test_one_gate_with_global_phase(target):
    circ = Circuit().x(target=target).gphase(0.15)
    expected = (
        "T  : |0| 1  |",
        "GP : |0|0.15|",
        "             ",
        f"q{target} : -X------",
        "",
        "T  : |0| 1  |",
        "",
        "Global phase: 0.15",
    )
    _assert_correct_diagram(circ, expected)


def test_one_gate_with_zero_global_phase():
    circ = Circuit().gphase(-0.15).x(target=0).gphase(0.15)
    expected = (
        "T  : |  0  | 1  |",
        "GP : |-0.15|0.00|",
        "                 ",
        "q0 : -X----------",
        "",
        "T  : |  0  | 1  |",
    )
    _assert_correct_diagram(circ, expected)


def test_one_gate_one_qubit_rotation_with_unicode():
    theta = FreeParameter("\u03b8")
    circ = Circuit().rx(angle=theta, target=0)
    # Column formats to length of the gate plus the ascii representation for the angle.
    expected = (
        "T  : |  0  |",
        "            ",
        "q0 : -Rx(θ)-",
        "",
        "T  : |  0  |",
        "",
        "Unassigned parameters: [θ].",
    )
    _assert_correct_diagram(circ, expected)


def test_one_gate_with_parametric_expression_global_phase_():
    theta = FreeParameter("\u03b8")
    circ = Circuit().x(target=0).gphase(2 * theta).x(0).gphase(1)
    expected = (
        "T  : |0| 1 |    2    |",
        "GP : |0|2*θ|2*θ + 1.0|",
        "                      ",
        "q0 : -X-X-------------",
        "",
        "T  : |0| 1 |    2    |",
        "",
        "Global phase: 2*θ + 1.0",
        "",
        "Unassigned parameters: [θ].",
    )
    _assert_correct_diagram(circ, expected)


def test_one_gate_one_qubit_rotation_with_parameter_assigned():
    theta = FreeParameter("theta")
    circ = Circuit().rx(angle=theta, target=0)
    new_circ = circ.make_bound_circuit({"theta": np.pi})
    # Column formats to length of the gate plus the ascii representation for the angle.
    expected = (
        "T  : |   0    |",
        "               ",
        "q0 : -Rx(3.14)-",
        "",
        "T  : |   0    |",
    )
    _assert_correct_diagram(new_circ, expected)


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
    _assert_correct_diagram(circ, expected)


def test_gate_width():
    class Foo(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["FOO"])

        def to_ir(self, target):
            return "foo"

    circ = Circuit().h(0).h(1).add_instruction(Instruction(Foo(), 0))
    expected = (
        "T  : |0| 1 |",
        "            ",
        "q0 : -H-FOO-",
        "            ",
        "q1 : -H-----",
        "",
        "T  : |0| 1 |",
    )
    _assert_correct_diagram(circ, expected)


def test_time_width():
    circ = Circuit()
    num_qubits = 15
    for qubit in range(num_qubits):
        if qubit == num_qubits - 1:
            break
        circ.cnot(qubit, qubit + 1)
    expected = (
        "T   : |0|1|2|3|4|5|6|7|8|9|10|11|12|13|",
        "                                       ",
        "q0  : -C-------------------------------",
        "       |                               ",
        "q1  : -X-C-----------------------------",
        "         |                             ",
        "q2  : ---X-C---------------------------",
        "           |                           ",
        "q3  : -----X-C-------------------------",
        "             |                         ",
        "q4  : -------X-C-----------------------",
        "               |                       ",
        "q5  : ---------X-C---------------------",
        "                 |                     ",
        "q6  : -----------X-C-------------------",
        "                   |                   ",
        "q7  : -------------X-C-----------------",
        "                     |                 ",
        "q8  : ---------------X-C---------------",
        "                       |               ",
        "q9  : -----------------X-C-------------",
        "                         |             ",
        "q10 : -------------------X-C-----------",
        "                           |           ",
        "q11 : ---------------------X--C--------",
        "                              |        ",
        "q12 : ------------------------X--C-----",
        "                                 |     ",
        "q13 : ---------------------------X--C--",
        "                                    |  ",
        "q14 : ------------------------------X--",
        "",
        "T   : |0|1|2|3|4|5|6|7|8|9|10|11|12|13|",
    )
    _assert_correct_diagram(circ, expected)


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
    _assert_correct_diagram(circ, expected)


def test_neg_control_qubits():
    circ = Circuit().x(2, control=[0, 1], control_state=[0, 1])
    expected = (
        "T  : |0|",
        "        ",
        "q0 : -N-",
        "      | ",
        "q1 : -C-",
        "      | ",
        "q2 : -X-",
        "",
        "T  : |0|",
    )
    _assert_correct_diagram(circ, expected)


def test_only_neg_control_qubits():
    circ = Circuit().x(2, control=[0, 1], control_state=0)
    expected = (
        "T  : |0|",
        "        ",
        "q0 : -N-",
        "      | ",
        "q1 : -N-",
        "      | ",
        "q2 : -X-",
        "",
        "T  : |0|",
    )
    _assert_correct_diagram(circ, expected)


def test_connector_across_three_qubits():
    circ = Circuit().x(control=(3, 4), target=5).h(range(2, 6))
    expected = (
        "T  : |0|1|",
        "          ",
        "q2 : -H---",
        "          ",
        "q3 : -C-H-",
        "      |   ",
        "q4 : -C-H-",
        "      |   ",
        "q5 : -X-H-",
        "",
        "T  : |0|1|",
    )
    _assert_correct_diagram(circ, expected)


def test_overlapping_qubits():
    circ = Circuit().cnot(0, 2).x(control=1, target=3).h(0)
    expected = (
        "T  : | 0 |1|",
        "            ",
        "q0 : -C---H-",
        "      |     ",
        "q1 : -|-C---",
        "      | |   ",
        "q2 : -X-|---",
        "        |   ",
        "q3 : ---X---",
        "",
        "T  : | 0 |1|",
    )
    _assert_correct_diagram(circ, expected)


def test_overlapping_qubits_angled_gates():
    circ = Circuit().zz(0, 2, 0.15).x(control=1, target=3).h(0)
    expected = (
        "T  : |    0     |1|",
        "                   ",
        "q0 : -ZZ(0.15)---H-",
        "      |            ",
        "q1 : -|--------C---",
        "      |        |   ",
        "q2 : -ZZ(0.15)-|---",
        "               |   ",
        "q3 : ----------X---",
        "",
        "T  : |    0     |1|",
    )
    _assert_correct_diagram(circ, expected)


def test_connector_across_gt_two_qubits():
    circ = Circuit().h(4).x(control=3, target=5).h(4).h(2)
    expected = (
        "T  : | 0 |1|",
        "            ",
        "q2 : -H-----",
        "            ",
        "q3 : ---C---",
        "        |   ",
        "q4 : -H-|-H-",
        "        |   ",
        "q5 : ---X---",
        "",
        "T  : | 0 |1|",
    )
    _assert_correct_diagram(circ, expected)


def test_connector_across_non_used_qubits():
    circ = Circuit().h(4).cnot(3, 100).h(4).h(101)
    expected = (
        "T    : | 0 |1|",
        "              ",
        "q3   : ---C---",
        "          |   ",
        "q4   : -H-|-H-",
        "          |   ",
        "q100 : ---X---",
        "              ",
        "q101 : -H-----",
        "",
        "T    : | 0 |1|",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_1q_no_preceding():
    circ = Circuit().add_verbatim_box(Circuit().h(0))
    expected = (
        "T  : |      0      |1|     2     |",
        "                                  ",
        "q0 : -StartVerbatim-H-EndVerbatim-",
        "",
        "T  : |      0      |1|     2     |",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_1q_preceding():
    circ = Circuit().h(0).add_verbatim_box(Circuit().h(0))
    expected = (
        "T  : |0|      1      |2|     3     |",
        "                                    ",
        "q0 : -H-StartVerbatim-H-EndVerbatim-",
        "",
        "T  : |0|      1      |2|     3     |",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_1q_following():
    circ = Circuit().add_verbatim_box(Circuit().h(0)).h(0)
    expected = (
        "T  : |      0      |1|     2     |3|",
        "                                    ",
        "q0 : -StartVerbatim-H-EndVerbatim-H-",
        "",
        "T  : |      0      |1|     2     |3|",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_2q_no_preceding():
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    expected = (
        "T  : |      0      |1|2|     3     |",
        "                                    ",
        "q0 : -StartVerbatim-H-C-EndVerbatim-",
        "      |               | |           ",
        "q1 : -*************---X-***********-",
        "",
        "T  : |      0      |1|2|     3     |",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_2q_preceding():
    circ = Circuit().h(0).add_verbatim_box(Circuit().h(0).cnot(0, 1))
    expected = (
        "T  : |0|      1      |2|3|     4     |",
        "                                      ",
        "q0 : -H-StartVerbatim-H-C-EndVerbatim-",
        "        |               | |           ",
        "q1 : ---*************---X-***********-",
        "",
        "T  : |0|      1      |2|3|     4     |",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_2q_following():
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)).h(0)
    expected = (
        "T  : |      0      |1|2|     3     |4|",
        "                                      ",
        "q0 : -StartVerbatim-H-C-EndVerbatim-H-",
        "      |               | |             ",
        "q1 : -*************---X-***********---",
        "",
        "T  : |      0      |1|2|     3     |4|",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_3q_no_preceding():
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2))
    expected = (
        "T  : |      0      |1|2|3|     4     |",
        "                                      ",
        "q0 : -StartVerbatim-H-C---EndVerbatim-",
        "      |               |   |           ",
        "q1 : -|---------------X-C-|-----------",
        "      |                 | |           ",
        "q2 : -*************-----X-***********-",
        "",
        "T  : |      0      |1|2|3|     4     |",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_3q_preceding():
    circ = Circuit().h(0).add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2))
    expected = (
        "T  : |0|      1      |2|3|4|     5     |",
        "                                        ",
        "q0 : -H-StartVerbatim-H-C---EndVerbatim-",
        "        |               |   |           ",
        "q1 : ---|---------------X-C-|-----------",
        "        |                 | |           ",
        "q2 : ---*************-----X-***********-",
        "",
        "T  : |0|      1      |2|3|4|     5     |",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_3q_following():
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2)).h(0)
    expected = (
        "T  : |      0      |1|2|3|     4     |5|",
        "                                        ",
        "q0 : -StartVerbatim-H-C---EndVerbatim-H-",
        "      |               |   |             ",
        "q1 : -|---------------X-C-|-------------",
        "      |                 | |             ",
        "q2 : -*************-----X-***********---",
        "",
        "T  : |      0      |1|2|3|     4     |5|",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_different_qubits():
    circ = Circuit().h(1).add_verbatim_box(Circuit().h(0)).cnot(3, 4)
    expected = (
        "T  : |0|      1      |2|     3     |4|",
        "                                      ",
        "q0 : ---StartVerbatim-H-EndVerbatim---",
        "        |               |             ",
        "q1 : -H-|---------------|-------------",
        "        |               |             ",
        "q3 : ---|---------------|-----------C-",
        "        |               |           | ",
        "q4 : ---*************---***********-X-",
        "",
        "T  : |0|      1      |2|     3     |4|",
    )
    _assert_correct_diagram(circ, expected)


def test_verbatim_qubset_qubits():
    circ = Circuit().h(1).cnot(0, 1).cnot(1, 2).add_verbatim_box(Circuit().h(1)).cnot(2, 3)
    expected = (
        "T  : |0|1|2|      3      |4|     5     |6|",
        "                                          ",
        "q0 : ---C---StartVerbatim---EndVerbatim---",
        "        |   |               |             ",
        "q1 : -H-X-C-|-------------H-|-------------",
        "          | |               |             ",
        "q2 : -----X-|---------------|-----------C-",
        "            |               |           | ",
        "q3 : -------*************---***********-X-",
        "",
        "T  : |0|1|2|      3      |4|     5     |6|",
    )
    _assert_correct_diagram(circ, expected)


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
    _assert_correct_diagram(circ, expected)


def test_result_types_target_none():
    circ = Circuit().h(0).h(100).probability()
    expected = (
        "T    : |0|Result Types|",
        "                       ",
        "q0   : -H-Probability--",
        "          |            ",
        "q100 : -H-Probability--",
        "",
        "T    : |0|Result Types|",
    )
    _assert_correct_diagram(circ, expected)


def test_result_types_target_some():
    circ = (
        Circuit()
        .h(0)
        .h(1)
        .h(100)
        .expectation(observable=Observable.Y() @ Observable.Z(), target=[0, 100])
    )
    expected = (
        "T    : |0|  Result Types  |",
        "                           ",
        "q0   : -H-Expectation(Y@Z)-",
        "          |                ",
        "q1   : -H-|----------------",
        "          |                ",
        "q100 : -H-Expectation(Y@Z)-",
        "",
        "T    : |0|  Result Types  |",
    )
    _assert_correct_diagram(circ, expected)


def test_additional_result_types():
    circ = Circuit().h(0).h(1).h(100).state_vector().amplitude(["110", "001"])
    expected = (
        "T    : |0|",
        "          ",
        "q0   : -H-",
        "          ",
        "q1   : -H-",
        "          ",
        "q100 : -H-",
        "",
        "T    : |0|",
        "",
        "Additional result types: StateVector, Amplitude(110,001)",
    )
    _assert_correct_diagram(circ, expected)


def test_multiple_result_types():
    circ = (
        Circuit()
        .cnot(0, 2)
        .cnot(1, 3)
        .h(0)
        .variance(observable=Observable.Y(), target=0)
        .expectation(observable=Observable.Y(), target=2)
        .sample(observable=Observable.Y())
    )
    expected = (
        "T  : | 0 |1|      Result Types      |",
        "                                     ",
        "q0 : -C---H-Variance(Y)----Sample(Y)-",
        "      |                    |         ",
        "q1 : -|-C------------------Sample(Y)-",
        "      | |                  |         ",
        "q2 : -X-|---Expectation(Y)-Sample(Y)-",
        "        |                  |         ",
        "q3 : ---X------------------Sample(Y)-",
        "",
        "T  : | 0 |1|      Result Types      |",
    )
    _assert_correct_diagram(circ, expected)


def test_multiple_result_types_with_state_vector_amplitude():
    circ = (
        Circuit()
        .cnot(0, 2)
        .cnot(1, 3)
        .h(0)
        .variance(observable=Observable.Y(), target=0)
        .expectation(observable=Observable.Y(), target=3)
        .expectation(observable=Observable.Hermitian(np.array([[1.0, 0.0], [0.0, 1.0]])), target=1)
        .amplitude(["0001"])
        .state_vector()
    )
    expected = (
        "T  : | 0 |1|     Result Types     |",
        "                                   ",
        "q0 : -C---H-Variance(Y)------------",
        "      |                            ",
        "q1 : -|-C---Expectation(Hermitian)-",
        "      | |                          ",
        "q2 : -X-|--------------------------",
        "        |                          ",
        "q3 : ---X---Expectation(Y)---------",
        "",
        "T  : | 0 |1|     Result Types     |",
        "",
        "Additional result types: Amplitude(0001), StateVector",
    )
    _assert_correct_diagram(circ, expected)


def test_multiple_result_types_with_custom_hermitian_ascii_symbol():
    herm_matrix = (Observable.Y() @ Observable.Z()).to_matrix()
    circ = (
        Circuit()
        .cnot(0, 2)
        .cnot(1, 3)
        .h(0)
        .variance(observable=Observable.Y(), target=0)
        .expectation(observable=Observable.Y(), target=3)
        .expectation(
            observable=Observable.Hermitian(
                matrix=herm_matrix,
                display_name="MyHerm",
            ),
            target=[1, 2],
        )
    )
    expected = (
        "T  : | 0 |1|   Result Types    |",
        "                                ",
        "q0 : -C---H-Variance(Y)---------",
        "      |                         ",
        "q1 : -|-C---Expectation(MyHerm)-",
        "      | |   |                   ",
        "q2 : -X-|---Expectation(MyHerm)-",
        "        |                       ",
        "q3 : ---X---Expectation(Y)------",
        "",
        "T  : | 0 |1|   Result Types    |",
    )
    _assert_correct_diagram(circ, expected)


def test_noise_1qubit():
    circ = Circuit().h(0).x(1).bit_flip(1, 0.1)
    expected = (
        "T  : |    0    |",
        "                ",
        "q0 : -H---------",
        "                ",
        "q1 : -X-BF(0.1)-",
        "",
        "T  : |    0    |",
    )
    _assert_correct_diagram(circ, expected)


def test_noise_2qubit():
    circ = Circuit().h(1).kraus((0, 2), [np.eye(4)])
    expected = (
        "T  : | 0  |",
        "           ",
        "q0 : ---KR-",
        "        |  ",
        "q1 : -H-|--",
        "        |  ",
        "q2 : ---KR-",
        "",
        "T  : | 0  |",
    )
    _assert_correct_diagram(circ, expected)


def test_noise_multi_probabilities():
    circ = Circuit().h(0).x(1).pauli_channel(1, 0.1, 0.2, 0.3)
    expected = (
        "T  : |        0        |",
        "                        ",
        "q0 : -H-----------------",
        "                        ",
        "q1 : -X-PC(0.1,0.2,0.3)-",
        "",
        "T  : |        0        |",
    )
    _assert_correct_diagram(circ, expected)


def test_noise_multi_probabilities_with_parameter():
    a = FreeParameter("a")
    c = FreeParameter("c")
    d = FreeParameter("d")
    circ = Circuit().h(0).x(1).pauli_channel(1, a, c, d)
    expected = (
        "T  : |     0     |",
        "                  ",
        "q0 : -H-----------",
        "                  ",
        "q1 : -X-PC(a,c,d)-",
        "",
        "T  : |     0     |",
        "",
        "Unassigned parameters: [a, c, d].",
    )
    _assert_correct_diagram(circ, expected)


def test_pulse_gate_1_qubit_circuit():
    circ = (
        Circuit()
        .h(0)
        .pulse_gate(0, PulseSequence().set_phase(Frame("x", Port("px", 1e-9), 1e9, 0), 0))
    )
    expected = (
        "T  : |0|1 |",
        "           ",
        "q0 : -H-PG-",
        "",
        "T  : |0|1 |",
    )
    _assert_correct_diagram(circ, expected)


def test_pulse_gate_multi_qubit_circuit():
    circ = (
        Circuit()
        .h(0)
        .pulse_gate([0, 1], PulseSequence().set_phase(Frame("x", Port("px", 1e-9), 1e9, 0), 0))
    )
    expected = (
        "T  : |0|1 |",
        "           ",
        "q0 : -H-PG-",
        "        |  ",
        "q1 : ---PG-",
        "",
        "T  : |0|1 |",
    )
    _assert_correct_diagram(circ, expected)


def test_circuit_with_nested_target_list():
    circ = (
        Circuit()
        .h(0)
        .h(1)
        .expectation(
            observable=(2 * Observable.Y()) @ (-3 * Observable.I())
            - 0.75 * Observable.Y() @ Observable.Z(),
            target=[[0, 1], [0, 1]],
        )
    )

    expected = (
        "T  : |0|      Result Types      |",
        "                                 ",
        "q0 : -H-Expectation(Hamiltonian)-",
        "        |                        ",
        "q1 : -H-Expectation(Hamiltonian)-",
        "",
        "T  : |0|      Result Types      |",
    )
    _assert_correct_diagram(circ, expected)


def test_hamiltonian():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .rx(0, FreeParameter("theta"))
        .adjoint_gradient(
            4 * (2e-5 * Observable.Z() + 2 * (3 * Observable.X() @ (2 * Observable.Y()))),
            [[0], [1, 2]],
        )
    )
    expected = (
        "T  : |0|1|    2    |        Result Types        |",
        "                                                 ",
        "q0 : -H-C-Rx(theta)-AdjointGradient(Hamiltonian)-",
        "        |           |                            ",
        "q1 : ---X-----------AdjointGradient(Hamiltonian)-",
        "                    |                            ",
        "q2 : ---------------AdjointGradient(Hamiltonian)-",
        "",
        "T  : |0|1|    2    |        Result Types        |",
        "",
        "Unassigned parameters: [theta].",
    )
    _assert_correct_diagram(circ, expected)


def test_power():
    class Foo(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["FOO"])

    class CFoo(Gate):
        def __init__(self):
            super().__init__(qubit_count=2, ascii_symbols=["C", "FOO"])

    class FooFoo(Gate):
        def __init__(self):
            super().__init__(qubit_count=2, ascii_symbols=["FOO", "FOO"])

    circ = Circuit().h(0, power=1).h(1, power=0).h(2, power=-3.14)
    circ.add_instruction(Instruction(Foo(), 0, power=-1))
    circ.add_instruction(Instruction(CFoo(), (0, 1), power=2))
    circ.add_instruction(Instruction(CFoo(), (1, 2), control=0, power=3))
    circ.add_instruction(Instruction(FooFoo(), (1, 2), control=0, power=4))
    expected = (
        "T  : |    0    |   1    |   2   |   3   |   4   |",
        "                                                 ",
        "q0 : -H---------(FOO^-1)-C-------C-------C-------",
        "                         |       |       |       ",
        "q1 : -(H^0)--------------(FOO^2)-C-------(FOO^4)-",
        "                                 |       |       ",
        "q2 : -(H^-3.14)------------------(FOO^3)-(FOO^4)-",
        "",
        "T  : |    0    |   1    |   2   |   3   |   4   |",
    )
    _assert_correct_diagram(circ, expected)


def test_measure():
    circ = Circuit().h(0).cnot(0, 1).measure([0])
    expected = (
        "T  : |0|1|2|",
        "            ",
        "q0 : -H-C-M-",
        "        |   ",
        "q1 : ---X---",
        "",
        "T  : |0|1|2|",
    )
    _assert_correct_diagram(circ, expected)


def test_measure_multiple_targets():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).cnot(2, 3).measure([0, 2, 3])
    expected = (
        "T  : |0|1|2|3|4|",
        "                ",
        "q0 : -H-C-----M-",
        "        |       ",
        "q1 : ---X-C-----",
        "          |     ",
        "q2 : -----X-C-M-",
        "            |   ",
        "q3 : -------X-M-",
        "",
        "T  : |0|1|2|3|4|",
    )
    _assert_correct_diagram(circ, expected)


def test_measure_multiple_instructions_after():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .cnot(1, 2)
        .cnot(2, 3)
        .measure(0)
        .measure(1)
        .h(3)
        .cnot(3, 4)
        .measure([2, 3])
    )
    expected = (
        "T  : |0|1|2|3|4|5|6|",
        "                    ",
        "q0 : -H-C-----M-----",
        "        |           ",
        "q1 : ---X-C---M-----",
        "          |         ",
        "q2 : -----X-C-----M-",
        "            |       ",
        "q3 : -------X-H-C-M-",
        "                |   ",
        "q4 : -----------X---",
        "",
        "T  : |0|1|2|3|4|5|6|",
    )
    _assert_correct_diagram(circ, expected)


def test_measure_with_readout_noise():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .apply_readout_noise(Noise.BitFlip(probability=0.1), target_qubits=1)
        .measure([0, 1])
    )
    expected = (
        "T  : |0|    1    |2|",
        "                    ",
        "q0 : -H-C---------M-",
        "        |           ",
        "q1 : ---X-BF(0.1)-M-",
        "",
        "T  : |0|    1    |2|",
    )
    _assert_correct_diagram(circ, expected)
