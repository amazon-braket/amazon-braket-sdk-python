import pytest

from braket.circuits import Operator
from braket.circuits.noise import Noise, ProbabilityNoise

invalid_data_qubit_count = [(0, ["foo"])]
invalid_data_ascii_symbols = [(1, None)]
invalid_data_ascii_symbols_length = [(2, ["foo", "boo", "braket"])]
invalid_data_prob = ["a", float("nan"), float("inf"), float("-inf"), 1+1j, 1.5, -2.6]


@pytest.fixture
def noise():
    return Noise(qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def probability_noise():
    return ProbabilityNoise(prob=0.1, qubit_count=1, ascii_symbols=["foo"])


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_qubit_count)
def test_invalid_data_qubit_count(qubit_count, ascii_symbols):
    noise = Noise(qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_ascii_symbols)
def test_invalid_data_ascii_symbols(qubit_count, ascii_symbols):
    noise = Noise(qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("qubit_count, ascii_symbols", invalid_data_ascii_symbols_length)
def test_invalid_data_ascii_symbols_length(qubit_count, ascii_symbols):
    noise = Noise(qubit_count, ascii_symbols)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("prob", invalid_data_prob)
def test_invalid_data_prob(prob):
    qubit_count = 1
    ascii_symbols = ["foo"]
    noise = ProbabilityNoise(prob, qubit_count, ascii_symbols)


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


def test_probability_noise_str(probability_noise):
    expected = "{}('prob': {}, 'qubit_count': {})".format(probability_noise.name,
                                                          probability_noise.prob,
                                                          probability_noise.qubit_count)
    assert str(probability_noise) == expected


def test_equality():
    noise_1 = Noise(qubit_count=1, ascii_symbols=["foo"])
    noise_2 = Noise(qubit_count=1, ascii_symbols=["foo"])
    other_noise = Noise.Amplitude_Damping(prob=0.5)
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
