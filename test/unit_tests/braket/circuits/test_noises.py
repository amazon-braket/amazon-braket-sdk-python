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

import json

import numpy as np
import pytest

import braket.ir.jaqcd as ir
from braket.circuits import Circuit, Instruction, Noise, QubitSet
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)
from braket.ir.jaqcd.shared_models import (
    DampingProbability,
    DampingSingleProbability,
    DoubleControl,
    DoubleTarget,
    MultiProbability,
    MultiTarget,
    SingleControl,
    SingleProbability,
    SingleProbability_34,
    SingleProbability_1516,
    SingleTarget,
    TripleProbability,
    TwoDimensionalMatrixList,
)

testdata = [
    (Noise.BitFlip, "bit_flip", ir.BitFlip, [SingleTarget, SingleProbability], {}),
    (Noise.PhaseFlip, "phase_flip", ir.PhaseFlip, [SingleTarget, SingleProbability], {}),
    (Noise.Depolarizing, "depolarizing", ir.Depolarizing, [SingleTarget, SingleProbability_34], {}),
    (
        Noise.AmplitudeDamping,
        "amplitude_damping",
        ir.AmplitudeDamping,
        [SingleTarget, DampingProbability],
        {},
    ),
    (
        Noise.GeneralizedAmplitudeDamping,
        "generalized_amplitude_damping",
        ir.GeneralizedAmplitudeDamping,
        [SingleTarget, DampingProbability, DampingSingleProbability],
        {},
    ),
    (
        Noise.PhaseDamping,
        "phase_damping",
        ir.PhaseDamping,
        [SingleTarget, DampingProbability],
        {},
    ),
    (
        Noise.TwoQubitDepolarizing,
        "two_qubit_depolarizing",
        ir.TwoQubitDepolarizing,
        [DoubleTarget, SingleProbability_1516],
        {},
    ),
    (
        Noise.TwoQubitDephasing,
        "two_qubit_dephasing",
        ir.TwoQubitDephasing,
        [DoubleTarget, SingleProbability_34],
        {},
    ),
    (
        Noise.TwoQubitPauliChannel,
        "two_qubit_pauli_channel",
        ir.MultiQubitPauliChannel,
        [DoubleTarget, MultiProbability],
        {},
    ),
    (
        Noise.PauliChannel,
        "pauli_channel",
        ir.PauliChannel,
        [SingleTarget, TripleProbability],
        {},
    ),
    (
        Noise.Kraus,
        "kraus",
        ir.Kraus,
        [TwoDimensionalMatrixList, MultiTarget],
        {"input_type": complex},
    ),
    (
        Noise.Kraus,
        "kraus",
        ir.Kraus,
        [TwoDimensionalMatrixList, MultiTarget],
        {"input_type": float},
    ),
    (
        Noise.Kraus,
        "kraus",
        ir.Kraus,
        [TwoDimensionalMatrixList, MultiTarget],
        {"input_type": int},
    ),
]


invalid_kraus_matrices = [
    ([np.array([[1]])]),
    ([np.array([1])]),
    ([np.array([0, 1, 2])]),
    ([np.array([[0, 1], [1, 2], [3, 4]])]),
    ([np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])]),
    ([np.array([[0, 1], [1, 1]])]),
    ([np.array([[1, 0], [0, 1]]), np.array([[0, 1], [1, 0]])]),
    ([np.array([[1, 0], [0, 1]]) * np.sqrt(0.5), np.eye(4) * np.sqrt(0.5)]),
    ([np.eye(8)]),
    ([np.eye(2), np.eye(2), np.eye(2), np.eye(2), np.eye(2)]),
]


def single_target_valid_input(**kwargs):
    return {"target": 2}


def double_target_valid_ir_input(**kwargs):
    return {"targets": [2, 3]}


def double_target_valid_input(**kwargs):
    return {"target1": 2, "target2": 3}


def single_probability_valid_input(**kwargs):
    return {"probability": 0.1234}


def single_probability_34_valid_input(**kwargs):
    return {"probability": 0.1234}


def single_probability_1516_valid_input(**kwargs):
    return {"probability": 0.1234}


def damping_single_probability_valid_input(**kwargs):
    return {"probability": 0.1234}


def damping_probability_valid_input(**kwargs):
    return {"gamma": 0.1234}


def triple_probability_valid_input(**kwargs):
    return {"probX": 0.1234, "probY": 0.1324, "probZ": 0.1423}


def single_control_valid_input(**kwargs):
    return {"control": 0}


def double_control_valid_ir_input(**kwargs):
    return {"controls": [0, 1]}


def double_control_valid_input(**kwargs):
    return {"control1": 0, "control2": 1}


def multi_target_valid_input(**kwargs):
    return {"targets": [5]}


def two_dimensional_matrix_list_valid_ir_input(**kwargs):
    return {"matrices": [[[[0, 0], [1, 0]], [[1, 0], [0, 0]]]]}


def two_dimensional_matrix_list_valid_input(**kwargs):
    input_type = kwargs.get("input_type")
    return {
        "matrices": [np.array([[input_type(0), input_type(1)], [input_type(1), input_type(0)]])]
    }


def multi_probability_valid_input(**kwargs):
    return {"probabilities": {"XX": 0.1}}


def multi_probability_invalid_input(**kwargs):
    return {"probabilities": {"XX": 1.1}}


valid_ir_switcher = {
    "SingleTarget": single_target_valid_input,
    "DoubleTarget": double_target_valid_ir_input,
    "SingleProbability": single_probability_valid_input,
    "SingleProbability_34": single_probability_34_valid_input,
    "SingleProbability_1516": single_probability_1516_valid_input,
    "DampingProbability": damping_probability_valid_input,
    "DampingSingleProbability": damping_single_probability_valid_input,
    "TripleProbability": triple_probability_valid_input,
    "MultiProbability": multi_probability_valid_input,
    "SingleControl": single_control_valid_input,
    "DoubleControl": double_control_valid_ir_input,
    "MultiTarget": multi_target_valid_input,
    "TwoDimensionalMatrixList": two_dimensional_matrix_list_valid_ir_input,
}


valid_subroutine_switcher = dict(
    valid_ir_switcher,
    **{
        "TwoDimensionalMatrixList": two_dimensional_matrix_list_valid_input,
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
    # based on the concept that control goes first in target input
    for subclass in irsubclasses:
        if subclass == SingleTarget:
            qubit_set.extend(list(single_target_valid_input().values()))
        elif subclass == DoubleTarget:
            qubit_set.extend(list(double_target_valid_ir_input().values()))
        elif subclass == MultiTarget:
            qubit_set.extend(list(multi_target_valid_input().values()))
        elif subclass == SingleControl:
            qubit_set = list(single_control_valid_input().values()) + qubit_set
        elif subclass == DoubleControl:
            qubit_set = list(double_control_valid_ir_input().values()) + qubit_set
        elif all(
            subclass != i
            for i in [
                SingleProbability,
                SingleProbability_34,
                SingleProbability_1516,
                DampingSingleProbability,
                DampingProbability,
                TripleProbability,
                TwoDimensionalMatrixList,
                MultiProbability,
            ]
        ):
            raise ValueError("Invalid subclass")
    input = {"target": QubitSet(qubit_set)}
    return input


def create_valid_noise_class_input(irsubclasses, **kwargs):
    input = {}
    if SingleProbability in irsubclasses:
        input |= single_probability_valid_input()
    if SingleProbability_34 in irsubclasses:
        input.update(single_probability_34_valid_input())
    if SingleProbability_1516 in irsubclasses:
        input.update(single_probability_1516_valid_input())
    if DampingSingleProbability in irsubclasses:
        input.update(damping_single_probability_valid_input())
    if DampingProbability in irsubclasses:
        input.update(damping_probability_valid_input())
    if TripleProbability in irsubclasses:
        input.update(triple_probability_valid_input())
    if MultiProbability in irsubclasses:
        input.update(multi_probability_valid_input())
    if TwoDimensionalMatrixList in irsubclasses:
        input.update(two_dimensional_matrix_list_valid_input(**kwargs))
    return input


def create_valid_instruction_input(testclass, irsubclasses, **kwargs):
    input = create_valid_target_input(irsubclasses)
    input["operator"] = testclass(**create_valid_noise_class_input(irsubclasses, **kwargs))
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
        elif all(
            subclass != i
            for i in [
                SingleProbability,
                SingleProbability_34,
                SingleProbability_1516,
                DampingSingleProbability,
                DampingProbability,
                TripleProbability,
                MultiProbability,
                TwoDimensionalMatrixList,
            ]
        ):
            raise ValueError("Invalid subclass")
    return qubit_count


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_ir_noise_level(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    expected = irclass(**create_valid_ir_input(irsubclasses))
    actual = testclass(**create_valid_noise_class_input(irsubclasses, **kwargs)).to_ir(
        **create_valid_target_input(irsubclasses)
    )
    assert actual == expected


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_ir_instruction_level(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    expected = irclass(**create_valid_ir_input(irsubclasses))
    instruction = Instruction(**create_valid_instruction_input(testclass, irsubclasses, **kwargs))
    actual = instruction.to_ir()
    assert actual == expected


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_noise_subroutine(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    qubit_count = calculate_qubit_count(irsubclasses)
    subroutine = getattr(Circuit(), subroutine_name)
    assert subroutine(**create_valid_subroutine_input(irsubclasses, **kwargs)) == Circuit(
        Instruction(**create_valid_instruction_input(testclass, irsubclasses, **kwargs))
    )
    if qubit_count == 1:
        multi_targets = [0, 1, 2]
        instruction_list = [
            Instruction(
                operator=testclass(**create_valid_noise_class_input(irsubclasses, **kwargs)),
                target=target,
            )
            for target in multi_targets
        ]
        subroutine = getattr(Circuit(), subroutine_name)
        subroutine_input = {"target": multi_targets}
        if SingleProbability in irsubclasses:
            subroutine_input |= single_probability_valid_input()
        if SingleProbability_34 in irsubclasses:
            subroutine_input.update(single_probability_34_valid_input())
        if SingleProbability_1516 in irsubclasses:
            subroutine_input.update(single_probability_1516_valid_input())
        if DampingSingleProbability in irsubclasses:
            subroutine_input.update(damping_single_probability_valid_input())
        if DampingProbability in irsubclasses:
            subroutine_input.update(damping_probability_valid_input())
        if TripleProbability in irsubclasses:
            subroutine_input.update(triple_probability_valid_input())
        if MultiProbability in irsubclasses:
            subroutine_input.update(multi_probability_valid_input())

        circuit1 = subroutine(**subroutine_input)
        circuit2 = Circuit(instruction_list)
        assert circuit1 == circuit2


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_noise_to_matrix(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    noise1 = testclass(**create_valid_noise_class_input(irsubclasses, **kwargs))
    noise2 = testclass(**create_valid_noise_class_input(irsubclasses, **kwargs))
    assert all(isinstance(matrix, np.ndarray) for matrix in noise1.to_matrix())
    assert all(np.allclose(m1, m2) for m1, m2 in zip(noise1.to_matrix(), noise2.to_matrix()))


@pytest.mark.parametrize("testclass,subroutine_name,irclass,irsubclasses,kwargs", testdata)
def test_fixed_qubit_count(testclass, subroutine_name, irclass, irsubclasses, kwargs):
    fixed_qubit_count = testclass.fixed_qubit_count()
    if fixed_qubit_count is not NotImplemented:
        noise = testclass(**create_valid_noise_class_input(irsubclasses, **kwargs))
        assert noise.qubit_count == fixed_qubit_count


@pytest.mark.parametrize(
    "parameterized_noise",
    [
        (Noise.BitFlip(0.1)),
        (Noise.BitFlip(FreeParameter("alpha"))),
        (Noise.PhaseFlip(0.1)),
        (Noise.PhaseFlip(FreeParameter("alpha"))),
        (Noise.Depolarizing(0.1)),
        (Noise.Depolarizing(FreeParameter("alpha"))),
        (Noise.AmplitudeDamping(0.1)),
        (Noise.AmplitudeDamping(FreeParameter("alpha"))),
        (Noise.GeneralizedAmplitudeDamping(0.1, 0.2)),
        (Noise.GeneralizedAmplitudeDamping(FreeParameter("alpha"), FreeParameter("beta"))),
        (Noise.PhaseDamping(0.1)),
        (Noise.PhaseDamping(FreeParameter("alpha"))),
        (Noise.TwoQubitDepolarizing(0.1)),
        (Noise.TwoQubitDepolarizing(FreeParameter("alpha"))),
        (Noise.TwoQubitDephasing(0.1)),
        (Noise.TwoQubitDephasing(FreeParameter("alpha"))),
        (Noise.TwoQubitPauliChannel({"XX": 0.1, "YY": 0.2})),
        (Noise.TwoQubitPauliChannel({"XX": FreeParameter("x"), "YY": FreeParameter("y")})),
        (Noise.PauliChannel(0.1, 0.2, 0.3)),
        (Noise.PauliChannel(FreeParameter("x"), FreeParameter("y"), FreeParameter("z"))),
    ],
)
def test_serialization(parameterized_noise):
    serialized = parameterized_noise.to_dict()
    serialized_str = json.dumps(serialized)
    deserialized_dict = json.loads(serialized_str)
    deserialized = Noise.from_dict(deserialized_dict)
    assert deserialized == parameterized_noise


@pytest.mark.parametrize(
    "parameterized_noise, params, expected_noise",
    [
        (Noise.BitFlip(FreeParameter("alpha")), {"alpha": 0.1}, Noise.BitFlip(0.1)),
        (Noise.PhaseFlip(FreeParameter("alpha")), {"alpha": 0.1}, Noise.PhaseFlip(0.1)),
        (Noise.Depolarizing(FreeParameter("alpha")), {"alpha": 0.1}, Noise.Depolarizing(0.1)),
        (
            Noise.AmplitudeDamping(FreeParameter("alpha")),
            {"alpha": 0.1},
            Noise.AmplitudeDamping(0.1),
        ),
        (
            Noise.GeneralizedAmplitudeDamping(FreeParameter("alpha"), FreeParameter("beta")),
            {"alpha": 0.1},
            Noise.GeneralizedAmplitudeDamping(0.1, FreeParameter("beta")),
        ),
        (Noise.PhaseDamping(FreeParameter("alpha")), {"alpha": 0.1}, Noise.PhaseDamping(0.1)),
        (
            Noise.TwoQubitDepolarizing(FreeParameter("alpha")),
            {"alpha": 0.1},
            Noise.TwoQubitDepolarizing(0.1),
        ),
        (
            Noise.TwoQubitDephasing(FreeParameter("alpha")),
            {"alpha": 0.1},
            Noise.TwoQubitDephasing(0.1),
        ),
        (
            Noise.TwoQubitPauliChannel({"XX": FreeParameter("x"), "YY": FreeParameter("y")}),
            {"x": 0.1},
            Noise.TwoQubitPauliChannel({"XX": 0.1, "YY": FreeParameter("y")}),
        ),
        (
            Noise.PauliChannel(FreeParameter("x"), FreeParameter("y"), FreeParameter("z")),
            {"x": 0.1, "z": 0.2},
            Noise.PauliChannel(0.1, FreeParameter("y"), 0.2),
        ),
    ],
)
def test_parameter_binding(parameterized_noise, params, expected_noise):
    result_noise = parameterized_noise.bind_values(**params)
    assert result_noise == expected_noise


def test_parameterized_noise():
    noise = Noise.PauliChannel(FreeParameter("a"), 0.2, FreeParameter("d"))
    assert noise.probX == FreeParameter("a")
    assert noise.probY == 0.2
    assert noise.probZ == FreeParameter("d")


# Additional Unitary noise tests


@pytest.mark.parametrize("matrices", invalid_kraus_matrices)
def test_kraus_invalid_matrix(matrices):
    with pytest.raises(ValueError):
        Noise.Kraus(matrices=matrices)


def test_kraus_matrix_target_size_mismatch():
    with pytest.raises(ValueError):
        Circuit().kraus(
            matrices=[np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])],
            targets=[0],
        )


@pytest.mark.parametrize(
    "probs",
    [
        {"X": -0.1},
        {"XY": 1.1},
        {"TX": 0.1},
        {"X": 0.5, "Y": 0.6},
        {"X": 0.1, "YY": 0.2},
        {"II": 0.9, "XX": 0.1},
    ],
)
def test_invalid_values_pauli_channel_two_qubit(probs):
    with pytest.raises(ValueError):
        Noise.TwoQubitPauliChannel(probs)


@pytest.mark.parametrize(
    "probs",
    [
        {"XY": 0.1},
        {"XX": 0.1, "ZZ": 0.2},
    ],
)
def test_valid_values_pauli_channel_two_qubit(probs):
    noise = Noise.TwoQubitPauliChannel(probs)
    assert len(noise.to_matrix()) == 16


@pytest.mark.parametrize(
    "noise, serialization_properties, target, expected_ir",
    [
        (
            Noise.BitFlip(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise bit_flip(0.5) q[3]",
        ),
        (
            Noise.BitFlip(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise bit_flip(0.5) $3",
        ),
        (
            Noise.PhaseFlip(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise phase_flip(0.5) q[3]",
        ),
        (
            Noise.PhaseFlip(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise phase_flip(0.5) $3",
        ),
        (
            Noise.PauliChannel(0.1, 0.2, 0.3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise pauli_channel(0.1, 0.2, 0.3) q[3]",
        ),
        (
            Noise.PauliChannel(0.1, 0.2, 0.3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise pauli_channel(0.1, 0.2, 0.3) $3",
        ),
        (
            Noise.Depolarizing(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise depolarizing(0.5) q[3]",
        ),
        (
            Noise.Depolarizing(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise depolarizing(0.5) $3",
        ),
        (
            Noise.TwoQubitDepolarizing(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3, 5],
            "#pragma braket noise two_qubit_depolarizing(0.5) q[3], q[5]",
        ),
        (
            Noise.TwoQubitDepolarizing(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3, 5],
            "#pragma braket noise two_qubit_depolarizing(0.5) $3, $5",
        ),
        (
            Noise.TwoQubitDephasing(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3, 5],
            "#pragma braket noise two_qubit_dephasing(0.5) q[3], q[5]",
        ),
        (
            Noise.TwoQubitDephasing(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3, 5],
            "#pragma braket noise two_qubit_dephasing(0.5) $3, $5",
        ),
        (
            Noise.AmplitudeDamping(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise amplitude_damping(0.5) q[3]",
        ),
        (
            Noise.AmplitudeDamping(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise amplitude_damping(0.5) $3",
        ),
        (
            Noise.GeneralizedAmplitudeDamping(0.5, 0.1),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise generalized_amplitude_damping(0.5, 0.1) q[3]",
        ),
        (
            Noise.GeneralizedAmplitudeDamping(0.5, 0.1),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise generalized_amplitude_damping(0.5, 0.1) $3",
        ),
        (
            Noise.PhaseDamping(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise phase_damping(0.5) q[3]",
        ),
        (
            Noise.PhaseDamping(0.5),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise phase_damping(0.5) $3",
        ),
        (
            Noise.Kraus([
                np.eye(4) * np.sqrt(0.9),
                np.kron([[1.0, 0.0], [0.0, 1.0]], [[0.0, 1.0], [1.0, 0.0]]) * np.sqrt(0.1),
            ]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3, 5],
            "#pragma braket noise kraus(["
            "[0.9486832980505138, 0, 0, 0], "
            "[0, 0.9486832980505138, 0, 0], "
            "[0, 0, 0.9486832980505138, 0], "
            "[0, 0, 0, 0.9486832980505138]], ["
            "[0, 0.31622776601683794, 0, 0], "
            "[0.31622776601683794, 0, 0, 0], "
            "[0, 0, 0, 0.31622776601683794], "
            "[0, 0, 0.31622776601683794, 0]]) q[3], q[5]",
        ),
        (
            Noise.Kraus([
                np.eye(4) * np.sqrt(0.9),
                np.kron([[1.0, 0.0], [0.0, 1.0]], [[0.0, 1.0], [1.0, 0.0]]) * np.sqrt(0.1),
            ]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3, 5],
            "#pragma braket noise kraus(["
            "[0.9486832980505138, 0, 0, 0], "
            "[0, 0.9486832980505138, 0, 0], "
            "[0, 0, 0.9486832980505138, 0], "
            "[0, 0, 0, 0.9486832980505138]], ["
            "[0, 0.31622776601683794, 0, 0], "
            "[0.31622776601683794, 0, 0, 0], "
            "[0, 0, 0, 0.31622776601683794], "
            "[0, 0, 0.31622776601683794, 0]]) $3, $5",
        ),
        (
            Noise.Kraus([
                np.array([[0.9486833j, 0], [0, 0.9486833j]]),
                np.array([[0, 0.31622777], [0.31622777, 0]]),
            ]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "#pragma braket noise kraus(["
            "[0.9486833im, 0], [0, 0.9486833im]], ["
            "[0, 0.31622777], [0.31622777, 0]]) q[3]",
        ),
        (
            Noise.Kraus([
                np.array([[0.9486833j, 0], [0, 0.9486833j]]),
                np.array([[0, 0.31622777], [0.31622777, 0]]),
            ]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "#pragma braket noise kraus(["
            "[0.9486833im, 0], [0, 0.9486833im]], ["
            "[0, 0.31622777], [0.31622777, 0]]) $3",
        ),
    ],
)
def test_noise_to_ir_openqasm(noise, serialization_properties, target, expected_ir):
    assert (
        noise.to_ir(
            target, ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )
        == expected_ir
    )
