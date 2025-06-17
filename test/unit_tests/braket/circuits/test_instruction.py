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

from braket.circuits import Gate, Instruction, Noise, Qubit, QubitSet, compiler_directives
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)


@pytest.fixture
def instr():
    return Instruction(Gate.H(), 0)


@pytest.fixture
def cnot():
    return Instruction(Gate.CNot(), [0, 1])


@pytest.fixture
def ccry():
    return Instruction(Gate.Ry(1.23), 0, control=[1, 2])


def test_empty_operator():
    with pytest.raises(ValueError):
        Instruction(None, target=0)


def test_non_matching_qubit_set_and_qubit_count():
    with pytest.raises(ValueError):
        Instruction(Gate.CNot(), target=[0, 0])


def test_init_with_qubits():
    target = QubitSet([0, 1])
    instr = Instruction(Gate.CNot(), target)
    assert instr.target == target


def test_init_with_qubit():
    target = Qubit(0)
    instr = Instruction(Gate.H(), target)
    assert instr.target == QubitSet(0)


def test_init_with_int():
    target = 0
    instr = Instruction(Gate.H(), target)
    assert instr.target == QubitSet(0)


def test_init_with_sequence():
    target = [0, Qubit(1)]
    instr = Instruction(Gate.CNot(), target)
    assert instr.target == QubitSet([0, 1])


def test_getters():
    target = [0, 1]
    operator = Gate.CNot()
    instr = Instruction(operator, target)

    assert instr.operator == operator
    assert instr.target == QubitSet([0, 1])


def test_operator_setter(instr):
    with pytest.raises(AttributeError):
        instr.operator = Gate.H()


def test_target_setter(instr):
    with pytest.raises(AttributeError):
        instr.target = QubitSet(0)


def test_adjoint_gate():
    instr = Instruction(Gate.S(), 0)
    adj = instr.adjoint()
    assert adj == [Instruction(Gate.Si(), 0)]


def test_adjoint_compiler_directive():
    instr = Instruction(compiler_directives.StartVerbatimBox()).adjoint()
    assert instr == [Instruction(compiler_directives.EndVerbatimBox())]


def test_adjoint_unsupported():
    with pytest.raises(NotImplementedError):
        Instruction(Noise.BitFlip(0.1), 0).adjoint()


def test_str(instr):
    expected = (
        f"Instruction('operator': {instr.operator}, "
        f"'target': {instr.target}, "
        f"'control': {instr.control}, "
        f"'control_state': {instr.control_state.as_tuple}, "
        f"'power': {instr.power})"
    )
    assert str(instr) == expected


def test_equality():
    instr_1 = Instruction(Gate.H(), 0)
    instr_2 = Instruction(Gate.H(), 0)
    other_instr = Instruction(Gate.CNot(), [0, 1])
    non_instr = "non instruction"

    assert instr_1 == instr_2
    assert instr_1 is not instr_2
    assert instr_1 != other_instr
    assert instr_1 != non_instr


def test_to_ir():
    expected_target = QubitSet([0, 1])
    expected_ir = "foo bar value"
    expected_ir_type = IRType.OPENQASM
    expected_serialization_properties = OpenQASMSerializationProperties(
        qubit_reference_type=QubitReferenceType.PHYSICAL
    )

    class FooGate(Gate):
        def __init__(self):
            super().__init__(qubit_count=2, ascii_symbols=["foo", "bar"])

        def to_ir(self, target, ir_type, serialization_properties):
            assert target == expected_target
            assert ir_type == expected_ir_type
            assert serialization_properties == expected_serialization_properties
            return expected_ir

    instr = Instruction(FooGate(), expected_target)
    assert instr.to_ir(expected_ir_type, expected_serialization_properties) == expected_ir


def test_copy_creates_new_object(instr):
    copy = instr.copy()
    assert copy == instr
    assert copy is not instr


def test_copy_with_mapping(cnot):
    target_mapping = {0: 10, 1: 11}
    expected = Instruction(Gate.CNot(), [10, 11])
    assert cnot.copy(target_mapping=target_mapping) == expected


def test_copy_with_control_mapping(ccry):
    control_mapping = {1: 10, 2: 11}
    expected = Instruction(Gate.Ry(1.23), target=1, control=[10, 11])
    assert ccry.copy(target=1, control_mapping=control_mapping) == expected


def test_copy_with_target(cnot):
    target = [10, 11]
    expected = Instruction(Gate.CNot(), target)
    assert cnot.copy(target=target) == expected


def test_copy_with_control(ccry):
    control = [10, 11]
    expected = Instruction(Gate.Ry(1.23), 3, control=control)
    assert ccry.copy(target=3, control=control) == expected


def test_copy_with_target_and_mapping(instr):
    cant_do_both = "Only 'target_mapping' or 'target' can be supplied, but not both."
    with pytest.raises(TypeError, match=cant_do_both):
        instr.copy(target=[10], target_mapping={0: 10})


def test_copy_with_control_target_and_mapping(instr):
    cant_do_both = "Only 'control_mapping' or 'control' can be supplied, but not both."
    with pytest.raises(TypeError, match=cant_do_both):
        instr.copy(target=[10], control=[10], control_mapping={0: 10})


def test_pow(instr):
    assert instr.power == 1
    cubed = instr**3
    assert instr.power == 1
    assert cubed.power == 3
    then_squared = cubed**2
    assert cubed.power == 3
    assert then_squared.power == 6
    modded = then_squared.__pow__(6, 5)
    assert modded.power == 1
