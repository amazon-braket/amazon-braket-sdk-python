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

import pytest

from braket.circuits import Operator
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.noise import (
    DampingNoise,
    GeneralizedAmplitudeDampingNoise,
    MultiQubitPauliNoise,
    Noise,
    PauliNoise,
    SingleProbabilisticNoise,
    SingleProbabilisticNoise_34,
    SingleProbabilisticNoise_1516,
)
from braket.circuits.serialization import IRType

invalid_data_qubit_count = [(0, ["foo"])]
invalid_data_ascii_symbols = [(1, None)]
invalid_data_ascii_symbols_length = [(2, ["foo", "boo", "braket"])]
invalid_data_prob = [float("nan"), float("inf"), float("-inf"), 0.95, -2.6]
invalid_data_prob_2 = ["a", 1.0 + 1j]
invalid_data_prob_damping = [float("nan"), float("inf"), float("-inf"), 1.5, -2.6]
invalid_data_prob_damping_2 = ["a", 1.0 + 1j]


@pytest.fixture
def base_noise():
    return Noise(qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def single_probability_noise():
    return SingleProbabilisticNoise(probability=0.1, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def single_probability_noise_34():
    return SingleProbabilisticNoise_34(probability=0.1, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def single_probability_noise_1516():
    return SingleProbabilisticNoise_1516(probability=0.1, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def pauli_noise():
    return PauliNoise(probX=0.1, probY=0.2, probZ=0.3, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def damping_noise():
    return DampingNoise(gamma=0.2, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def generalized_amplitude_damping_noise():
    return GeneralizedAmplitudeDampingNoise(
        gamma=0.2, probability=0.9, qubit_count=1, ascii_symbols=["foo"]
    )


@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_qubit_count)
def test_invalid_data_qubit_count(qubit_count, ascii_symbols):
    with pytest.raises(ValueError):
        Noise(qubit_count, ascii_symbols)


@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_ascii_symbols)
def test_invalid_data_ascii_symbols(qubit_count, ascii_symbols):
    with pytest.raises(ValueError):
        Noise(qubit_count, ascii_symbols)


@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_ascii_symbols_length)
def test_invalid_data_ascii_symbols_length(qubit_count, ascii_symbols):
    with pytest.raises(ValueError):
        Noise(qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob)
def test_invalid_data_single_prob(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(ValueError):
        SingleProbabilisticNoise(probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob)
def test_invalid_data_single_prob_34(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(ValueError):
        SingleProbabilisticNoise_34(probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob)
def test_invalid_data_single_prob_1516(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(ValueError):
        SingleProbabilisticNoise_1516(probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob_2)
def test_invalid_data_type_single_prob(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(TypeError):
        SingleProbabilisticNoise(probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob_2)
def test_invalid_data_type_single_prob_34(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(TypeError):
        SingleProbabilisticNoise_34(probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob_2)
def test_invalid_data_type_single_prob_1516(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(TypeError):
        SingleProbabilisticNoise_1516(probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probX", invalid_data_prob)
def test_invalid_data_pauli_probX(probX):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probY = 0.1
    probZ = 0.1
    with pytest.raises(ValueError):
        PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probY", invalid_data_prob)
def test_invalid_data_pauli_probY(probY):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probZ = 0.1
    with pytest.raises(ValueError):
        PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probZ", invalid_data_prob)
def test_invalid_data_pauli_probZ(probZ):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probY = 0.1
    with pytest.raises(ValueError):
        PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probX", invalid_data_prob_2)
def test_invalid_data_type_pauli_probX(probX):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probY = 0.1
    probZ = 0.1
    with pytest.raises(TypeError):
        PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probY", invalid_data_prob_2)
def test_invalid_data_type_pauli_probY(probY):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probZ = 0.1
    with pytest.raises(TypeError):
        PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probZ", invalid_data_prob_2)
def test_invalid_data_type_pauli_probZ(probZ):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probY = 0.1
    with pytest.raises(TypeError):
        PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


def test_invalid_data_pauli_sum():
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probY = 0.1
    probZ = 0.9
    with pytest.raises(ValueError):
        PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.parametrize("gamma", invalid_data_prob_damping)
def test_invalid_data_damping_prob(gamma):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(ValueError):
        DampingNoise(gamma, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob_damping)
def test_invalid_data_generalized_amplitude_damping_prob(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    gamma = 0.1
    with pytest.raises(ValueError):
        GeneralizedAmplitudeDampingNoise(gamma, probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("gamma", invalid_data_prob_damping_2)
def test_invalid_data_type_damping_prob(gamma):
    qubit_count = 1
    ascii_symbols = ["foo"]
    with pytest.raises(TypeError):
        DampingNoise(gamma, qubit_count, ascii_symbols)


@pytest.mark.parametrize("probability", invalid_data_prob_damping_2)
def test_invalid_data_type_generalized_amplitude_damping_prob(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    gamma = 0.1
    with pytest.raises(TypeError):
        GeneralizedAmplitudeDampingNoise(gamma, probability, qubit_count, ascii_symbols)


@pytest.mark.parametrize("gamma", invalid_data_prob_damping)
def test_invalid_data_generalized_amplitude_damping_gamma(gamma):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probability = 0.1
    with pytest.raises(ValueError):
        GeneralizedAmplitudeDampingNoise(gamma, probability, qubit_count, ascii_symbols)


def test_ascii_symbols(base_noise):
    assert base_noise.ascii_symbols == ("foo",)


def test_is_operator(base_noise):
    assert isinstance(base_noise, Operator)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_ir_not_implemented_by_default(base_noise):
    base_noise.to_ir(None)


@pytest.mark.parametrize(
    "ir_type, serialization_properties, expected_exception, expected_message",
    [
        (IRType.JAQCD, None, NotImplementedError, "to_jaqcd has not been implemented yet."),
        (IRType.OPENQASM, None, NotImplementedError, "to_openqasm has not been implemented yet."),
        ("invalid-ir-type", None, ValueError, "Supplied ir_type invalid-ir-type is not supported."),
        (
            IRType.OPENQASM,
            "invalid-serialization-properties",
            ValueError,
            "serialization_properties must be of type OpenQASMSerializationProperties for "
            "IRType.OPENQASM.",
        ),
    ],
)
def test_noise_to_ir(
    ir_type, serialization_properties, expected_exception, expected_message, base_noise
):
    with pytest.raises(expected_exception) as exc:
        base_noise.to_ir(0, ir_type, serialization_properties=serialization_properties)
    assert exc.value.args[0] == expected_message


def test_to_matrix_not_implemented_by_default(base_noise):
    with pytest.raises(NotImplementedError):
        base_noise.to_matrix(None)


def test_invalid_deserializatoin():
    with pytest.raises(NotImplementedError):
        Noise.from_dict({})


@pytest.mark.parametrize(
    "noise, expected_string, expected_repr",
    [
        (Noise(1, ["foo"]), "Noise('qubit_count': 1)", "Noise('qubit_count': 1)"),
        (
            SingleProbabilisticNoise(0.1, 1, ["foo"]),
            "SingleProbabilisticNoise(0.1)",
            "SingleProbabilisticNoise('probability': 0.1, 'qubit_count': 1)",
        ),
        (
            DampingNoise(0.1, 1, ["foo"]),
            "DampingNoise(0.1)",
            "DampingNoise('gamma': 0.1, 'qubit_count': 1)",
        ),
        (
            GeneralizedAmplitudeDampingNoise(0.1, 0.2, 1, ["foo"]),
            "GeneralizedAmplitudeDampingNoise(0.1, 0.2)",
            "GeneralizedAmplitudeDampingNoise('gamma': 0.1, 'probability': 0.2, 'qubit_count': 1)",
        ),
        (
            PauliNoise(0.1, 0.2, 0.3, 1, ["foo"]),
            "PauliNoise(0.1, 0.2, 0.3)",
            "PauliNoise('probX': 0.1, 'probY': 0.2, 'probZ': 0.3, 'qubit_count': 1)",
        ),
        (
            MultiQubitPauliNoise({"X": 0.2}, 1, ["foo"]),
            "MultiQubitPauliNoise({'X': 0.2})",
            "MultiQubitPauliNoise('probabilities' : {'X': 0.2}, 'qubit_count': 1)",
        ),
    ],
)
def test_noise_str_repr(noise, expected_string, expected_repr):
    assert str(noise) == expected_string
    assert repr(noise) == expected_repr


@pytest.mark.parametrize(
    "noise",
    [
        SingleProbabilisticNoise(0.1, 1, ["foo"]),
        DampingNoise(0.1, 1, ["foo"]),
        GeneralizedAmplitudeDampingNoise(0.1, 0.2, 1, ["foo"]),
        PauliNoise(0.1, 0.2, 0.3, 1, ["foo"]),
        MultiQubitPauliNoise({"X": 0.2}, 1, ["foo"]),
    ],
)
def test_noise_serialization(noise):
    representation = noise.to_dict()
    assert isinstance(representation, dict)
    serialized = json.dumps(representation)
    assert isinstance(serialized, str)


@pytest.mark.parametrize(
    "noise, equal_noise, unequal_noise, param_noise",
    [
        (
            SingleProbabilisticNoise(0.1, 1, ["foo"]),
            SingleProbabilisticNoise(0.1, 1, ["foo"]),
            SingleProbabilisticNoise(0.2, 1, ["foo"]),
            SingleProbabilisticNoise(FreeParameter("alpha"), 1, ["foo"]),
        ),
        (
            DampingNoise(0.1, 1, ["foo"]),
            DampingNoise(0.1, 1, ["foo"]),
            DampingNoise(0.2, 1, ["foo"]),
            DampingNoise(FreeParameter("alpha"), 1, ["foo"]),
        ),
        (
            GeneralizedAmplitudeDampingNoise(0.1, 0.2, 1, ["foo"]),
            GeneralizedAmplitudeDampingNoise(0.1, 0.2, 1, ["foo"]),
            GeneralizedAmplitudeDampingNoise(0.2, 0.2, 1, ["foo"]),
            GeneralizedAmplitudeDampingNoise(FreeParameter("alpha"), 0.2, 1, ["foo"]),
        ),
        (
            PauliNoise(0.1, 0.2, 0.3, 1, ["foo"]),
            PauliNoise(0.1, 0.2, 0.3, 1, ["foo"]),
            PauliNoise(0.2, 0.2, 0.3, 1, ["foo"]),
            PauliNoise(FreeParameter("x"), FreeParameter("y"), FreeParameter("z"), 1, ["foo"]),
        ),
        (
            MultiQubitPauliNoise({"X": 0.2}, 1, ["foo"]),
            MultiQubitPauliNoise({"X": 0.2}, 1, ["foo"]),
            MultiQubitPauliNoise({"X": 0.3}, 1, ["foo"]),
            MultiQubitPauliNoise({"X": FreeParameter("alpha")}, 1, ["foo"]),
        ),
    ],
)
def test_noise_equality(noise, equal_noise, unequal_noise, param_noise):
    assert noise == noise
    assert noise is noise
    assert noise == equal_noise
    assert noise is not equal_noise
    assert noise != unequal_noise
    assert noise != param_noise
    assert noise != Noise(qubit_count=1, ascii_symbols=["foo"])


def test_noise_base_not_equal_to_different_type():
    assert Noise(qubit_count=1, ascii_symbols=["foo"]) != "foo"


def test_register_noise():
    class _FooNoise(Noise):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["foo"])

    Noise.register_noise(_FooNoise)
    assert Noise._FooNoise().name == _FooNoise().name


@pytest.mark.parametrize(
    "noise_class, params",
    [
        (SingleProbabilisticNoise, {"probability": 0.6}),
        (SingleProbabilisticNoise, {"probability": -0.1}),
        (SingleProbabilisticNoise_34, {"probability": 0.76}),
        (SingleProbabilisticNoise_34, {"probability": -0.1}),
        (SingleProbabilisticNoise_1516, {"probability": 0.93755}),
        (SingleProbabilisticNoise_1516, {"probability": -0.1}),
        (MultiQubitPauliNoise, {"probabilities": {"X": 0.4, "Y": 0.7}}),
        (MultiQubitPauliNoise, {"probabilities": {"X": 0.4, "Y": -0.7}}),
        (PauliNoise, {"probX": 0.5, "probY": 0.5, "probZ": 0.5}),
        (PauliNoise, {"probX": -0.1, "probY": 0, "probZ": 0}),
        (DampingNoise, {"gamma": -0.1}),
        (DampingNoise, {"gamma": 1.1}),
        (GeneralizedAmplitudeDampingNoise, {"gamma": 0.1, "probability": -0.2}),
        (GeneralizedAmplitudeDampingNoise, {"gamma": 0.1, "probability": 1.2}),
    ],
)
def test_invalid_values(noise_class, params):
    with pytest.raises(ValueError):
        noise_class(**params, qubit_count=1, ascii_symbols=["foo"])


@pytest.mark.parametrize(
    "probs, qubit_count, ascii_symbols",
    [
        ({"X": 0.1}, 1, ["PC"]),
        ({"XXY": 0.1}, 3, ["PC3", "PC3", "PC3"]),
        ({"YX": 0.1, "IZ": 0.2}, 2, ["PC2", "PC2"]),
    ],
)
def test_multi_qubit_noise(probs, qubit_count, ascii_symbols):
    noise = MultiQubitPauliNoise(probs, qubit_count, ascii_symbols)
    assert noise.probabilities == probs
    assert noise.qubit_count == qubit_count
    assert noise.ascii_symbols == tuple(ascii_symbols)
    assert noise.parameters == [probs[key] for key in sorted(probs.keys())]


@pytest.mark.xfail(raises=ValueError)
class TestInvalidMultiQubitNoise:
    qubit_count = 1
    ascii_symbols = ["PC2"]

    def test_non_empty(self):
        MultiQubitPauliNoise({}, self.qubit_count, self.ascii_symbols)

    def test_non_identity(self):
        MultiQubitPauliNoise({"I": 0.1}, self.qubit_count, self.ascii_symbols)

    def test_non_equal_length_paulis(self):
        MultiQubitPauliNoise({"X": 0.1, "XY": 0.1}, 1, self.ascii_symbols)
        MultiQubitPauliNoise({"X": 0.1, "Y": 0.1}, 2, ["PC2", "PC2"])

    def test_prob_over_one(self):
        MultiQubitPauliNoise({"X": 0.9, "Y": 0.9}, 1, self.ascii_symbols)
        MultiQubitPauliNoise({"XX": 0.9, "YY": 0.9}, 1, self.ascii_symbols)

    def test_prob_under_one(self):
        MultiQubitPauliNoise({"X": -0.6, "Y": -0.9}, 1, self.ascii_symbols)
        MultiQubitPauliNoise({"XX": -0.9, "YY": -0.9}, 2, ["PC2", "PC2"])

    def test_non_pauli_string(self):
        MultiQubitPauliNoise({"T": 0.1}, 1, self.ascii_symbols)

    def test_individual_probs(self):
        MultiQubitPauliNoise({"X": -0.1}, 1, self.ascii_symbols)
        MultiQubitPauliNoise({"X": 1.1}, 1, self.ascii_symbols)

    @pytest.mark.xfail(raises=TypeError)
    def test_keys_strings(self):
        MultiQubitPauliNoise({1: 1.1}, 1, self.ascii_symbols)

    @pytest.mark.xfail(raises=TypeError)
    def test_values_floats(self):
        MultiQubitPauliNoise({"X": "str"}, 1, self.ascii_symbols)
