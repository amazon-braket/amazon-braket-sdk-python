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

from braket.circuits import Gate, Instruction, Observable
from braket.circuits.noise_model import (
    CriteriaKey,
    CriteriaKeyResult,
    GateCriteria,
    ObservableCriteria,
)


@pytest.mark.parametrize(
    "gates, qubits",
    [
        (None, range(3)),
        (None, None),
        (Gate.H, range(3)),
        ([Gate.H], range(3)),
        ([Gate.I, Gate.H], range(3)),
        (Gate.H, 1),
        ([Gate.H], [1]),
        ([Gate.I, Gate.H], [1, 0]),
        (Gate.H, None),
    ],
)
def test_happy_case(gates, qubits):
    criteria = GateCriteria(gates=gates, qubits=qubits)
    assert criteria.applicable_key_types() == [CriteriaKey.QUBIT, CriteriaKey.GATE]
    if gates is None:
        assert CriteriaKeyResult.ALL == criteria.get_keys(CriteriaKey.GATE)
    else:
        assert Gate.H in criteria.get_keys(CriteriaKey.GATE)
    if qubits is None:
        assert CriteriaKeyResult.ALL == criteria.get_keys(CriteriaKey.QUBIT)
    else:
        assert 1 in criteria.get_keys(CriteriaKey.QUBIT)


@pytest.mark.parametrize(
    "gates, qubits",
    [
        (None, range(3)),
        (None, None),
        (Gate.H, range(3)),
        ([Gate.H], 1),
        ([Gate.H], [1]),
        ([Gate.H], [[1]]),
        ([Gate.CNot], [0, 1]),
        ([Gate.CNot], [[1, 2]]),
        ([Gate.CNot], [[3, 4], [5, 6]]),
        ([Gate.I, Gate.H], range(3)),
        ([Gate.I, Gate.H], None),
    ],
)
def test_serialization(gates, qubits):
    test_criteria = GateCriteria(gates=gates, qubits=qubits)
    serialized_criteria = test_criteria.to_dict()
    assert serialized_criteria["__class__"] == "GateCriteria"
    assert "gates" in serialized_criteria
    assert "qubits" in serialized_criteria
    deserialized_criteria = GateCriteria.from_dict(serialized_criteria)
    assert test_criteria == deserialized_criteria


@pytest.mark.parametrize(
    "gates, qubits, matching_instructions, non_matching_instructions",
    [
        (None, 1, [Instruction(Gate.H(), 1)], [Instruction(Gate.CNot(), [0, 1])]),
        (
            None,
            None,
            [Instruction(Gate.H(), 1), Instruction(Gate.CNot(), [0, 1])],
            [Instruction(Observable.X, 0)],
        ),
        (
            Gate.H,
            range(3),
            [Instruction(Gate.H(), 0), Instruction(Gate.H(), 1)],
            [
                Instruction(Gate.H(), 3),
                Instruction(Gate.I(), 1),
                [Instruction(Gate.H(), 0)],
            ],
        ),
        (Gate.H, 1, [Instruction(Gate.H(), 1)], [Instruction(Gate.H(), 0)]),
        ([Gate.H], [1], [Instruction(Gate.H(), 1)], [Instruction(Gate.H(), 0)]),
        (
            [Gate.CNot],
            [0, 1],
            [Instruction(Gate.CNot(), [0, 1])],
            [Instruction(Gate.CNot(), [1, 0])],
        ),
        (
            [Gate.CNot],
            [[0, 1], [1, 2]],
            [Instruction(Gate.CNot(), [0, 1]), Instruction(Gate.CNot(), [1, 2])],
            [Instruction(Gate.CNot(), [1, 0])],
        ),
        (
            [Gate.I, Gate.H],
            range(3),
            [Instruction(Gate.H(), 0), Instruction(Gate.I(), 2)],
            [Instruction(Gate.H(), 3), Instruction(Gate.X(), 1)],
        ),
        (
            Gate.H,
            None,
            [Instruction(Gate.H(), 0), Instruction(Gate.H(), 10)],
            [Instruction(Gate.I(), 1), Instruction(Gate.X(), 3)],
        ),
        (
            Gate.H,
            [],
            [Instruction(Gate.H(), 0), Instruction(Gate.H(), 10)],
            [Instruction(Gate.I(), 1), Instruction(Gate.X(), 3)],
        ),
    ],
)
def test_matcher(gates, qubits, matching_instructions, non_matching_instructions):
    criteria = GateCriteria(gates=gates, qubits=qubits)
    for instruction in matching_instructions:
        assert criteria.instruction_matches(instruction)
    for instruction in non_matching_instructions:
        assert not criteria.instruction_matches(instruction)


@pytest.mark.parametrize(
    "gates, qubits",
    [
        (Gate.CNot, [[0, 1], 2]),
    ],
)
@pytest.mark.xfail(raises=TypeError)
def test_invalid_type_params(gates, qubits):
    GateCriteria(gates=gates, qubits=qubits)


@pytest.mark.parametrize(
    "gates, qubits",
    [
        ([Gate.H, Gate.CNot], 1),
        (Gate.CNot, [[0, 1], [2]]),
    ],
)
@pytest.mark.xfail(raises=ValueError)
def test_invalid_value_params(gates, qubits):
    GateCriteria(gates=gates, qubits=qubits)


def test_representation():
    criteria = GateCriteria(gates=[Gate.I], qubits=0)
    str_representation = criteria.__repr__()
    assert str_representation == "GateCriteria(gates={'I'}, qubits={0})"


def test_string():
    criteria = GateCriteria(gates=[Gate.I], qubits=0)
    str_representation = criteria.__str__()
    assert str_representation == "GateCriteria({'I'}, {0})"


def test_get_keys_for_unknown_keytypes():
    criteria = GateCriteria(gates=[Gate.I], qubits=0)
    result = criteria.get_keys(CriteriaKey.UNITARY_GATE)
    assert len(result) == 0


@pytest.mark.parametrize(
    "criteria0, criteria1",
    [
        (GateCriteria(Gate.H, range(3)), GateCriteria(Gate.H, range(3))),
        (GateCriteria(Gate.H, [0, 1, 2]), GateCriteria(Gate.H, range(3))),
        (GateCriteria(Gate.H, [1, 2, 0]), GateCriteria(Gate.H, range(3))),
        (GateCriteria(Gate.H), GateCriteria(Gate.H, None)),
        (
            GateCriteria([Gate.H, Gate.I], range(3)),
            GateCriteria([Gate.I, Gate.H], range(3)),
        ),
    ],
)
def test_equal_criteria(criteria0, criteria1):
    assert criteria0 == criteria1


@pytest.mark.parametrize(
    "criteria0, criteria1",
    [
        (GateCriteria(Gate.H, range(3)), GateCriteria(Gate.I, range(3))),
        (GateCriteria(Gate.H, [1, 2, 3]), GateCriteria(Gate.H, range(3))),
        (GateCriteria(Gate.H), GateCriteria(Gate.H, range(3))),
        (GateCriteria(Gate.H, range(3)), float(3)),
        (GateCriteria(Gate.H, range(3)), ObservableCriteria(Observable.X, range(3))),
    ],
)
def test_not_equal_criteria(criteria0, criteria1):
    assert criteria0 != criteria1
