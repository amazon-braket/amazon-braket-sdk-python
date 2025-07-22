import pytest

from braket.circuits import Circuit
from braket.circuits.observables import X, Y, Z, H, I
from braket.passes.circuit_passes.result_type_validator import ResultTypeValidator

from braket.emulation.device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES


@pytest.fixture
def supported_result_types():
    return [result_type.name for result_type in DEFAULT_SUPPORTED_RESULT_TYPES]


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit().h(0).cnot(0, 1).probability(),
        Circuit().h(0).cnot(0, 1).expectation(observable=Z(), target=0),
        Circuit().h(0).cnot(0, 1).sample(observable=X(), target=0),
        Circuit().h(0).cnot(0, 1).variance(observable=Z(), target=0),
        Circuit().h(0).cnot(0, 1).expectation(observable=Z(), target=0).probability(),
        Circuit().h(0).cnot(0, 1).sample(observable=Y(), target=1).probability(target=[0]),
        Circuit().h(0).cnot(0, 1).variance(observable=H(), target=0),
        Circuit().h(0).cnot(0, 1).expectation(observable=I(), target=0),
    ],
)
def test_valid_circuits(supported_result_types, circuit):
    """
    ResultTypeValidator should not raise any errors when validating these circuits.
    """
    ResultTypeValidator(supported_result_types).validate(circuit)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().h(0).cnot(0, 1).state_vector(),
        Circuit().h(0).cnot(0, 1).probability().state_vector(),
        Circuit().h(0).cnot(0, 1).expectation(observable=Z(), target=0).state_vector(),
        Circuit().h(0).cnot(0, 1).density_matrix(),
        Circuit().h(0).cnot(0, 1).amplitude(state=["00", "11"]),
    ],
)
def test_invalid_circuits(supported_result_types, circuit):
    """
    ResultTypeValidator should raise errors when validating these circuits.
    """
    with pytest.raises(ValueError):
        ResultTypeValidator(supported_result_types).validate(circuit)


def test_invalid_instantiation():
    with pytest.raises(ValueError, match="Supported result types must be provided."):
        ResultTypeValidator([])


@pytest.mark.parametrize(
    "result_types_1, result_types_2",
    [
        (["Expectation"], ["Expectation"]),
        (["Probability", "Sample"], ["Sample", "Probability"]),
        (
            ["Expectation", "Probability", "Sample", "Variance"],
            ["Variance", "Sample", "Probability", "Expectation"],
        ),
    ],
)
def test_equality(result_types_1, result_types_2):
    assert ResultTypeValidator(result_types_1) == ResultTypeValidator(result_types_2)


@pytest.mark.parametrize(
    "result_types_1, result_types_2",
    [
        (["Expectation"], ["Probability"]),
        (["Probability"], ["Probability", "Sample"]),
        (["Probability", "Sample"], ["Sample"]),
        (
            ["Expectation", "Probability", "Sample"],
            ["Expectation", "Probability", "Sample", "Variance"],
        ),
    ],
)
def test_inequality(result_types_1, result_types_2):
    assert ResultTypeValidator(result_types_1) != ResultTypeValidator(result_types_2)
