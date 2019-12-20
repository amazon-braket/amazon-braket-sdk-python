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

from unittest.mock import Mock

import braket.ir.jaqcd as jaqcd
import numpy as np
import pytest
from braket.circuits import (
    AsciiCircuitDiagram,
    Circuit,
    Gate,
    Instruction,
    Moments,
    QubitSet,
    circuit,
)


@pytest.fixture
def cnot():
    return Circuit().add_instruction(Instruction(Gate.CNot(), [0, 1]))


@pytest.fixture
def cnot_instr():
    return Instruction(Gate.CNot(), [0, 1])


@pytest.fixture
def h():
    return Circuit().add_instruction(Instruction(Gate.H(), 0))


@pytest.fixture
def h_instr():
    return Instruction(Gate.H(), 0)


@pytest.fixture
def bell_pair():
    return (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
    )


def test_repr(h):
    expected = f"Circuit('instructions': {list(h.instructions)})"
    assert repr(h) == expected


def test_str(h):
    expected = AsciiCircuitDiagram.build_diagram(h)
    assert str(h) == expected


def test_equality():
    circ_1 = Circuit().h(0)
    circ_2 = Circuit().h(0)
    other_circ = Circuit().h(1)
    non_circ = "non circuit"

    assert circ_1 == circ_2
    assert circ_1 is not circ_2
    assert circ_1 != other_circ
    assert circ_1 != non_circ


def test_add_instruction_default(cnot_instr):
    circ = Circuit().add_instruction(cnot_instr)
    assert list(circ.instructions) == [cnot_instr]


def test_add_instruction_with_mapping(cnot_instr):
    expected = [Instruction(Gate.CNot(), [10, 11])]
    circ = Circuit().add_instruction(cnot_instr, target_mapping={0: 10, 1: 11})
    assert list(circ.instructions) == expected


def test_add_instruction_with_target(cnot_instr):
    expected = [Instruction(Gate.CNot(), [10, 11])]
    circ = Circuit().add_instruction(cnot_instr, target=[10, 11])
    assert list(circ.instructions) == expected


def test_add_multiple_single_qubit_instruction(h_instr):
    circ = Circuit().add_instruction(h_instr, target=[0, 1, 2, 3])
    expected = Circuit().h(0).h(1).h(2).h(3)
    assert circ == expected


@pytest.mark.xfail(raises=TypeError)
def test_add_instruction_with_target_and_mapping(h):
    Circuit().add_instruction(h, target=[10], target_mapping={0: 10})


def test_add_circuit_default(bell_pair):
    circ = Circuit().add_circuit(bell_pair)
    assert circ == bell_pair


def test_add_circuit_with_mapping(bell_pair):
    circ = Circuit().add_circuit(bell_pair, target_mapping={0: 10, 1: 11})
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 10))
        .add_instruction(Instruction(Gate.CNot(), [10, 11]))
    )
    assert circ == expected


def test_add_circuit_with_target(bell_pair):
    circ = Circuit().add_circuit(bell_pair, target=[10, 11])
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 10))
        .add_instruction(Instruction(Gate.CNot(), [10, 11]))
    )
    assert circ == expected


def test_add_circuit_with_target_and_non_continuous_qubits():
    widget = Circuit().h(5).h(50).h(100)
    circ = Circuit().add_circuit(widget, target=[1, 3, 5])
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 1))
        .add_instruction(Instruction(Gate.H(), 3))
        .add_instruction(Instruction(Gate.H(), 5))
    )
    assert circ == expected


@pytest.mark.xfail(raises=TypeError)
def test_add_circuit_with_target_and_mapping(h):
    Circuit().add_circuit(h, target=[10], target_mapping={0: 10})


def test_add_with_instruction_with_default(cnot_instr):
    circ = Circuit().add(cnot_instr)
    assert circ == Circuit().add_instruction(cnot_instr)


def test_add_with_instruction_with_mapping(cnot_instr):
    target_mapping = {0: 10, 1: 11}
    circ = Circuit().add(cnot_instr, target_mapping=target_mapping)
    expected = Circuit().add_instruction(cnot_instr, target_mapping=target_mapping)
    assert circ == expected


def test_add_with_instruction_with_target(cnot_instr):
    target = [10, 11]
    circ = Circuit().add(cnot_instr, target=target)
    expected = Circuit().add_instruction(cnot_instr, target=target)
    assert circ == expected


def test_add_with_circuit_with_default(bell_pair):
    circ = Circuit().add(bell_pair)
    assert circ == Circuit().add_circuit(bell_pair)


def test_add_with_circuit_with_mapping(bell_pair):
    target_mapping = {0: 10, 1: 11}
    circ = Circuit().add(bell_pair, target_mapping=target_mapping)
    expected = Circuit().add_circuit(bell_pair, target_mapping=target_mapping)
    assert circ == expected


def test_add_with_circuit_with_target(bell_pair):
    target = [10, 11]
    circ = Circuit().add(bell_pair, target=target)
    expected = Circuit().add_circuit(bell_pair, target=target)
    assert circ == expected


def test_iadd_operator(cnot_instr, h):
    circ = Circuit()
    circ += h
    circ += cnot_instr
    circ += [h, cnot_instr]

    assert circ == Circuit().add(h).add(cnot_instr).add(h).add(cnot_instr)


def test_add_operator(h, cnot, bell_pair):
    addition = h + bell_pair + h + h
    expected = Circuit().add(h).add(bell_pair).add(h).add(h)

    assert addition == expected
    assert addition != (h + h + bell_pair + h)


@pytest.mark.xfail(raises=TypeError)
def test_iadd_with_unknown_type(h):
    h += 100


def test_subroutine_register():
    # register a private method to avoid Sphinx docs picking this up
    @circuit.subroutine(register=True)
    def _foo(target):
        """this docstring will be added to the registered attribute"""
        return Instruction(Gate.H(), target)

    circ = Circuit()._foo(0)
    assert circ == Circuit(Instruction(Gate.H(), 0))
    assert Circuit._foo.__doc__ == _foo.__doc__


def test_subroutine_returns_circuit():
    @circuit.subroutine()
    def foo(target):
        return Circuit().add(Instruction(Gate.H(), 0))

    circ = Circuit().add(foo, 0)
    assert circ == Circuit(Instruction(Gate.H(), 0))


def test_subroutine_returns_instruction():
    @circuit.subroutine()
    def foo(target):
        return Instruction(Gate.H(), 0)

    circ = Circuit().add(foo, 0)
    assert circ == Circuit(Instruction(Gate.H(), 0))


def test_subroutine_returns_iterable():
    @circuit.subroutine()
    def foo(target):
        for qubit in range(1):
            yield Instruction(Gate.H(), qubit)

    circ = Circuit().add(foo, 0)
    assert circ == Circuit(Instruction(Gate.H(), 0))


def test_subroutine_nested():
    @circuit.subroutine()
    def h(target):
        for qubit in target:
            yield Instruction(Gate.H(), qubit)

    @circuit.subroutine()
    def h_nested(target):
        for qubit in target:
            yield h(target)

    circ = Circuit().add(h_nested, [0, 1])
    expected = Circuit([Instruction(Gate.H(), j) for i in range(2) for j in range(2)])
    assert circ == expected


def test_ir_empty_instructions():
    circ = Circuit()
    assert circ.to_ir() == jaqcd.Program(instructions=[])


def test_ir_non_empty_instructions():
    circ = Circuit().h(0).cnot(0, 1)
    expected = jaqcd.Program(instructions=[jaqcd.H(target=0), jaqcd.CNot(control=0, target=1)])
    assert circ.to_ir() == expected


def test_depth_getter(h):
    assert h.depth is h._moments.depth


@pytest.mark.xfail(raises=AttributeError)
def test_depth_setter(h):
    h.depth = 1


def test_instructions_getter(h):
    assert list(h.instructions) == list(h._moments.values())


@pytest.mark.xfail(raises=AttributeError)
def test_instructions_setter(h, h_instr):
    h.instructions = iter([h_instr])


def test_moments_getter(h):
    assert h.moments is h._moments


@pytest.mark.xfail(raises=AttributeError)
def test_moments_setter(h):
    h.moments = Moments()


def test_qubit_count_getter(h):
    assert h.qubit_count is h._moments.qubit_count


@pytest.mark.xfail(raises=AttributeError)
def test_qubit_count_setter(h):
    h.qubit_count = 1


def test_qubits_getter(h):
    assert h.qubits == h._moments.qubits
    assert h.qubits is not h._moments.qubits


@pytest.mark.xfail(raises=AttributeError)
def test_qubits_setter(h):
    h.qubits = QubitSet(1)


def test_diagram(h):
    expected = "foo bar diagram"
    mock_diagram = Mock()
    mock_diagram.build_diagram.return_value = expected

    assert h.diagram(mock_diagram) == expected
    mock_diagram.build_diagram.assert_called_with(h)


def test_to_matrix_single_qubit_gate(h):
    expected_matrix = Gate.H().to_matrix()
    assert (expected_matrix == h.to_matrix()).all()


def test_to_matrix_two_single_qubit_gates():
    circ = Circuit().h(0).i(1)
    expected_matrix = np.kron(Gate.H().to_matrix(), Gate.I().to_matrix())
    assert (expected_matrix == circ.to_matrix()).all()


def test_to_matrix_multi_qubit_gates():
    circ = Circuit().cnot(0, 1).i(2)
    expected_matrix = np.kron(Gate.CNot().to_matrix(), Gate.I().to_matrix())
    assert (expected_matrix == circ.to_matrix()).all()
