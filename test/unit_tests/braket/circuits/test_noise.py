import pytest
from braket.circuits import Noise, Operator


@pytest.fixture
def noise():
    return Noise(qubit_count=1, ascii_symbols=["foo"])


def test_is_operator(noise):
    assert isinstance(noise, Operator)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_ir_not_implemented_by_default(noise):
    noise.to_ir(None)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_matrix_not_implemented_by_default(noise):
    noise.to_matrix(None)


def test_str(noise):
    expected = "{}('qubit_count': {})".format(noise.name, noise.qubit_count)
    assert str(noise) == expected


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
