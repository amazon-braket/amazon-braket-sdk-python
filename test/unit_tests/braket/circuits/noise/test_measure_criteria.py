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

import pytest

from braket.circuits.instruction import Instruction
from braket.circuits.gates import X
from braket.circuits.measure import Measure
from braket.circuits.noise_model import MeasureCriteria


@pytest.mark.parametrize(
    "criteria, instruction, expected",
    [
        (MeasureCriteria(), Instruction(Measure(), [0]), True),
        (MeasureCriteria(qubits=[0]), Instruction(Measure(), [0]), True),
        (MeasureCriteria(qubits=[1]), Instruction(Measure(), [0]), False),
        (MeasureCriteria(qubits=[0, 1]), Instruction(Measure(), [0]), True),
        (MeasureCriteria(qubits=[0, 1]), Instruction(Measure(), [1]), True),
        (MeasureCriteria(qubits=[0, 1]), Instruction(Measure(), [2]), False),
        (MeasureCriteria(), Instruction(X(), [0]), False),
    ],
)
def test_instruction_matches(criteria, instruction, expected):
    assert criteria.instruction_matches(instruction) is expected


@pytest.mark.parametrize(
    "criteria, qubits, expected",
    [
        # Test with no specific qubits
        (MeasureCriteria(), [0, 1], {0, 1}),
        (MeasureCriteria(), [0], {0}),
        # Test with specific qubits
        (MeasureCriteria([0]), [0, 1], {0}),
        (MeasureCriteria([0, 1]), [0, 1], {0, 1}),
        (MeasureCriteria([1]), [0], set()),
        # Test with empty qubit sets
        (MeasureCriteria(), [], set()),
        (MeasureCriteria([0]), [], set()),
    ],
)
def test_qubit_intersection(criteria, qubits, expected):
    assert criteria.qubit_intersection(qubits) == expected


def test_serialization():
    criteria = MeasureCriteria([0, 1])
    serialized = criteria.to_dict()
    deserialized = MeasureCriteria.from_dict(serialized)
    assert criteria.qubits == deserialized.qubits


def test_str_representation():
    criteria = MeasureCriteria([0, 1])
    assert str(criteria) == "MeasureCriteria(qubits=[0, 1])"


def test_repr_representation():
    criteria = MeasureCriteria([0, 1])
    assert repr(criteria) == "MeasureCriteria(qubits=[0, 1])"


def test_get_keys():
    criteria = MeasureCriteria([0, 1])
    assert criteria.get_keys("GATE") == {Measure()}
    assert criteria.get_keys("QUBIT") == {0, 1}
