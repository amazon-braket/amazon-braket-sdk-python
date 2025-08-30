# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import pytest
from unittest.mock import Mock

from braket.circuits import Circuit, Instruction
from braket.circuits.measure import Measure
from braket.circuits.noise_model.measure_criteria import MeasureCriteria
from braket.circuits.noise_model.criteria import CriteriaKey, CriteriaKeyResult
from braket.circuits.noise_model.noise_model import NoiseModel
from braket.circuits.noises import BitFlip, PhaseFlip


def test_measure_criteria_initialization():
    # Test initialization with no qubits
    criteria = MeasureCriteria()
    assert criteria._qubits is None

    # Test initialization with single qubit
    criteria = MeasureCriteria(qubits=0)
    assert criteria._qubits == {0}

    # Test initialization with multiple qubits
    criteria = MeasureCriteria(qubits=[0, 1])
    assert criteria._qubits == {0, 1}


def test_measure_criteria_string_representation():
    # Test string representation with no qubits
    criteria = MeasureCriteria()
    assert str(criteria) == "MeasureCriteria(None)"
    assert repr(criteria) == "MeasureCriteria(qubits=None)"

    # Test string representation with qubits
    criteria = MeasureCriteria(qubits=[0, 1])
    assert str(criteria) == "MeasureCriteria({0, 1})"
    assert repr(criteria) == "MeasureCriteria(qubits={0, 1})"


def test_measure_criteria_applicable_key_types():
    criteria = MeasureCriteria()
    assert list(criteria.applicable_key_types()) == [CriteriaKey.QUBIT]


def test_measure_criteria_get_keys():
    # Test with no qubits specified
    criteria = MeasureCriteria()
    assert criteria.get_keys(CriteriaKey.QUBIT) == CriteriaKeyResult.ALL
    assert criteria.get_keys(CriteriaKey.GATE) == set()

    # Test with specific qubits
    criteria = MeasureCriteria(qubits=[0, 1])
    assert criteria.get_keys(CriteriaKey.QUBIT) == {0, 1}
    assert criteria.get_keys(CriteriaKey.GATE) == set()


def test_measure_criteria_instruction_matches():
    criteria = MeasureCriteria(qubits=[0, 1])

    # Test with matching measure instruction
    measure_instruction = Instruction(Measure(), 0)
    assert criteria.instruction_matches(measure_instruction) is True

    # Test with non-matching qubit
    measure_instruction = Instruction(Measure(), 2)
    assert criteria.instruction_matches(measure_instruction) is False

    # Test with non-measure instruction
    non_measure_instruction = Mock(spec=Instruction)
    non_measure_instruction.operator = Mock()
    assert criteria.instruction_matches(non_measure_instruction) is False


def test_measure_criteria_serialization():
    # Test serialization with no qubits
    criteria = MeasureCriteria()
    serialized = criteria.to_dict()
    assert serialized == {"__class__": "MeasureCriteria", "qubits": None}
    deserialized = MeasureCriteria.from_dict(serialized)
    assert deserialized._qubits is None

    # Test serialization with qubits
    criteria = MeasureCriteria(qubits=[0, 1])
    serialized = criteria.to_dict()
    assert serialized == {"__class__": "MeasureCriteria", "qubits": [0, 1]}
    deserialized = MeasureCriteria.from_dict(serialized)
    assert deserialized._qubits == {0, 1}


@pytest.mark.parametrize(
    "noise_model, input_circuit, expected_circuit",
    [
        (
            # Test single qubit measurement with noise
            NoiseModel().add_noise(BitFlip(0.1), MeasureCriteria(qubits=[0])),
            Circuit().x(0).measure(0),
            Circuit().x(0).bit_flip(0, 0.1).measure(0),
        ),
        (
            # Test multiple qubit measurements with noise
            NoiseModel().add_noise(BitFlip(0.1), MeasureCriteria(qubits=[0, 1])),
            Circuit().x(0).x(1).measure([0, 1]),
            Circuit().x(0).x(1).bit_flip(0, 0.1).measure(0).bit_flip(1, 0.1).measure(1),
        ),
        (
            # Test measurement on non-targeted qubit
            NoiseModel().add_noise(BitFlip(0.1), MeasureCriteria(qubits=[0])),
            Circuit().x(1).measure(1),
            Circuit().x(1).measure(1),
        ),
        (
            # Test multiple noise types on same measurement
            NoiseModel()
            .add_noise(BitFlip(0.1), MeasureCriteria(qubits=[0]))
            .add_noise(PhaseFlip(0.2), MeasureCriteria(qubits=[0])),
            Circuit().x(0).measure(0),
            Circuit().x(0).bit_flip(0, 0.1).phase_flip(0, 0.2).measure(0),
        ),
    ],
)
def test_measure_criteria_in_noise_model(noise_model, input_circuit, expected_circuit):
    noisy_circuit = noise_model.apply(input_circuit)
    assert noisy_circuit == expected_circuit


def test_measure_criteria_from_dict():
    # Test with no qubits
    d = {"__class__": "MeasureCriteria", "qubits": None}
    obj = MeasureCriteria.from_dict(d)
    assert isinstance(obj, MeasureCriteria)
    assert obj._qubits is None

    # Test with specific qubits
    d = {"__class__": "MeasureCriteria", "qubits": [0, 1]}
    obj = MeasureCriteria.from_dict(d)
    assert isinstance(obj, MeasureCriteria)
    assert obj._qubits == {0, 1}


def test_measure_criteria_from_dict_via_class_and_base():
    d = {"__class__": "MeasureCriteria", "qubits": [0, 1]}
    # Call via MeasureCriteria
    obj1 = MeasureCriteria.from_dict(d)
    assert isinstance(obj1, MeasureCriteria)
    assert obj1._qubits == {0, 1}

    # Call via base class CircuitInstructionCriteria
    from braket.circuits.noise_model.circuit_instruction_criteria import CircuitInstructionCriteria

    obj2 = CircuitInstructionCriteria.from_dict(d)
    assert isinstance(obj2, MeasureCriteria)
    assert obj2._qubits == {0, 1}

    # Call via Criteria base class
    from braket.circuits.noise_model.criteria import Criteria

    obj3 = Criteria.from_dict(d)
    assert isinstance(obj3, MeasureCriteria)
    assert obj3._qubits == {0, 1}
