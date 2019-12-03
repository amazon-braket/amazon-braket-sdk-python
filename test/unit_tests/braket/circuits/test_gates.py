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

import braket.ir.jaqcd as ir
import numpy as np
import pytest
from braket.circuits import Circuit, Gate, Instruction, QubitSet
from braket.ir.jaqcd.shared_models import (
    Angle,
    DoubleControl,
    DoubleTarget,
    SingleControl,
    SingleTarget,
)

testdata = [
    (Gate.H, "h", ir.H, [SingleTarget]),
    (Gate.I, "i", ir.I, [SingleTarget]),
    (Gate.X, "x", ir.X, [SingleTarget]),
    (Gate.Y, "y", ir.Y, [SingleTarget]),
    (Gate.Z, "z", ir.Z, [SingleTarget]),
    (Gate.S, "s", ir.S, [SingleTarget]),
    (Gate.Si, "si", ir.Si, [SingleTarget]),
    (Gate.T, "t", ir.T, [SingleTarget]),
    (Gate.Ti, "ti", ir.Ti, [SingleTarget]),
    (Gate.V, "v", ir.V, [SingleTarget]),
    (Gate.Vi, "vi", ir.Vi, [SingleTarget]),
    (Gate.Rx, "rx", ir.Rx, [SingleTarget, Angle]),
    (Gate.Ry, "ry", ir.Ry, [SingleTarget, Angle]),
    (Gate.Rz, "rz", ir.Rz, [SingleTarget, Angle]),
    (Gate.CNot, "cnot", ir.CNot, [SingleTarget, SingleControl]),
    (Gate.CCNot, "ccnot", ir.CCNot, [SingleTarget, DoubleControl]),
    (Gate.Swap, "swap", ir.Swap, [DoubleTarget]),
    (Gate.CSwap, "cswap", ir.CSwap, [SingleControl, DoubleTarget]),
    (Gate.ISwap, "iswap", ir.ISwap, [DoubleTarget]),
    (Gate.PSwap, "pswap", ir.PSwap, [DoubleTarget, Angle]),
    (Gate.PhaseShift, "phaseshift", ir.PhaseShift, [SingleTarget, Angle]),
    (Gate.CPhaseShift, "cphaseshift", ir.CPhaseShift, [SingleControl, SingleTarget, Angle]),
    (Gate.CPhaseShift00, "cphaseshift00", ir.CPhaseShift00, [SingleControl, SingleTarget, Angle]),
    (Gate.CPhaseShift01, "cphaseshift01", ir.CPhaseShift01, [SingleControl, SingleTarget, Angle]),
    (Gate.CPhaseShift10, "cphaseshift10", ir.CPhaseShift10, [SingleControl, SingleTarget, Angle]),
    (Gate.CY, "cy", ir.CY, [SingleTarget, SingleControl]),
    (Gate.CZ, "cz", ir.CZ, [SingleTarget, SingleControl]),
    (Gate.XX, "xx", ir.XX, [DoubleTarget, Angle]),
    (Gate.YY, "yy", ir.YY, [DoubleTarget, Angle]),
    (Gate.ZZ, "zz", ir.ZZ, [DoubleTarget, Angle]),
]


def single_target_valid_input():
    return {"target": 2}


def double_target_valid_input():
    return {"targets": [2, 3]}


def angle_valid_input():
    return {"angle": 0.123}


def single_control_valid_input():
    return {"control": 0}


def double_control_valid_input():
    return {"controls": [0, 1]}


valid_ir_switcher = {
    "SingleTarget": single_target_valid_input,
    "DoubleTarget": double_target_valid_input,
    "Angle": angle_valid_input,
    "SingleControl": single_control_valid_input,
    "DoubleControl": double_control_valid_input,
}


def create_valid_ir_input(irsubclasses):
    input = {}
    for subclass in irsubclasses:
        input.update(valid_ir_switcher.get(subclass.__name__, lambda: "Invalid subclass")())
    return input


def create_valid_target_input(irsubclasses):
    input = {}
    qubit_set = []
    # based on the concept that control goes first in target input
    for subclass in irsubclasses:
        if subclass == SingleTarget:
            qubit_set.extend(list(single_target_valid_input().values()))
        elif subclass == DoubleTarget:
            qubit_set.extend(list(double_target_valid_input().values()))
        elif subclass == SingleControl:
            qubit_set = list(single_control_valid_input().values()) + qubit_set
        elif subclass == DoubleControl:
            qubit_set = list(double_control_valid_input().values()) + qubit_set
        elif subclass == Angle:
            pass
        else:
            raise ValueError("Invalid subclass")
    input["target"] = QubitSet(qubit_set)
    return input


def create_valid_gate_class_input(irsubclasses):
    input = {}
    if Angle in irsubclasses:
        input.update(angle_valid_input())
    return input


def create_valid_instruction_input(testclass, irsubclasses):
    input = create_valid_target_input(irsubclasses)
    input["operator"] = testclass(**create_valid_gate_class_input(irsubclasses))
    return input


def calculate_qubit_count(irsubclasses):
    qubit_count = 0
    for subclass in irsubclasses:
        if subclass == SingleTarget:
            qubit_count += 1
        elif subclass == DoubleTarget:
            qubit_count += 2
        elif subclass == SingleControl:
            qubit_count += 1
        elif subclass == DoubleControl:
            qubit_count += 2
        elif subclass == Angle:
            pass
        else:
            raise ValueError("Invalid subclass")
    return qubit_count


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses", testdata)
def test_ir_gate_level(testclass, subroutine_name, irclass, irsubclasses):
    expected = irclass(**create_valid_ir_input(irsubclasses))
    actual = testclass(**create_valid_gate_class_input(irsubclasses)).to_ir(
        **create_valid_target_input(irsubclasses)
    )
    assert actual == expected


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses", testdata)
def test_ir_instruction_level(testclass, subroutine_name, irclass, irsubclasses):
    expected = irclass(**create_valid_ir_input(irsubclasses))
    instruction = Instruction(**create_valid_instruction_input(testclass, irsubclasses))
    actual = instruction.to_ir()
    assert actual == expected


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses", testdata)
def test_gate_subroutine(testclass, subroutine_name, irclass, irsubclasses):
    qubit_count = calculate_qubit_count(irsubclasses)
    subroutine = getattr(Circuit(), subroutine_name)
    assert subroutine(**create_valid_ir_input(irsubclasses)) == Circuit(
        Instruction(**create_valid_instruction_input(testclass, irsubclasses))
    )
    if qubit_count == 1:
        multi_targets = [0, 1, 2]
        instruction_list = []
        for target in multi_targets:
            instruction_list.append(
                Instruction(
                    operator=testclass(**create_valid_gate_class_input(irsubclasses)), target=target
                )
            )
        subroutine = getattr(Circuit(), subroutine_name)
        subroutine_input = {"target": multi_targets}
        if Angle in irsubclasses:
            subroutine_input.update(angle_valid_input())
        assert subroutine(**subroutine_input) == Circuit(instruction_list)


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses", testdata)
def test_gate_to_matrix(testclass, subroutine_name, irclass, irsubclasses):
    gate1 = testclass(**create_valid_gate_class_input(irsubclasses))
    gate2 = testclass(**create_valid_gate_class_input(irsubclasses))
    assert isinstance(gate1.to_matrix(), np.ndarray)
    assert gate1.matrix_equivalence(gate2)
