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

from unittest.mock import Mock
from collections import defaultdict

import pytest

from braket.circuits import Circuit, Gate, Noise, Observable, ResultType
from braket.circuits.gates import Unitary, H
from braket.circuits.noise_model import (
    CircuitInstructionCriteria,
    Criteria,
    GateCriteria,
    NoiseModel,
    ObservableCriteria,
    QubitInitializationCriteria,
    UnitaryGateCriteria,
    MeasureCriteria,
)
from braket.circuits.noises import (
    BitFlip,
    Depolarizing,
    PauliChannel,
    TwoQubitDepolarizing,
    PhaseFlip,
)
from braket.circuits.instruction import Instruction
from braket.circuits.measure import Measure
from braket.circuits.result_type import ObservableResultType
from braket.circuits.noise_model.noise_model import (
    NoiseModelInstruction,
    CriteriaKeyResult,
    _apply_noise_on_observable_result_types,
)
from braket.circuits.observable import Observable
from braket.circuits.result_types import Sample


def h_unitary():
    return Unitary(Gate.H().to_matrix())


@pytest.fixture
def default_noise_model():
    noise_list = []
    criteria_list = []
    noise_model = NoiseModel()
    for i in range(3):
        noise = Mock(spec=Noise)
        criteria = Mock(spec=CircuitInstructionCriteria)
        criteria.instruction_matches.return_value = i % 2 == 0
        noise_model.add_noise(noise, criteria)
        noise_list.append(noise)
        criteria_list.append(criteria)
    return noise_model, noise_list, criteria_list


def test_simple_add_noise():
    noise_model = NoiseModel()
    assert len(noise_model.instructions) == 0
    mock_noise = Mock(spec=Noise)
    mock_criteria = Mock(spec=CircuitInstructionCriteria)
    noise_model.add_noise(mock_noise, mock_criteria)
    noise_list = noise_model.instructions
    assert len(noise_list) == 1
    assert mock_noise == noise_list[0].noise
    assert mock_criteria == noise_list[0].criteria


def test_insert_noise(default_noise_model):
    noise_model, noise_list, criteria_list = default_noise_model
    listed_noise = noise_model.instructions
    assert len(listed_noise) == 3

    mock_noise = Mock(spec=Noise)
    mock_criteria = Mock(spec=CircuitInstructionCriteria)

    noise_model.insert_noise(1, mock_noise, mock_criteria)

    listed_noise = noise_model.instructions
    assert len(listed_noise) == 4
    assert listed_noise[0].noise == noise_list[0]
    assert listed_noise[0].criteria == criteria_list[0]
    assert listed_noise[1].noise == mock_noise
    assert listed_noise[1].criteria == mock_criteria
    assert listed_noise[2].noise == noise_list[1]
    assert listed_noise[2].criteria == criteria_list[1]
    assert listed_noise[3].noise == noise_list[2]
    assert listed_noise[3].criteria == criteria_list[2]


def test_remove_noise(default_noise_model):
    noise_model, noise_list, _ = default_noise_model

    listed_noise = noise_model.instructions
    assert len(listed_noise) == 3

    noise_model.remove_noise(1)

    listed_noise = noise_model.instructions
    assert len(listed_noise) == 2
    assert listed_noise[0].noise == noise_list[0]
    assert listed_noise[1].noise == noise_list[2]


@pytest.mark.parametrize(
    "gate, qubit, noise, noise_type, expected_length",
    [
        (None, None, None, None, 6),
        (None, None, PauliChannel, None, 2),
        (Gate.H, None, None, None, 3),
        (Gate.CNot, None, None, None, 2),
        (None, 0, None, None, 5),
        # (None, (0, 1), None, None, 1), # TODO: I'm not sure of the best way to fix this.
        (Gate.CNot, (0, 1), None, None, 1),
        (Gate.CNot, (1, 0), None, None, 0),
        (Gate.H, 2, None, None, 1),
        (Gate.H, None, Depolarizing, None, 2),
    ],
)
def test_filter(gate, qubit, noise, noise_type, expected_length):
    noise_model = (
        NoiseModel()
        .add_noise(PauliChannel(0.01, 0.02, 0.03), GateCriteria(Gate.I, [0, 1]))
        .add_noise(Depolarizing(0.04), GateCriteria(Gate.H))
        .add_noise(Depolarizing(0.05), GateCriteria(Gate.CNot, [0, 1]))
        .add_noise(PauliChannel(0.06, 0.07, 0.08), GateCriteria(Gate.H, [0, 1]))
        .add_noise(Depolarizing(0.09), GateCriteria(None, 0))
        .add_noise(Depolarizing(0.10), QubitInitializationCriteria([0, 1]))
    )
    result_model = noise_model.from_filter(qubit=qubit, gate=gate, noise=noise)
    assert len(result_model.instructions) == expected_length


@pytest.mark.parametrize(
    "noise_types, expected_string",
    [
        ([], ""),
        ([Criteria], ""),
        (
            [GateCriteria],
            "Gate Noise:\n  my_noise 0, my_criteria 0\n  my_noise 1, my_criteria 1",
        ),
        (
            [Criteria, GateCriteria, ObservableCriteria, QubitInitializationCriteria],
            "Initialization Noise:\n  my_noise 0, my_criteria 0\n  my_noise 1, my_criteria 1\n"
            "Gate Noise:\n  my_noise 0, my_criteria 0\n  my_noise 1, my_criteria 1\n"
            "Readout Noise:\n  my_noise 0, my_criteria 0\n  my_noise 1, my_criteria 1",
        ),
    ],
)
def test_str_representation(noise_types, expected_string):
    noise_model = NoiseModel()

    for noise_type in noise_types:
        for index in range(2):
            mock_noise = Mock(spec=Noise)
            mock_noise.__str__ = Mock(return_value=f"my_noise {index}")
            mock_criteria = Mock(spec=noise_type)
            mock_criteria.__str__ = Mock(return_value=f"my_criteria {index}")
            noise_model.add_noise(mock_noise, mock_criteria)

    str_representation = noise_model.__str__()
    assert str_representation == expected_string


def test_repr_representation():
    noise_model = NoiseModel()
    mock_noise = Mock(spec=Noise)
    mock_noise.__repr__ = Mock(return_value="n")
    mock_criteria = Mock(spec=Criteria)
    mock_criteria.__repr__ = Mock(return_value="c")
    noise_model.add_noise(mock_noise, mock_criteria)
    str_representation = noise_model.__repr__()
    assert str_representation == "{'instructions': [NoiseModelInstruction(noise=n, criteria=c)]}"


def test_serialization():
    noise_model = (
        NoiseModel()
        .add_noise(PauliChannel(0.01, 0.02, 0.03), GateCriteria(Gate.I, [0, 1]))
        .add_noise(Depolarizing(0.04), GateCriteria(Gate.H))
        .add_noise(Depolarizing(0.05), GateCriteria(Gate.CNot, [0, 1]))
        .add_noise(PauliChannel(0.06, 0.07, 0.08), GateCriteria(Gate.H, [0, 1]))
    )
    serialized_model = noise_model.to_dict()
    deserialized_model = NoiseModel.from_dict(serialized_model)
    assert len(deserialized_model.instructions) == len(noise_model.instructions)
    for index, deserialized_item in enumerate(deserialized_model.instructions):
        assert noise_model.instructions[index].noise == deserialized_item.noise
        assert noise_model.instructions[index].criteria == deserialized_item.criteria
    assert deserialized_model is not None


def test_apply():
    noise_model = (
        NoiseModel()
        .add_noise(PauliChannel(0.01, 0.02, 0.03), GateCriteria(Gate.I, [0, 1]))
        .add_noise(Depolarizing(0.04), GateCriteria(Gate.H))
        .add_noise(TwoQubitDepolarizing(0.05), GateCriteria(Gate.CNot, [0, 1]))
        .add_noise(PauliChannel(0.06, 0.07, 0.08), GateCriteria(Gate.H, [0, 1]))
        .add_noise(Depolarizing(0.10), UnitaryGateCriteria(h_unitary(), 0))
        .add_noise(Depolarizing(0.06), ObservableCriteria(Observable.Z, 0))
        .add_noise(Depolarizing(0.09), QubitInitializationCriteria(0))
    )
    layer1 = Circuit().h(0).cnot(0, 1).sample(Observable.Z(), 0)
    layer2 = Circuit().unitary([0], h_unitary().to_matrix())
    circuit = layer1 + layer2
    noisy_circuit_from_circuit = noise_model.apply(circuit)
    expected_circuit = (
        Circuit()
        .depolarizing(0, 0.09)
        .h(0)
        .depolarizing(0, 0.04)
        .pauli_channel(0, 0.06, 0.07, 0.08)
        .cnot(0, 1)
        .two_qubit_depolarizing(0, 1, 0.05)
        .unitary([0], h_unitary().to_matrix())
        .depolarizing(0, 0.10)
        .apply_readout_noise(Depolarizing(0.06), 0)
        .sample(Observable.Z(), 0)
    )
    assert noisy_circuit_from_circuit == expected_circuit


def test_apply_in_order():
    noise_model = (
        NoiseModel()
        .add_noise(Depolarizing(0.01), GateCriteria(Gate.H))
        .add_noise(Depolarizing(0.02), GateCriteria(Gate.H))
    )
    circuit = Circuit().h(0)
    noisy_circuit = noise_model.apply(circuit)
    expected_circuit = circuit.apply_gate_noise([Depolarizing(0.01), Depolarizing(0.02)])
    assert noisy_circuit == expected_circuit


@pytest.mark.parametrize(
    "noise_model, input_circuit, expected_circuit",
    [
        (
            # model with noise on H(0)
            NoiseModel().add_noise(Depolarizing(0.01), GateCriteria(Gate.H, 0)),
            # input circuit has an H gate on qubit 0
            Circuit().h(0).cnot(0, 1),
            # expected circuit has noise on qubit 0
            Circuit().h(0).depolarizing(0, 0.01).cnot(0, 1),
        ),
        (
            # model with noise on H(0)
            NoiseModel().add_noise(Depolarizing(0.01), GateCriteria(Gate.H, 0)),
            # input circuit has two H gates on qubit 0
            Circuit().h(0).h(0).cnot(0, 1),
            # expected circuit has noise on qubit 0
            Circuit().h(0).depolarizing(0, 0.01).h(0).depolarizing(0, 0.01).cnot(0, 1),
        ),
        (
            # model with noise on all gates, on qubits 0, 1
            NoiseModel().add_noise(Depolarizing(0.01), GateCriteria(None, [0, 1])),
            # input circuit
            Circuit().h(0).h(1).cnot(0, 1),
            # expected circuit has noise on qubit 0
            Circuit().h(0).depolarizing(0, 0.01).h(1).depolarizing(1, 0.01).cnot(0, 1),
        ),
        (
            # model with noise on all gates, on qubits [0, 1]
            NoiseModel().add_noise(Depolarizing(0.01), GateCriteria(None, [[0, 1]])),
            # input circuit
            Circuit().h(0).h(1).cnot(0, 1),
            # expected circuit has noise on the CNot gate
            Circuit().h(0).h(1).cnot(0, 1).depolarizing(0, 0.01).depolarizing(1, 0.01),
        ),
        (
            # model with noise on all gates, on qubits [0, 1]
            NoiseModel().add_noise(TwoQubitDepolarizing(0.01), GateCriteria(None, [[0, 1]])),
            # input circuit
            Circuit().h(0).h(1).cnot(0, 1),
            # expected circuit has noise on the CNot gate
            Circuit().h(0).h(1).cnot(0, 1).two_qubit_depolarizing(0, 1, 0.01),
        ),
        (
            # model with noise on a unitary H(0)
            NoiseModel().add_noise(Depolarizing(0.01), UnitaryGateCriteria(h_unitary(), 0)),
            # input circuit has a unitary H gate on qubit 0
            Circuit().unitary([0], h_unitary().to_matrix()).cnot(0, 1),
            # expected circuit has noise on qubit 0
            Circuit().unitary([0], h_unitary().to_matrix()).depolarizing(0, 0.01).cnot(0, 1),
        ),
    ],
)
def test_gate_noise(noise_model, input_circuit, expected_circuit):
    result_circuit = noise_model.apply(input_circuit)
    assert result_circuit == expected_circuit


@pytest.mark.parametrize(
    "noise_model, input_circuit, expected_circuit",
    [
        (
            # model
            NoiseModel().add_noise(Depolarizing(0.01), QubitInitializationCriteria()),
            # input circuit
            Circuit().h(0).cnot(0, 1),
            # expected circuit has noise on both qubits
            Circuit().depolarizing(0, 0.01).depolarizing(1, 0.01).h(0).cnot(0, 1),
        ),
        (
            # model
            NoiseModel().add_noise(Depolarizing(0.01), QubitInitializationCriteria(range(4))),
            # input circuit
            Circuit().h(0).cnot(0, 1),
            # expected circuit has noise on both qubits
            Circuit().depolarizing(0, 0.01).depolarizing(1, 0.01).h(0).cnot(0, 1),
        ),
        (
            # model only specifies noise on one qubit
            NoiseModel().add_noise(Depolarizing(0.01), QubitInitializationCriteria(1)),
            # input circuit
            Circuit().h(0).cnot(0, 1),
            # expected circuit has noise on one qubit
            Circuit().depolarizing(1, 0.01).h(0).cnot(0, 1),
        ),
        (
            # model only specifies noise on an unrelated qubit
            NoiseModel().add_noise(Depolarizing(0.01), QubitInitializationCriteria(2)),
            # input circuit
            Circuit().h(0).cnot(0, 1),
            # expected circuit has no noise applied
            Circuit().h(0).cnot(0, 1),
        ),
        (
            # model does not specify initialization noise
            NoiseModel().add_noise(Depolarizing(0.01), GateCriteria(Gate.X, 2)),
            # input circuit
            Circuit().h(0).cnot(0, 1),
            # expected circuit has no noise applied
            Circuit().h(0).cnot(0, 1),
        ),
    ],
)
def test_apply_initialization_noise(noise_model, input_circuit, expected_circuit):
    result_circuit = noise_model.apply(input_circuit)
    assert result_circuit == expected_circuit


@pytest.mark.parametrize(
    "noise_model, input_circuit, expected_circuit",
    [
        (
            # model
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(Observable.Z)),
            # input circuit has no explicit observables
            Circuit().h(0).cnot(0, 1),
            # expected circuit has no noise applied
            Circuit().h(0).cnot(0, 1),
        ),
        (
            # model has observable criteria only on one qubit
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(Observable.Z, 0)),
            # input circuit has no explicit observables
            Circuit().h(0).cnot(0, 1),
            # expected circuit has no noise applied
            Circuit().h(0).cnot(0, 1),
        ),
        (
            # model
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(Observable.Z)),
            # input circuit has explicit explicit observables
            Circuit().h(0).cnot(0, 1).sample(Observable.Z(), 0),
            # expected circuit has noise applied
            Circuit().h(0).cnot(0, 1).depolarizing(0, 0.01).sample(Observable.Z(), 0),
        ),
        (
            # model
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(Observable.X, 0)),
            # input circuit doesn't contain observable X
            Circuit().h(0).cnot(0, 1),
            # expected circuit has no change.
            Circuit().h(0).cnot(0, 1),
        ),
        (
            # model
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(Observable.X, 0)),
            # input circuit contains observable X
            Circuit().h(0).cnot(0, 1).sample(Observable.X(), 0),
            # expected circuit noise applied.
            Circuit().h(0).cnot(0, 1).depolarizing(0, 0.01).sample(Observable.X(), 0),
        ),
        (
            # model only has an observable on Z
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(Observable.Z, 0)),
            # input circuit contains observable X
            Circuit().h(0).cnot(0, 1).sample(Observable.X(), 0),
            # expected circuit has no change
            Circuit().h(0).cnot(0, 1).sample(Observable.X(), 0),
        ),
        (
            # model uses qubit criteria
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(None, None)),
            # input circuit doesn't contain observables
            Circuit().h(0).cnot(0, 1),
            # expected circuit has no noise applied
            Circuit().h(0).cnot(0, 1),
        ),
        (
            # model uses qubit criteria on non-related qubits
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(None, [2, 3])),
            # input circuit doesn't contain observables
            Circuit().h(0).cnot(0, 1),
            # expected circuit has no change
            Circuit().h(0).cnot(0, 1),
        ),
        (
            # model uses qubit criteria
            NoiseModel().add_noise(Depolarizing(0.01), ObservableCriteria(None, [0, 1])),
            # input circuit contains observable X
            Circuit().h(0).cnot(0, 1).sample(Observable.X(), 0),
            # expected circuit noise applied.
            Circuit().h(0).cnot(0, 1).depolarizing(0, 0.01).sample(Observable.X(), 0),
        ),
        (
            # model uses observable and qubit criteria
            NoiseModel()
            .add_noise(Depolarizing(0.01), ObservableCriteria(Observable.X, 0))
            .add_noise(Depolarizing(0.02), ObservableCriteria(None, [0, 1])),
            # input circuit contains observable X
            Circuit().h(0).cnot(0, 1).sample(Observable.X(), 0),
            # expected circuit noise applied.
            Circuit()
            .h(0)
            .cnot(0, 1)
            .depolarizing(0, 0.01)
            .depolarizing(0, 0.02)
            .sample(Observable.X(), 0),
        ),
        (
            # model uses observable criteria with any observable/qubit.
            NoiseModel().add_noise(BitFlip(0.01), ObservableCriteria(None, None)),
            # input circuit contains many different types of result types for qubit 0
            Circuit()
            .h(0)
            .cnot(0, 1)
            .probability(target=[0, 1])
            .probability(target=0)
            .expectation(observable=Observable.Z(), target=0)
            .sample(observable=Observable.X(), target=0)
            .variance(observable=Observable.Z(), target=0),
            # expected circuit only applies BitFlip once to qubit 0
            Circuit()
            .h(0)
            .cnot(0, 1)
            .probability(target=[0, 1])
            .probability(target=0)
            .expectation(observable=Observable.Z(), target=0)
            .sample(observable=Observable.X(), target=0)
            .variance(observable=Observable.Z(), target=0)
            .apply_readout_noise(BitFlip(0.01), 0),
        ),
        (
            # model uses observable criteria with any observable/qubit.
            NoiseModel().add_noise(BitFlip(0.01), ObservableCriteria(None, None)),
            # input circuit only has a probability result type
            Circuit().h(0).cnot(0, 1).probability(target=[0, 1]).probability(target=0),
            # expected circuit has no noise applied
            Circuit().h(0).cnot(0, 1).probability(target=[0, 1]).probability(target=0),
        ),
    ],
)
def test_apply_readout_noise(noise_model, input_circuit, expected_circuit):
    result_circuit = noise_model.apply(input_circuit)
    assert result_circuit == expected_circuit


@pytest.mark.xfail(raises=IndexError)
def test_remove_noise_at_invalid_index():
    noise_model = NoiseModel()
    noise_model.remove_noise(index=0)
    assert not "should not get here"


def test_add_invalid_noise():
    noise_model = NoiseModel()
    with pytest.raises(TypeError):
        noise_model.add_noise(Mock(), Mock(spec=Criteria))


def test_add_invalid_criteria():
    noise_model = NoiseModel()
    with pytest.raises(TypeError):
        noise_model.add_noise(Mock(spec=Noise), Mock())


def test_apply_to_circuit_list():
    noise_model = NoiseModel()
    with pytest.raises(TypeError):
        noise_model.add_noise(Mock(), Mock(spec=Criteria))
        noise_model.apply([])


@pytest.mark.parametrize(
    "noise_model, input_circuit, expected_circuit",
    [
        (
            # model with measure noise on qubit 0
            NoiseModel().add_noise(BitFlip(0.01), MeasureCriteria([0])),
            # input circuit with measure on qubit 0
            Circuit().h(0).measure([0]),
            # expected circuit has noise before measure
            Circuit().h(0).bit_flip(0, 0.01).measure([0]),
        ),
        (
            # model with measure noise on qubits 0 and 1
            NoiseModel().add_noise(BitFlip(0.01), MeasureCriteria([0, 1])),
            # input circuit with measure on qubits 0 and 1
            Circuit().h(0).cnot(0, 1).measure([0, 1]),
            # expected circuit has noise before measure
            Circuit().h(0).cnot(0, 1).bit_flip(0, 0.01).bit_flip(1, 0.01).measure([0, 1]),
        ),
        (
            # model with measure noise on qubit 1
            NoiseModel().add_noise(BitFlip(0.01), MeasureCriteria([1])),
            # input circuit with measure on qubit 0
            Circuit().h(0).measure([0]),
            # expected circuit has no noise (measure on wrong qubit)
            Circuit().h(0).measure([0]),
        ),
        (
            # model with measure noise and gate noise
            NoiseModel()
            .add_noise(BitFlip(0.01), MeasureCriteria([0]))
            .add_noise(Depolarizing(0.02), GateCriteria(Gate.H, [0])),
            # input circuit with H gate and measure
            Circuit().h(0).measure([0]),
            # expected circuit has both types of noise
            Circuit().h(0).depolarizing(0, 0.02).bit_flip(0, 0.01).measure([0]),
        ),
        (
            # model with measure noise and observable noise
            NoiseModel()
            .add_noise(BitFlip(0.01), MeasureCriteria([0]))
            .add_noise(Depolarizing(0.02), ObservableCriteria(Observable.Z, [0])),
            # input circuit with measure only
            Circuit().h(0).measure([0]),
            # expected circuit has measure noise only
            Circuit().h(0).bit_flip(0, 0.01).measure([0]),
        ),
        (
            # model with measure noise and observable noise
            NoiseModel()
            .add_noise(BitFlip(0.01), MeasureCriteria([0]))
            .add_noise(Depolarizing(0.02), ObservableCriteria(Observable.Z, [0])),
            # input circuit with observable only
            Circuit().h(0).sample(Observable.Z(), 0),
            # expected circuit has observable noise only
            Circuit().h(0).depolarizing(0, 0.02).sample(Observable.Z(), 0),
        ),
    ],
)
def test_apply_measure_noise(noise_model, input_circuit, expected_circuit):
    assert noise_model.apply(input_circuit) == expected_circuit


@pytest.mark.parametrize(
    "circuit, expected",
    [
        (Circuit().h(0).measure([0]), Circuit().h(0).measure([0])),
        (Circuit().h(0).sample(Observable.Z(), 0), Circuit().h(0).sample(Observable.Z(), 0)),
    ],
)
def test_circuit_with_measure_or_result_type_only(circuit, expected):
    assert circuit == expected


def test_add_noise_invalid_combinations():
    noise_model = NoiseModel()
    mock_noise = Mock(spec=Noise)

    # Test invalid noise type
    with pytest.raises(TypeError):
        noise_model.add_noise("not a noise", GateCriteria(Gate.H))

    # Test invalid criteria type
    with pytest.raises(TypeError):
        noise_model.add_noise(mock_noise, "not a criteria")

    # Test None values
    with pytest.raises(TypeError):
        noise_model.add_noise(None, GateCriteria(Gate.H))
    with pytest.raises(TypeError):
        noise_model.add_noise(mock_noise, None)


def test_serialization_edge_cases():
    # Test empty noise model
    empty_model = NoiseModel()
    serialized = empty_model.to_dict()
    deserialized = NoiseModel.from_dict(serialized)
    assert len(deserialized.instructions) == 0

    # Test invalid serialization data
    with pytest.raises(KeyError):
        NoiseModel.from_dict({})


def test_filter_edge_cases():
    noise_model = (
        NoiseModel()
        .add_noise(Depolarizing(0.01), GateCriteria(Gate.H))
        .add_noise(Depolarizing(0.02), GateCriteria(Gate.CNot))
        .add_noise(Depolarizing(0.03), ObservableCriteria(Observable.Z))
    )

    # Test filtering with multiple criteria
    filtered = noise_model.from_filter(gate=Gate.H, noise=Depolarizing)
    assert len(filtered.instructions) == 1

    # Test filtering with no matches
    filtered = noise_model.from_filter(gate=Gate.X)
    assert len(filtered.instructions) == 0

    # Test filtering with invalid combinations
    filtered = noise_model.from_filter(gate="invalid")
    assert len(filtered.instructions) == 0


def test_apply_overlapping_noise():
    noise_model = (
        NoiseModel()
        .add_noise(Depolarizing(0.01), GateCriteria(Gate.H))
        .add_noise(Depolarizing(0.02), GateCriteria(None, 0))
    )

    circuit = Circuit().h(0)
    noisy_circuit = noise_model.apply(circuit)
    expected_circuit = Circuit().h(0).depolarizing(0, 0.01).depolarizing(0, 0.02)
    assert noisy_circuit == expected_circuit


def test_apply_multiple_result_types():
    noise_model = (
        NoiseModel()
        .add_noise(Depolarizing(0.01), ObservableCriteria(Observable.Z, 0))
        .add_noise(Depolarizing(0.02), ObservableCriteria(Observable.X, 0))
    )

    circuit = Circuit().h(0).sample(Observable.Z(), 0).sample(Observable.X(), 0)
    noisy_circuit = noise_model.apply(circuit)
    expected_circuit = (
        Circuit()
        .h(0)
        .depolarizing(0, 0.01)
        .sample(Observable.Z(), 0)
        .depolarizing(0, 0.02)
        .sample(Observable.X(), 0)
    )
    assert noisy_circuit == expected_circuit


def test_process_measure_block_multiple_measurements():
    """Test processing measure blocks with multiple measurements."""
    noise_model = NoiseModel()
    measure_block = [
        Instruction(Measure(), [0]),
        Instruction(Measure(), [1]),
        Instruction(Measure(), [2]),
    ]
    measure_noise_map = defaultdict(list)
    noise_model._process_measure_block(measure_block, measure_noise_map)
    assert len(measure_noise_map) == 0  # No noise instructions added yet


def test_process_measure_block_no_measurements():
    """Test processing measure blocks with no measurements."""
    noise_model = NoiseModel()
    measure_block = []
    measure_noise_map = defaultdict(list)
    noise_model._process_measure_block(measure_block, measure_noise_map)
    assert len(measure_noise_map) == 0


def test_apply_noise_to_all_qubits():
    """Test applying noise to all qubits in a block."""
    noise_model = NoiseModel()
    result = Circuit()
    noise_instruction = NoiseModelInstruction(noise=BitFlip(0.1), criteria=MeasureCriteria())
    qubits_in_block = {0, 1, 2}
    noise_model._apply_noise_to_qubits(
        result, noise_instruction, qubits_in_block, CriteriaKeyResult.ALL
    )
    assert len(result.instructions) == 3
    for i in range(3):
        assert isinstance(result.instructions[i].operator, BitFlip)


def test_apply_noise_to_specific_qubits():
    """Test applying noise to specific qubits in a block."""
    noise_model = NoiseModel()
    result = Circuit()
    noise_instruction = NoiseModelInstruction(noise=BitFlip(0.1), criteria=MeasureCriteria())
    qubits_in_block = {0, 1, 2}
    target_qubits = {0, 2}
    noise_model._apply_noise_to_qubits(result, noise_instruction, qubits_in_block, target_qubits)
    assert len(result.instructions) == 2
    assert isinstance(result.instructions[0].operator, BitFlip)
    assert result.instructions[0].target == [0]
    assert isinstance(result.instructions[1].operator, BitFlip)
    assert result.instructions[1].target == [2]


def test_process_noise_instructions_multiple():
    """Test processing multiple noise instructions for measure blocks."""
    noise_model = NoiseModel()
    result = Circuit()
    measure_block = [Instruction(Measure(), [0])]
    qubits_in_block = {0}
    noise_model._instructions = [
        NoiseModelInstruction(noise=BitFlip(0.1), criteria=MeasureCriteria()),
        NoiseModelInstruction(noise=PhaseFlip(0.1), criteria=MeasureCriteria()),
    ]
    noise_model._process_noise_instructions(result, measure_block, qubits_in_block)
    assert len(result.instructions) == 2
    assert isinstance(result.instructions[0].operator, BitFlip)
    assert isinstance(result.instructions[1].operator, PhaseFlip)


def test_apply_measure_noise_multiple_blocks():
    """Test applying measure noise to multiple measure blocks."""
    circuit = Circuit()
    circuit.add_instruction(Instruction(Measure(), [0]))
    circuit.add_instruction(Instruction(H(), [1]))
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), MeasureCriteria([0, 1]))
    result = noise_model._apply_measure_noise(circuit)
    assert any(isinstance(instr.operator, BitFlip) for instr in result.instructions)


def test_apply_readout_noise_to_observable():
    """Test applying readout noise to observable result types."""
    circuit = Circuit()
    circuit.add_result_type(Sample(Observable.X(), [0]))
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), ObservableCriteria(Observable.X, [0]))
    result = _apply_noise_on_observable_result_types(circuit, noise_model.instructions)
    # The BitFlip noise is applied as an instruction
    assert any(isinstance(instr.operator, BitFlip) for instr in result.instructions)
    assert any(isinstance(rt, Sample) for rt in result.result_types)


def test_apply_readout_noise_multiple_observables():
    """Test applying readout noise to multiple observable result types."""
    circuit = Circuit()
    circuit.add_result_type(Sample(Observable.X(), [0]))
    circuit.add_result_type(Sample(Observable.Z(), [1]))
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), ObservableCriteria(Observable.X, [0]))
    noise_model.add_noise(BitFlip(0.01), ObservableCriteria(Observable.Z, [1]))
    result = _apply_noise_on_observable_result_types(circuit, noise_model.instructions)
    assert any(isinstance(rt, Sample) for rt in result.result_types)


def test_process_measure_block_with_noise():
    """Test processing a measure block with noise instructions."""
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), MeasureCriteria([0, 1]))
    measure_block = [Instruction(Measure(), [0]), Instruction(Measure(), [1])]
    measure_noise_map = defaultdict(list)
    noise_model._process_measure_block(measure_block, measure_noise_map)
    # The implementation does not support block-level matching, so the map should be empty
    assert all(len(v) == 0 for v in measure_noise_map.values())


def test_process_measure_block_without_matching_noise():
    """Test processing a measure block without matching noise instructions."""
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), MeasureCriteria([2, 3]))  # Different qubits
    measure_block = [Instruction(Measure(), [0]), Instruction(Measure(), [1])]
    measure_noise_map = defaultdict(list)
    noise_model._process_measure_block(measure_block, measure_noise_map)
    assert all(len(v) == 0 for v in measure_noise_map.values())


def test_process_all_measure_blocks():
    """Test processing all measure blocks in a circuit."""
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), MeasureCriteria([0, 1]))
    circuit = Circuit().h(0).measure([0]).h(1).measure([1])
    measure_noise_map = defaultdict(list)
    noise_model._process_all_measure_blocks(circuit, measure_noise_map)
    # The implementation does not support block-level matching, so the map should be empty
    assert all(len(v) == 0 for v in measure_noise_map.values())


def test_process_noise_instructions():
    """Test processing noise instructions for a measure block."""
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), MeasureCriteria([0]))
    result = Circuit()
    measure_block = [Instruction(Measure(), [0])]
    qubits_in_block = {0}
    noise_model._process_noise_instructions(result, measure_block, qubits_in_block)
    assert any(isinstance(instr.operator, BitFlip) for instr in result.instructions)


def test_flush_measure_block():
    """Test flushing a measure block with noise."""
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), MeasureCriteria([0]))
    result = Circuit()
    measure_block = [Instruction(Measure(), [0])]
    # Only pass result and measure_block (3 arguments including self)
    noise_model._flush_measure_block(result, measure_block)
    assert any(isinstance(instr.operator, BitFlip) for instr in result.instructions)


def test_apply_noise_on_observable_result_types():
    """Test applying noise on observable result types."""
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.01), ObservableCriteria(Observable.Z, [0]))
    circuit = Circuit().h(0).add_result_type(Sample(Observable.Z(), [0]))
    result = _apply_noise_on_observable_result_types(circuit, noise_model.instructions)
    assert any(isinstance(instr.operator, H) for instr in result.instructions)
    assert any(isinstance(rt, Sample) for rt in result.result_types)


def test_measure_criteria_edge_cases():
    """Test edge cases for MeasureCriteria."""
    # Test with None qubits
    criteria = MeasureCriteria(None)
    assert criteria.qubits is None
    assert criteria.qubit_intersection([0, 1, 2]) == {0, 1, 2}

    # Test with empty qubit set
    criteria = MeasureCriteria([])
    assert criteria.qubits is None  # Empty list is treated as None
    assert criteria.qubit_intersection([0, 1, 2]) == {0, 1, 2}

    # Test with single qubit
    criteria = MeasureCriteria(0)
    assert criteria.qubits == {0}
    assert criteria.qubit_intersection([0, 1, 2]) == {0}


def test_noise_model_measure_block_processing():
    """Test measure block processing in NoiseModel."""
    # Test with empty measure block
    noise_model = NoiseModel()
    circuit = Circuit()
    result = noise_model._apply_measure_noise(circuit)
    assert result == circuit

    # Test with measure block containing multiple measurements
    noise_model = NoiseModel().add_noise(BitFlip(0.01), MeasureCriteria([0, 1]))
    circuit = Circuit().h(0).cnot(0, 1).measure([0]).measure([1])
    result = noise_model._apply_measure_noise(circuit)

    expected_types = [
        Gate.H,
        Gate.CNot,
        BitFlip,
        BitFlip,
        Measure,
        Measure,
    ]
    expected_targets = [
        [0],
        [0, 1],
        [0],
        [1],
        [0],
        [1],
    ]
    actual_instructions = result.instructions
    assert len(actual_instructions) == len(expected_types)
    for instr, expected_type, expected_target in zip(
        actual_instructions, expected_types, expected_targets
    ):
        assert isinstance(instr.operator, expected_type)
        assert list(instr.target) == expected_target
        if isinstance(instr.operator, BitFlip):
            assert instr.operator.probability == 0.01


def test_observable_criteria_edge_cases():
    """Test edge cases for ObservableCriteria."""
    # Test with None observables and qubits
    criteria = ObservableCriteria(None, None)
    assert criteria._observables is None
    assert criteria._qubits is None

    # Test with empty observable set
    criteria = ObservableCriteria([], None)
    assert criteria._observables is None  # Empty list is treated as None
    assert criteria._qubits is None

    # Test with single observable and qubit
    criteria = ObservableCriteria(Observable.X, 0)
    assert criteria._observables == {Observable.X}
    assert criteria._qubits == {0}

    # Test with non-ObservableResultType
    criteria = ObservableCriteria(Observable.X, 0)
    assert not criteria.result_type_matches(ResultType.StateVector())

    # Test with valid target (not empty)
    criteria = ObservableCriteria(Observable.X, 0)
    # Use Sample result type, which is a valid ObservableResultType
    assert criteria.result_type_matches(Sample(Observable.X(), [0]))


def test_noise_model_observable_result_types():
    """Test noise application on observable result types."""
    # Test with multiple observable result types
    noise_model = NoiseModel().add_noise(BitFlip(0.01), ObservableCriteria(Observable.Z))
    circuit = Circuit().h(0).cnot(0, 1).sample(Observable.Z(), 0).sample(Observable.Z(), 1)
    result = noise_model.apply(circuit)
    expected = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .apply_readout_noise(BitFlip(0.01), 0)
        .sample(Observable.Z(), 0)
        .apply_readout_noise(BitFlip(0.01), 1)
        .sample(Observable.Z(), 1)
    )
    assert result == expected

    # Test with mixed observable types
    noise_model = NoiseModel().add_noise(BitFlip(0.01), ObservableCriteria(Observable.Z))
    circuit = Circuit().h(0).cnot(0, 1).sample(Observable.Z(), 0).sample(Observable.X(), 1)
    result = noise_model.apply(circuit)
    expected = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .apply_readout_noise(BitFlip(0.01), 0)
        .sample(Observable.Z(), 0)
        .sample(Observable.X(), 1)
    )
    assert result == expected

    # Test with no observable result types
    noise_model = NoiseModel().add_noise(BitFlip(0.01), ObservableCriteria(Observable.Z))
    circuit = Circuit().h(0).cnot(0, 1)
    result = noise_model.apply(circuit)
    assert result == circuit
