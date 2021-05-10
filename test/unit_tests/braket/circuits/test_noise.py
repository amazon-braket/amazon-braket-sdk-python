import pytest

from braket.circuits import Operator
from braket.circuits.noise import (
    DampingNoise,
    GeneralizedAmplitudeDampingNoise,
    PauliNoise,
    Noise,
    SingleProbabilisticNoise,
)

invalid_data_qubit_count = [(0, ["foo"])]
invalid_data_ascii_symbols = [(1, None)]
invalid_data_ascii_symbols_length = [(2, ["foo", "boo", "braket"])]
invalid_data_prob = ["a", float("nan"), float("inf"), float("-inf"), 1 + 1j, 1.5, -2.6]


@pytest.fixture
def noise():
    return Noise(qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def single_probability_noise():
    return SingleProbabilisticNoise(probability=0.1, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def pauli_noise():
    return PauliNoise(probX=0.1, probY=0.2, probZ=0.3, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def damping_noise():
    return DampingNoise(gamma=0.2, qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def generalized_amplitude_damping_noise():
    return GeneralizedAmplitudeDampingNoise(
        probability=0.9, gamma=0.2, qubit_count=1, ascii_symbols=["foo"]
    )


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_qubit_count)
def test_invalid_data_qubit_count(qubit_count, ascii_symbols):
    Noise(qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_ascii_symbols)
def test_invalid_data_ascii_symbols(qubit_count, ascii_symbols):
    Noise(qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_ascii_symbols_length)
def test_invalid_data_ascii_symbols_length(qubit_count, ascii_symbols):
    Noise(qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("probability", invalid_data_prob)
def test_invalid_data_single_prob(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    SingleProbabilisticNoise(probability, qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("probX", invalid_data_prob)
def test_invalid_data_pauli_probX(probX):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probY = 0.1
    probZ = 0.1
    PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("probY", invalid_data_prob)
def test_invalid_data_pauli_probY(probY):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probZ = 0.1
    PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("probZ", invalid_data_prob)
def test_invalid_data_pauli_probZ(probZ):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probY = 0.1
    PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
def test_invalid_data_pauli_sum():
    qubit_count = 1
    ascii_symbols = ["foo"]
    probX = 0.1
    probY = 0.1
    probZ = 0.9
    PauliNoise(probX, probY, probZ, qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("gamma", invalid_data_prob)
def test_invalid_data_damping_prob(gamma):
    qubit_count = 1
    ascii_symbols = ["foo"]
    DampingNoise(gamma, qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("probability", invalid_data_prob)
def test_invalid_data_generalized_amplitude_damping_prob(probability):
    qubit_count = 1
    ascii_symbols = ["foo"]
    gamma = 0.1
    GeneralizedAmplitudeDampingNoise(probability, gamma, qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("gamma", invalid_data_prob)
def test_invalid_data_generalized_amplitude_damping_gamma(gamma):
    qubit_count = 1
    ascii_symbols = ["foo"]
    probability = 0.1
    GeneralizedAmplitudeDampingNoise(probability, gamma, qubit_count, ascii_symbols)


def test_ascii_symbols(noise):
    assert noise.ascii_symbols == ("foo",)


def test_is_operator(noise):
    assert isinstance(noise, Operator)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_ir_not_implemented_by_default(noise):
    noise.to_ir(None)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_matrix_not_implemented_by_default(noise):
    noise.to_matrix(None)


def test_noise_str(noise):
    expected = "{}('qubit_count': {})".format(noise.name, noise.qubit_count)
    assert str(noise) == expected


def test_single_probability_noise_str(single_probability_noise):
    expected = "{}('probability': {}, 'qubit_count': {})".format(
        single_probability_noise.name,
        single_probability_noise.probability,
        single_probability_noise.qubit_count,
    )
    assert str(single_probability_noise) == expected


def test_pauli_noise_str(pauli_noise):
    expected = "{}('probX': {}, 'probY': {}, 'probZ': {}, 'qubit_count': {})".format(
        pauli_noise.name,
        pauli_noise.probX,
        pauli_noise.probY,
        pauli_noise.probZ,
        pauli_noise.qubit_count,
    )
    assert str(pauli_noise) == expected


def test_damping_noise_str(damping_noise):
    expected = "{}('gamma': {}, 'qubit_count': {})".format(
        damping_noise.name,
        damping_noise.gamma,
        damping_noise.qubit_count,
    )
    assert str(damping_noise) == expected


def test_generalized_amplitude_damping_noise_str(generalized_amplitude_damping_noise):
    expected = "{}('probability': {}, 'gamma': {}, 'qubit_count': {})".format(
        generalized_amplitude_damping_noise.name,
        generalized_amplitude_damping_noise.probability,
        generalized_amplitude_damping_noise.gamma,
        generalized_amplitude_damping_noise.qubit_count,
    )
    assert str(generalized_amplitude_damping_noise) == expected


def test_equality():
    noise_1 = Noise(qubit_count=1, ascii_symbols=["foo"])
    noise_2 = Noise(qubit_count=1, ascii_symbols=["foo"])
    other_noise = Noise.AmplitudeDamping(gamma=0.5)
    non_noise = "non noise"

    assert noise_1 == noise_2
    assert noise_1 is not noise_2
    assert noise_1 != other_noise
    assert noise_1 != non_noise


def test_register_noise():
    class _FooNoise(Noise):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["foo"])

    Noise.register_noise(_FooNoise)
    assert Noise._FooNoise().name == _FooNoise().name
