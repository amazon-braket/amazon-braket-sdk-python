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

import functools

import numpy as np
import pytest

import braket.ir.jaqcd as ir
from braket.circuits import Circuit, FreeParameter, Gate, Instruction, QubitSet
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)
from braket.ir.jaqcd.shared_models import (
    Angle,
    DoubleControl,
    DoubleTarget,
    MultiTarget,
    SingleControl,
    SingleTarget,
    TwoDimensionalMatrix,
)
from braket.pulse import ArbitraryWaveform, Frame, Port, PulseSequence


class NoTarget:
    pass


class DoubleAngle:
    pass


class TripleAngle:
    pass


class SingleNegControlModifier:
    pass


testdata = [
    (Gate.H, "h", ir.H, [SingleTarget], {}),
    (Gate.GPhase, "gphase", None, [NoTarget, Angle], {}),
    (Gate.I, "i", ir.I, [SingleTarget], {}),
    (Gate.X, "x", ir.X, [SingleTarget], {}),
    (Gate.Y, "y", ir.Y, [SingleTarget], {}),
    (Gate.Z, "z", ir.Z, [SingleTarget], {}),
    (Gate.S, "s", ir.S, [SingleTarget], {}),
    (Gate.Si, "si", ir.Si, [SingleTarget], {}),
    (Gate.T, "t", ir.T, [SingleTarget], {}),
    (Gate.Ti, "ti", ir.Ti, [SingleTarget], {}),
    (Gate.V, "v", ir.V, [SingleTarget], {}),
    (Gate.Vi, "vi", ir.Vi, [SingleTarget], {}),
    (Gate.Rx, "rx", ir.Rx, [SingleTarget, Angle], {}),
    (Gate.Ry, "ry", ir.Ry, [SingleTarget, Angle], {}),
    (Gate.Rz, "rz", ir.Rz, [SingleTarget, Angle], {}),
    (Gate.U, "u", None, [SingleTarget, TripleAngle], {}),
    (Gate.CNot, "cnot", ir.CNot, [SingleTarget, SingleControl], {}),
    (Gate.CV, "cv", ir.CV, [SingleTarget, SingleControl], {}),
    (Gate.CCNot, "ccnot", ir.CCNot, [SingleTarget, DoubleControl], {}),
    (Gate.Swap, "swap", ir.Swap, [DoubleTarget], {}),
    (Gate.CSwap, "cswap", ir.CSwap, [SingleControl, DoubleTarget], {}),
    (Gate.ISwap, "iswap", ir.ISwap, [DoubleTarget], {}),
    (Gate.PSwap, "pswap", ir.PSwap, [DoubleTarget, Angle], {}),
    (Gate.XY, "xy", ir.XY, [DoubleTarget, Angle], {}),
    (Gate.PhaseShift, "phaseshift", ir.PhaseShift, [SingleTarget, Angle], {}),
    (Gate.CPhaseShift, "cphaseshift", ir.CPhaseShift, [SingleControl, SingleTarget, Angle], {}),
    (
        Gate.CPhaseShift00,
        "cphaseshift00",
        ir.CPhaseShift00,
        [SingleControl, SingleTarget, Angle],
        {},
    ),
    (
        Gate.CPhaseShift01,
        "cphaseshift01",
        ir.CPhaseShift01,
        [SingleControl, SingleTarget, Angle],
        {},
    ),
    (
        Gate.CPhaseShift10,
        "cphaseshift10",
        ir.CPhaseShift10,
        [SingleControl, SingleTarget, Angle],
        {},
    ),
    (Gate.CY, "cy", ir.CY, [SingleTarget, SingleControl], {}),
    (Gate.CZ, "cz", ir.CZ, [SingleTarget, SingleControl], {}),
    (Gate.ECR, "ecr", ir.ECR, [DoubleTarget], {}),
    (Gate.XX, "xx", ir.XX, [DoubleTarget, Angle], {}),
    (Gate.YY, "yy", ir.YY, [DoubleTarget, Angle], {}),
    (Gate.ZZ, "zz", ir.ZZ, [DoubleTarget, Angle], {}),
    (Gate.GPi, "gpi", None, [SingleTarget, Angle], {}),
    (Gate.GPi2, "gpi2", None, [SingleTarget, Angle], {}),
    (Gate.PRx, "prx", None, [SingleTarget, DoubleAngle], {}),
    (Gate.MS, "ms", None, [DoubleTarget, TripleAngle], {}),
    (
        Gate.Unitary,
        "unitary",
        ir.Unitary,
        [TwoDimensionalMatrix, MultiTarget],
        {"input_type": complex},
    ),
    (
        Gate.Unitary,
        "unitary",
        ir.Unitary,
        [TwoDimensionalMatrix, MultiTarget],
        {"input_type": float},
    ),
    (
        Gate.Unitary,
        "unitary",
        ir.Unitary,
        [TwoDimensionalMatrix, MultiTarget],
        {"input_type": int},
    ),
]

parameterizable_gates = [
    Gate.GPhase,
    Gate.Rx,
    Gate.Ry,
    Gate.Rz,
    Gate.U,
    Gate.PhaseShift,
    Gate.PSwap,
    Gate.XX,
    Gate.XY,
    Gate.YY,
    Gate.ZZ,
    Gate.CPhaseShift,
    Gate.CPhaseShift00,
    Gate.CPhaseShift01,
    Gate.CPhaseShift10,
    Gate.GPi,
    Gate.GPi2,
    Gate.PRx,
    Gate.MS,
]


invalid_unitary_matrices = [
    (np.array([[1]])),
    (np.array([1])),
    (np.array([0, 1, 2])),
    (np.array([[0, 1], [1, 2], [3, 4]])),
    (np.array([[0, 1, 2], [2, 3]], dtype=object)),
    (np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])),
    (np.array([[0, 1], [1, 1]])),
]


def no_target_valid_input(**kwargs):
    return {}


def single_target_valid_input(**kwargs):
    return {"target": 2}


def double_target_valid_ir_input(**kwargs):
    return {"targets": [2, 3]}


def double_target_valid_input(**kwargs):
    return {"target1": 2, "target2": 3}


def angle_valid_input(**kwargs):
    return {"angle": 0.123}


def double_angle_valid_input(**kwargs):
    return {"angle_1": 0.123, "angle_2": 3.567}


def triple_angle_valid_input(**kwargs):
    return {"angle_1": 0.123, "angle_2": 4.567, "angle_3": 8.910}


def single_control_valid_input(**kwargs):
    return {"control": 0}


def single_neg_control_valid_input(**kwargs):
    return {"control": [0], "control_state": [0]}


def double_control_valid_ir_input(**kwargs):
    return {"controls": [0, 1]}


def double_control_valid_input(**kwargs):
    return {"control1": 0, "control2": 1}


def multi_target_valid_input(**kwargs):
    return {"targets": [5]}


def two_dimensional_matrix_valid_ir_input(**kwargs):
    return {"matrix": [[[0, 0], [1, 0]], [[1, 0], [0, 0]]]}


def two_dimensional_matrix_valid_input(**kwargs):
    input_type = kwargs.get("input_type")
    return {"matrix": np.array([[input_type(0), input_type(1)], [input_type(1), input_type(0)]])}


valid_ir_switcher = {
    "NoTarget": no_target_valid_input,
    "SingleTarget": single_target_valid_input,
    "DoubleTarget": double_target_valid_ir_input,
    "Angle": angle_valid_input,
    "DoubleAngle": double_angle_valid_input,
    "TripleAngle": triple_angle_valid_input,
    "SingleControl": single_control_valid_input,
    "SingleNegControlModifier": single_neg_control_valid_input,
    "DoubleControl": double_control_valid_ir_input,
    "MultiTarget": multi_target_valid_input,
    "TwoDimensionalMatrix": two_dimensional_matrix_valid_ir_input,
}

valid_subroutine_switcher = dict(
    valid_ir_switcher,
    **{
        "TwoDimensionalMatrix": two_dimensional_matrix_valid_input,
        "DoubleTarget": double_target_valid_input,
        "DoubleControl": double_control_valid_input,
    },
)


def create_valid_ir_input(irsubclasses):
    input = {}
    for subclass in irsubclasses:
        input |= valid_ir_switcher.get(subclass.__name__, lambda: "Invalid subclass")()
    return input


def create_valid_subroutine_input(irsubclasses, **kwargs):
    input = {}
    for subclass in irsubclasses:
        input |= valid_subroutine_switcher.get(subclass.__name__, lambda: "Invalid subclass")(
            **kwargs
        )
    return input


def create_valid_target_input(irsubclasses):
    qubit_set = []
    control_qubit_set = []
    control_state = None
    # based on the concept that control goes first in target input
    for subclass in irsubclasses:
        if subclass == NoTarget:
            qubit_set.extend(list(no_target_valid_input().values()))
        elif subclass == SingleTarget:
            qubit_set.extend(list(single_target_valid_input().values()))
        elif subclass == DoubleTarget:
            qubit_set.extend(list(double_target_valid_ir_input().values()))
        elif subclass == MultiTarget:
            qubit_set.extend(list(multi_target_valid_input().values()))
        elif subclass == SingleControl:
            qubit_set = list(single_control_valid_input().values()) + qubit_set
        elif subclass == SingleNegControlModifier:
            control_qubit_set = list(single_neg_control_valid_input()["control"])
            control_state = list(single_neg_control_valid_input()["control_state"])
        elif subclass == DoubleControl:
            qubit_set = list(double_control_valid_ir_input().values()) + qubit_set
        elif subclass not in (Angle, TwoDimensionalMatrix, DoubleAngle, TripleAngle):
            raise ValueError("Invalid subclass")
    input = {"target": QubitSet(qubit_set)}
    input["control"] = QubitSet(control_qubit_set)
    input["control_state"] = control_state
    return input


def create_valid_gate_class_input(irsubclasses, **kwargs):
    input = {}
    if Angle in irsubclasses:
        input.update(angle_valid_input())
    if DoubleAngle in irsubclasses:
        input.update(double_angle_valid_input())
    if TripleAngle in irsubclasses:
        input.update(triple_angle_valid_input())
    if TwoDimensionalMatrix in irsubclasses:
        input.update(two_dimensional_matrix_valid_input(**kwargs))
    return input


def create_valid_instruction_input(testclass, irsubclasses, **kwargs):
    input = create_valid_target_input(irsubclasses)
    input["operator"] = testclass(**create_valid_gate_class_input(irsubclasses, **kwargs))
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
        elif subclass == MultiTarget:
            qubit_count += 3
        elif subclass not in (
            NoTarget,
            Angle,
            TwoDimensionalMatrix,
            DoubleAngle,
            TripleAngle,
        ):
            raise ValueError("Invalid subclass")
    return qubit_count


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_ir_gate_level(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    if irclass is not None:
        expected = irclass(**create_valid_ir_input(irsubclasses))
        actual = testclass(**create_valid_gate_class_input(irsubclasses, **kwargs)).to_ir(
            **create_valid_target_input(irsubclasses)
        )
        assert actual == expected


@pytest.mark.parametrize(
    "gate, target, serialization_properties, expected_ir",
    [
        (
            Gate.Rx(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "rx(0.17) q[4];",
        ),
        (
            Gate.Rx(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "rx(0.17) $4;",
        ),
        (
            Gate.X(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "x q[4];",
        ),
        (
            Gate.X(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "x $4;",
        ),
        (
            Gate.Z(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "z q[4];",
        ),
        (
            Gate.Z(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "z $4;",
        ),
        (
            Gate.Y(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "y q[4];",
        ),
        (
            Gate.Y(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "y $4;",
        ),
        (
            Gate.H(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "h q[4];",
        ),
        (
            Gate.H(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "h $4;",
        ),
        (
            Gate.Ry(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "ry(0.17) q[4];",
        ),
        (
            Gate.Ry(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "ry(0.17) $4;",
        ),
        (
            Gate.ZZ(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "zz(0.17) q[4], q[5];",
        ),
        (
            Gate.ZZ(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "zz(0.17) $4, $5;",
        ),
        (
            Gate.I(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "i q[4];",
        ),
        (
            Gate.I(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "i $4;",
        ),
        (
            Gate.V(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "v q[4];",
        ),
        (
            Gate.V(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "v $4;",
        ),
        (
            Gate.CY(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cy q[0], q[1];",
        ),
        (
            Gate.CY(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cy $0, $1;",
        ),
        (
            Gate.Rz(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "rz(0.17) q[4];",
        ),
        (
            Gate.Rz(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "rz(0.17) $4;",
        ),
        (
            Gate.U(angle_1=0.17, angle_2=3.45, angle_3=5.21),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "U(0.17, 3.45, 5.21) q[4];",
        ),
        (
            Gate.U(angle_1=0.17, angle_2=3.45, angle_3=5.21),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "U(0.17, 3.45, 5.21) $4;",
        ),
        (
            Gate.XX(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "xx(0.17) q[4], q[5];",
        ),
        (
            Gate.XX(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "xx(0.17) $4, $5;",
        ),
        (
            Gate.T(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "t q[4];",
        ),
        (
            Gate.T(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "t $4;",
        ),
        (
            Gate.CZ(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cz $0, $1;",
        ),
        (
            Gate.CZ(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cz q[0], q[1];",
        ),
        (
            Gate.YY(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "yy(0.17) q[4], q[5];",
        ),
        (
            Gate.YY(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "yy(0.17) $4, $5;",
        ),
        (
            Gate.XY(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "xy(0.17) q[4], q[5];",
        ),
        (
            Gate.XY(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "xy(0.17) $4, $5;",
        ),
        (
            Gate.ISwap(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "iswap $0, $1;",
        ),
        (
            Gate.ISwap(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "iswap q[0], q[1];",
        ),
        (
            Gate.Swap(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "swap $0, $1;",
        ),
        (
            Gate.Swap(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "swap q[0], q[1];",
        ),
        (
            Gate.ECR(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "ecr $0, $1;",
        ),
        (
            Gate.ECR(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "ecr q[0], q[1];",
        ),
        (
            Gate.CV(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cv $0, $1;",
        ),
        (
            Gate.CV(),
            [0, 1],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cv q[0], q[1];",
        ),
        (
            Gate.Vi(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "vi q[4];",
        ),
        (
            Gate.Vi(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "vi $4;",
        ),
        (
            Gate.CSwap(),
            [0, 1, 2],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cswap q[0], q[1], q[2];",
        ),
        (
            Gate.CSwap(),
            [0, 1, 2],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cswap $0, $1, $2;",
        ),
        (
            Gate.CPhaseShift01(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cphaseshift01(0.17) q[4], q[5];",
        ),
        (
            Gate.CPhaseShift01(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cphaseshift01(0.17) $4, $5;",
        ),
        (
            Gate.CPhaseShift00(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cphaseshift00(0.17) q[4], q[5];",
        ),
        (
            Gate.CPhaseShift00(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cphaseshift00(0.17) $4, $5;",
        ),
        (
            Gate.CPhaseShift(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cphaseshift(0.17) q[4], q[5];",
        ),
        (
            Gate.CPhaseShift(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cphaseshift(0.17) $4, $5;",
        ),
        (
            Gate.S(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "s q[4];",
        ),
        (
            Gate.S(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "s $4;",
        ),
        (
            Gate.Si(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "si q[4];",
        ),
        (
            Gate.Si(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "si $4;",
        ),
        (
            Gate.Ti(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "ti q[4];",
        ),
        (
            Gate.Ti(),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "ti $4;",
        ),
        (
            Gate.PhaseShift(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "phaseshift(0.17) q[4];",
        ),
        (
            Gate.PhaseShift(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "phaseshift(0.17) $4;",
        ),
        (
            Gate.CNot(),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cnot q[4], q[5];",
        ),
        (
            Gate.CNot(),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cnot $4, $5;",
        ),
        (
            Gate.PSwap(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "pswap(0.17) q[4], q[5];",
        ),
        (
            Gate.PSwap(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "pswap(0.17) $4, $5;",
        ),
        (
            Gate.CPhaseShift10(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "cphaseshift10(0.17) q[4], q[5];",
        ),
        (
            Gate.CPhaseShift10(angle=0.17),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "cphaseshift10(0.17) $4, $5;",
        ),
        (
            Gate.CCNot(),
            [4, 5, 6],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "ccnot q[4], q[5], q[6];",
        ),
        (
            Gate.CCNot(),
            [4, 5, 6],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "ccnot $4, $5, $6;",
        ),
        (
            Gate.Unitary(Gate.CCNot().to_matrix()),
            [4, 5, 6],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket unitary(["
            "[1.0, 0, 0, 0, 0, 0, 0, 0], "
            "[0, 1.0, 0, 0, 0, 0, 0, 0], "
            "[0, 0, 1.0, 0, 0, 0, 0, 0], "
            "[0, 0, 0, 1.0, 0, 0, 0, 0], "
            "[0, 0, 0, 0, 1.0, 0, 0, 0], "
            "[0, 0, 0, 0, 0, 1.0, 0, 0], "
            "[0, 0, 0, 0, 0, 0, 0, 1.0], "
            "[0, 0, 0, 0, 0, 0, 1.0, 0]"
            "]) q[4], q[5], q[6]",
        ),
        (
            Gate.Unitary(Gate.CCNot().to_matrix()),
            [4, 5, 6],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "#pragma braket unitary(["
            "[1.0, 0, 0, 0, 0, 0, 0, 0], "
            "[0, 1.0, 0, 0, 0, 0, 0, 0], "
            "[0, 0, 1.0, 0, 0, 0, 0, 0], "
            "[0, 0, 0, 1.0, 0, 0, 0, 0], "
            "[0, 0, 0, 0, 1.0, 0, 0, 0], "
            "[0, 0, 0, 0, 0, 1.0, 0, 0], "
            "[0, 0, 0, 0, 0, 0, 0, 1.0], "
            "[0, 0, 0, 0, 0, 0, 1.0, 0]"
            "]) $4, $5, $6",
        ),
        (
            Gate.Unitary(np.round(Gate.ECR().to_matrix(), 8)),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket unitary(["
            "[0, 0, 0.70710678, 0.70710678im], "
            "[0, 0, 0.70710678im, 0.70710678], "
            "[0.70710678, -0.70710678im, 0, 0], "
            "[-0.70710678im, 0.70710678, 0, 0]"
            "]) q[4], q[5]",
        ),
        (
            Gate.Unitary(np.round(Gate.ECR().to_matrix(), 8)),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "#pragma braket unitary(["
            "[0, 0, 0.70710678, 0.70710678im], "
            "[0, 0, 0.70710678im, 0.70710678], "
            "[0.70710678, -0.70710678im, 0, 0], "
            "[-0.70710678im, 0.70710678, 0, 0]"
            "]) $4, $5",
        ),
        (
            Gate.Unitary(np.round(Gate.T().to_matrix(), 8)),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket unitary([[1.0, 0], [0, 0.70710678 + 0.70710678im]]) q[4]",
        ),
        (
            Gate.Unitary(np.round(Gate.T().to_matrix(), 8)),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "#pragma braket unitary([[1.0, 0], [0, 0.70710678 + 0.70710678im]]) $4",
        ),
        (
            Gate.Unitary(np.array([[1.0, 0], [0, 0.70710678 - 0.70710678j]])),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket unitary([[1.0, 0], [0, 0.70710678 - 0.70710678im]]) q[4]",
        ),
        (
            Gate.PulseGate(
                PulseSequence().play(
                    Frame("user_frame", Port("device_port_x", 1e-9), 1e9),
                    ArbitraryWaveform([1, 2], "arb_wf"),
                ),
                1,
            ),
            [0],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "\n".join(["cal {", "    play(user_frame, arb_wf);", "}"]),
        ),
        (
            Gate.GPi(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "gpi(0.17) q[4];",
        ),
        (
            Gate.GPi(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "gpi(0.17) $4;",
        ),
        (
            Gate.GPi2(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "gpi2(0.17) q[4];",
        ),
        (
            Gate.GPi2(angle=0.17),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "gpi2(0.17) $4;",
        ),
        (
            Gate.PRx(angle_1=0.17, angle_2=3.45),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "prx(0.17, 3.45) q[4];",
        ),
        (
            Gate.PRx(angle_1=0.17, angle_2=3.45),
            [4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "prx(0.17, 3.45) $4;",
        ),
        (
            Gate.MS(angle_1=0.17, angle_2=3.45),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            f"ms(0.17, 3.45, {np.pi / 2}) q[4], q[5];",
        ),
        (
            Gate.MS(angle_1=0.17, angle_2=3.45),
            [4, 5],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            f"ms(0.17, 3.45, {np.pi / 2}) $4, $5;",
        ),
    ],
)
def test_gate_to_ir_openqasm(gate, target, serialization_properties, expected_ir):
    assert (
        gate.to_ir(
            target, ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )
        == expected_ir
    )


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_ir_instruction_level(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    if irclass is not None:
        expected = irclass(**create_valid_ir_input(irsubclasses))
        instruction = Instruction(
            **create_valid_instruction_input(testclass, irsubclasses, **kwargs)
        )
        actual = instruction.to_ir()
        assert actual == expected


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_gate_subroutine(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    qubit_count = calculate_qubit_count(irsubclasses)
    subroutine = getattr(Circuit(), subroutine_name)
    assert subroutine(**create_valid_subroutine_input(irsubclasses, **kwargs)) == Circuit(
        Instruction(**create_valid_instruction_input(testclass, irsubclasses, **kwargs))
    )
    if qubit_count == 1:
        multi_targets = [0, 1, 2]
        instruction_list = [
            Instruction(
                operator=testclass(**create_valid_gate_class_input(irsubclasses, **kwargs)),
                target=target,
            )
            for target in multi_targets
        ]
        subroutine = getattr(Circuit(), subroutine_name)
        subroutine_input = {"target": multi_targets}
        if Angle in irsubclasses:
            subroutine_input.update(angle_valid_input())
        if DoubleAngle in irsubclasses:
            subroutine_input.update(double_angle_valid_input())
        if TripleAngle in irsubclasses:
            subroutine_input.update(triple_angle_valid_input())
        assert subroutine(**subroutine_input) == Circuit(instruction_list)


@pytest.mark.parametrize(
    "control, control_state, instruction_set",
    [
        (
            2,
            None,
            Instruction(**create_valid_instruction_input(Gate.PhaseShift, [SingleTarget, Angle])),
        ),
        (
            2,
            [0],
            [
                Instruction(operator=Gate.X(), target=2),
                Instruction(
                    **create_valid_instruction_input(Gate.PhaseShift, [SingleTarget, Angle])
                ),
                Instruction(operator=Gate.X(), target=2),
            ],
        ),
        (
            [0, 2],
            [0, 1],
            Instruction(
                **create_valid_instruction_input(
                    Gate.PhaseShift, [SingleTarget, SingleNegControlModifier, Angle]
                )
            ),
        ),
    ],
)
def test_control_gphase_subroutine(control, control_state, instruction_set):
    subroutine = getattr(Circuit(), "gphase")
    assert subroutine(angle=0.123, control=control, control_state=control_state) == Circuit(
        instruction_set
    )


def test_angle_gphase_is_none():
    with pytest.raises(ValueError, match="angle must not be None"):
        Gate.GPhase(angle=None)


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_gate_adjoint_expansion_correct(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    gate = testclass(**create_valid_gate_class_input(irsubclasses, **kwargs))
    matrices = [elem.to_matrix() for elem in gate.adjoint()]
    matrices.append(gate.to_matrix())
    identity = np.eye(2**gate.qubit_count)
    assert np.allclose(functools.reduce(lambda a, b: a @ b, matrices), identity)


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_gate_to_matrix(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    gate1 = testclass(**create_valid_gate_class_input(irsubclasses, **kwargs))
    gate2 = testclass(**create_valid_gate_class_input(irsubclasses, **kwargs))
    assert isinstance(gate1.to_matrix(), np.ndarray)
    assert gate1.matrix_equivalence(gate2)


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_fixed_qubit_count(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    fixed_qubit_count = testclass.fixed_qubit_count()
    if fixed_qubit_count is not NotImplemented:
        gate = testclass(**create_valid_gate_class_input(irsubclasses, **kwargs))
        assert gate.qubit_count == fixed_qubit_count


# Additional Unitary gate tests


def test_equality():
    u1 = Gate.Unitary(np.array([[0 + 0j, 1 + 0j], [1 + 0j, 0 + 0j]]))
    u2 = Gate.Unitary(np.array([[0, 1], [1, 0]], dtype=np.float32), display_name=["u2"])
    other_gate = Gate.Unitary(np.array([[1, 0], [0, 1]]))
    non_gate = "non gate"

    assert u1 == u2
    assert u1 is not u2
    assert u1 != other_gate
    assert u1 != non_gate


def test_free_param_equality():
    param1 = FreeParameter("theta")
    param2 = FreeParameter("phi")
    rx1 = Gate.Rx(param1)
    rx2 = Gate.Rx(param1)
    other_gate = Gate.Rx(param2)

    assert rx1 == rx2
    assert rx1 is not rx2
    assert rx1 != other_gate
    assert rx1 != param1


def test_large_unitary():
    matrix = np.eye(16, dtype=np.float32)
    # Permute rows of matrix
    matrix[[*range(16)]] = matrix[[(i + 1) % 16 for i in range(16)]]
    unitary = Gate.Unitary(matrix)
    assert unitary.qubit_count == 4


@pytest.mark.parametrize("gate", parameterizable_gates)
def test_bind_values(gate):
    double_angled = gate.__name__ in ["PRx"]
    triple_angled = gate.__name__ in ("MS", "U")
    num_params = 1
    if triple_angled:
        num_params = 3
    elif double_angled:
        num_params = 2
    thetas = [FreeParameter(f"theta_{i}") for i in range(num_params)]
    mapping = {f"theta_{i}": i for i in range(num_params)}
    param_gate = gate(*thetas)
    new_gate = param_gate.bind_values(**mapping)
    expected = gate(*range(num_params))

    assert type(new_gate) is type(param_gate) and new_gate == expected
    if triple_angled:
        for angle in new_gate.angle_1, new_gate.angle_2, new_gate.angle_3:
            assert isinstance(angle, float)
    elif double_angled:
        for angle in new_gate.angle_1, new_gate.angle_2:
            assert isinstance(angle, float)
    else:
        assert isinstance(new_gate.angle, float)


def test_bind_values_pulse_gate():
    qubit_count = 1
    frame = Frame("user_frame", Port("device_port_x", 1e-9), 1e9)
    gate = Gate.PulseGate(
        PulseSequence()
        .set_frequency(frame, FreeParameter("a") + FreeParameter("c"))
        .delay(frame, FreeParameter("d")),
        qubit_count,
    )

    def to_ir(pulse_gate):
        return pulse_gate.to_ir(range(pulse_gate.qubit_count), IRType.OPENQASM)

    a = 3
    a_bound = gate.bind_values(a=a)
    a_bound_ir = to_ir(a_bound)

    assert a_bound_ir == "\n".join([
        "cal {",
        "    set_frequency(user_frame, 3.0 + c);",
        "    delay[d * 1s] user_frame;",
        "}",
    ])

    assert a_bound_ir == to_ir(
        Gate.PulseGate(gate.pulse_sequence.make_bound_pulse_sequence({"a": a}), qubit_count)
    )
    assert a_bound_ir != to_ir(gate)

    c = 4e-6
    ac_bound = a_bound.bind_values(c=c)
    ac_bound_ir = to_ir(ac_bound)
    assert ac_bound_ir == to_ir(
        Gate.PulseGate(a_bound.pulse_sequence.make_bound_pulse_sequence({"c": c}), qubit_count)
    )
    assert ac_bound_ir != a_bound_ir


def test_pulse_gate_capture_throws():
    with pytest.raises(ValueError):
        Circuit().pulse_gate(
            0, PulseSequence().capture_v0(Frame("user_frame", Port("device_port_x", dt=1e-9), 1e9))
        )


@pytest.mark.parametrize("matrix", invalid_unitary_matrices)
def test_unitary_invalid_matrix(matrix):
    with pytest.raises(ValueError):
        Gate.Unitary(matrix=matrix)


def test_unitary_matrix_target_size_mismatch():
    with pytest.raises(ValueError):
        Circuit().unitary(
            matrix=np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]), targets=[0]
        )


def test_pulse_gate_to_matrix():
    with pytest.raises(NotImplementedError):
        Gate.PulseGate(
            PulseSequence().play(
                Frame("user_frame", Port("device_port_x", 1e-9), 1e9),
                ArbitraryWaveform([1, 2], "arb_wf"),
            ),
            1,
        ).to_matrix()


@pytest.mark.parametrize(
    "gate, target, control, control_state, expected_ir",
    (
        (Gate.H(), QubitSet(0), QubitSet(1), None, "ctrl @ h q[1], q[0];"),
        (Gate.H(), QubitSet(0), QubitSet([1, 2]), None, "ctrl(2) @ h q[1], q[2], q[0];"),
        (Gate.Ry(angle=1.23), QubitSet(0), QubitSet([2]), None, "ctrl @ ry(1.23) q[2], q[0];"),
        (
            Gate.MS(angle_1=0.17, angle_2=3.45),
            QubitSet(0),
            QubitSet([1, 2]),
            None,
            f"ctrl(2) @ ms(0.17, 3.45, {np.pi / 2}) q[1], q[2], q[0];",
        ),
        (
            Gate.CCNot(),
            QubitSet([0, 1, 2]),
            QubitSet([3, 4]),
            None,
            "ctrl(2) @ ccnot q[3], q[4], q[0], q[1], q[2];",
        ),
        (
            Gate.Z(),
            QubitSet([0]),
            QubitSet([1, 2, 3, 4, 5, 6, 7]),
            [1, 1, 1, 0, 0, 1, 0],
            "ctrl(3) @ negctrl(2) @ ctrl @ negctrl @ "
            "z q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[0];",
        ),
        (
            Gate.Z(),
            QubitSet([0]),
            QubitSet([1, 2, 3, 4, 5, 6, 7]),
            "1110010",
            "ctrl(3) @ negctrl(2) @ ctrl @ negctrl @ "
            "z q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[0];",
        ),
        (
            Gate.Z(),
            QubitSet([0]),
            QubitSet([1, 2, 3, 4, 5, 6, 7]),
            114,
            "ctrl(3) @ negctrl(2) @ ctrl @ negctrl @ "
            "z q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[0];",
        ),
        (
            Gate.Z(),
            QubitSet([0]),
            QubitSet([1, 2, 3]),
            [1, 0],
            "negctrl @ ctrl @ negctrl @ z q[1], q[2], q[3], q[0];",
        ),
        (
            Gate.Z(),
            QubitSet([0]),
            QubitSet([1, 2, 3]),
            "10",
            "negctrl @ ctrl @ negctrl @ z q[1], q[2], q[3], q[0];",
        ),
        (
            Gate.GPhase(0.3),
            QubitSet([]),
            QubitSet([1]),
            "1",
            "ctrl @ gphase(0.3) q[1];",
        ),
    ),
)
def test_gate_control(gate, target, control, control_state, expected_ir):
    serialization_properties = OpenQASMSerializationProperties(
        qubit_reference_type=QubitReferenceType.VIRTUAL
    )
    assert (
        gate.to_ir(
            target,
            control=control,
            control_state=control_state,
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        )
        == expected_ir
    )


@pytest.mark.parametrize(
    "control, control_state, error_string",
    (
        (
            [0, 1],
            [1, 0, 1],
            "State value represents a binary sequence of length greater "
            "than the specified number of qubits.",
        ),
        (
            [0, 1],
            "101",
            "State value represents a binary sequence of length greater "
            "than the specified number of qubits.",
        ),
        (
            [0, 1],
            5,
            "State value represents a binary sequence of length greater "
            "than the specified number of qubits.",
        ),
    ),
)
def test_gate_control_invalid_state(control, control_state, error_string):
    with pytest.raises(ValueError, match=error_string):
        Gate.X().to_ir(
            target=[0],
            control=control,
            control_state=control_state,
            ir_type=IRType.OPENQASM,
            serialization_properties=OpenQASMSerializationProperties(
                qubit_reference_type=QubitReferenceType.VIRTUAL
            ),
        )


@pytest.mark.parametrize(
    "gate, target, power, expected_ir",
    (
        (Gate.H(), QubitSet(0), 2, "pow(2) @ h q[0];"),
        (Gate.H(), QubitSet(0), 2.0, "pow(2.0) @ h q[0];"),
        (Gate.H(), QubitSet(0), 2.5, "pow(2.5) @ h q[0];"),
        (Gate.H(), QubitSet(0), 0, "pow(0) @ h q[0];"),
        (Gate.H(), QubitSet(0), -2, "inv @ pow(2) @ h q[0];"),
        (Gate.H(), QubitSet(0), -2.0, "inv @ pow(2.0) @ h q[0];"),
        (Gate.H(), QubitSet(0), -2.5, "inv @ pow(2.5) @ h q[0];"),
    ),
)
def test_gate_power(gate, target, power, expected_ir):
    serialization_properties = OpenQASMSerializationProperties(
        qubit_reference_type=QubitReferenceType.VIRTUAL
    )
    assert (
        gate.to_ir(
            target,
            power=power,
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        )
        == expected_ir
    )


def test_hash():
    assert hash(Gate.Unitary(Gate.CCNot().to_matrix())) == hash(
        Gate.Unitary(Gate.CCNot().to_matrix())
    )
