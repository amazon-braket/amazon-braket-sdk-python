import pytest

from braket.circuits import Circuit
from braket.circuits.observables import X, Y, Z, H, I
from braket.passes.circuit_passes.result_type_validator import ResultTypeValidator

from braket.emulation.device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES


@pytest.fixture
def supported_result_types():
    return [result_type.name for result_type in DEFAULT_SUPPORTED_RESULT_TYPES]


@pytest.fixture
def connectivity_graph():
    # Create a simple connectivity graph for a 2-qubit device
    return {"0": ["1"], "1": ["0"]}


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
def test_valid_circuits(supported_result_types, connectivity_graph, circuit):
    """
    ResultTypeValidator should not raise any errors when validating these circuits.
    """
    ResultTypeValidator(supported_result_types, connectivity_graph).validate(circuit)


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
def test_invalid_circuits(supported_result_types, connectivity_graph, circuit):
    """
    ResultTypeValidator should raise errors when validating these circuits.
    """
    with pytest.raises(ValueError):
        ResultTypeValidator(supported_result_types, connectivity_graph).validate(circuit)


def test_invalid_instantiation():
    with pytest.raises(ValueError, match="Supported result types must be provided."):
        ResultTypeValidator([], {"0": ["1"]})

    with pytest.raises(ValueError, match="Connectivity graph must be provided."):
        ResultTypeValidator(["Expectation"], None)


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
    connectivity_graph = {"0": ["1"], "1": ["0"]}
    assert ResultTypeValidator(result_types_1, connectivity_graph) == ResultTypeValidator(
        result_types_2, connectivity_graph
    )


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
    connectivity_graph = {"0": ["1"], "1": ["0"]}
    assert ResultTypeValidator(result_types_1, connectivity_graph) != ResultTypeValidator(
        result_types_2, connectivity_graph
    )

    # Test inequality with different connectivity graphs
    assert ResultTypeValidator(result_types_1, {"0": ["1"], "1": ["0"]}) != ResultTypeValidator(
        result_types_1, {"0": ["1", "2"], "1": ["0"], "2": ["0"]}
    )


def test_invalid_qubit_target():
    """
    Test that ResultTypeValidator raises an error when a result type targets a qubit
    that is not in the device's connectivity graph.
    """
    # Create a connectivity graph for a 1-qubit device
    connectivity_graph = {"0": []}

    # Create a circuit with a result type targeting qubit 1, which is not in the device
    circuit = Circuit().h(0).expectation(observable=Z(), target=1)

    # The validator should raise an error because qubit 1 is not in the device
    with pytest.raises(
        ValueError, match="Qubit 1 in result type Expectation is not a valid qubit for this device."
    ):
        ResultTypeValidator(["Expectation", "Probability"], connectivity_graph).validate(circuit)
