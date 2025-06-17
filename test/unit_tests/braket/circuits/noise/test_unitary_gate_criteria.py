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

import numpy as np
import pytest

from braket.circuits import Gate, Instruction, Observable
from braket.circuits.gates import Unitary
from braket.circuits.noise_model import (
    CriteriaKey,
    CriteriaKeyResult,
    ObservableCriteria,
    UnitaryGateCriteria,
)


def h_unitary():
    return Unitary(Gate.H().to_matrix())


def i_unitary():
    return Unitary(Gate.I().to_matrix())


def x_unitary():
    return Unitary(Gate.X().to_matrix())


def cnot_unitary():
    return Unitary(Gate.CNot().to_matrix())


@pytest.mark.parametrize(
    "unitary, qubits",
    [
        (h_unitary(), range(3)),
        (h_unitary(), 1),
        (h_unitary(), None),
    ],
)
def test_happy_case(unitary, qubits):
    criteria = UnitaryGateCriteria(unitary=unitary, qubits=qubits)
    assert criteria.applicable_key_types() == [
        CriteriaKey.QUBIT,
        CriteriaKey.UNITARY_GATE,
    ]
    assert h_unitary().to_matrix().tobytes() in criteria.get_keys(CriteriaKey.UNITARY_GATE)
    if qubits is None:
        assert CriteriaKeyResult.ALL == criteria.get_keys(CriteriaKey.QUBIT)
    else:
        assert 1 in criteria.get_keys(CriteriaKey.QUBIT)


def test_serialization():
    test_criteria = UnitaryGateCriteria(unitary=h_unitary(), qubits=range(3))
    serialized_criteria = test_criteria.to_dict()
    assert serialized_criteria["__class__"] == "UnitaryGateCriteria"
    assert "unitary" in serialized_criteria
    assert "qubits" in serialized_criteria
    deserialized_criteria = UnitaryGateCriteria.from_dict(serialized_criteria)
    assert test_criteria == deserialized_criteria


@pytest.mark.parametrize(
    "unitary, qubits, matching_instructions, non_matching_instructions",
    [
        (
            h_unitary(),
            range(3),
            [
                Instruction(h_unitary(), 0),
                Instruction(h_unitary(), 1),
            ],
            [
                Instruction(Gate.H, 3),
                Instruction(h_unitary(), 3),
                Instruction(i_unitary(), 1),
                [Instruction(h_unitary(), 0)],
            ],
        ),
        (
            cnot_unitary(),
            [[0, 1]],
            [
                Instruction(cnot_unitary(), [0, 1]),
            ],
            [
                Instruction(Gate.CNot(), [0, 1]),
            ],
        ),
        (
            h_unitary(),
            1,
            [Instruction(h_unitary(), 1)],
            [Instruction(h_unitary(), 0)],
        ),
        (
            h_unitary(),
            None,
            [Instruction(h_unitary(), 0), Instruction(h_unitary(), 10)],
            [Instruction(i_unitary(), 1), Instruction(x_unitary(), 3)],
        ),
        (
            h_unitary(),
            [],
            [Instruction(h_unitary(), 0), Instruction(h_unitary(), 10)],
            [Instruction(i_unitary(), 1), Instruction(x_unitary(), 3)],
        ),
    ],
)
def test_matcher(unitary, qubits, matching_instructions, non_matching_instructions):
    criteria = UnitaryGateCriteria(unitary=unitary, qubits=qubits)
    for instruction in matching_instructions:
        assert criteria.instruction_matches(instruction)
    for instruction in non_matching_instructions:
        assert not criteria.instruction_matches(instruction)


@pytest.mark.parametrize(
    "unitary, qubits",
    [
        (None, 1),
        ([], 1),
        ([h_unitary()], 1),
        (np.zeros(15, dtype=int), 1),
    ],
)
@pytest.mark.xfail(raises=TypeError)
def test_invalid_params(unitary, qubits):
    UnitaryGateCriteria(unitary=unitary, qubits=qubits)


def test_representation():
    criteria = UnitaryGateCriteria(unitary=h_unitary(), qubits=0)
    str_representation = criteria.__repr__()
    assert (
        str_representation == "UnitaryGateCriteria(unitary=Unitary('qubit_count': 1), qubits={0})"
    )  # noqa


def test_string():
    criteria = UnitaryGateCriteria(unitary=h_unitary(), qubits=0)
    str_representation = criteria.__str__()
    assert (
        str_representation == "UnitaryGateCriteria(unitary=Unitary('qubit_count': 1), qubits={0})"
    )  # noqa


def test_get_keys_for_unknown_keytypes():
    criteria = UnitaryGateCriteria(unitary=h_unitary(), qubits=0)
    result = criteria.get_keys(CriteriaKey.GATE)
    assert len(result) == 0


@pytest.mark.parametrize(
    "criteria0, criteria1",
    [
        (
            UnitaryGateCriteria(h_unitary(), range(3)),
            UnitaryGateCriteria(h_unitary(), range(3)),
        ),
        (
            UnitaryGateCriteria(h_unitary(), [0, 1, 2]),
            UnitaryGateCriteria(h_unitary(), range(3)),
        ),
        (
            UnitaryGateCriteria(h_unitary(), [1, 2, 0]),
            UnitaryGateCriteria(h_unitary(), range(3)),
        ),
        (UnitaryGateCriteria(h_unitary()), UnitaryGateCriteria(h_unitary(), None)),
    ],
)
def test_equal_criteria(criteria0, criteria1):
    assert criteria0 == criteria1


@pytest.mark.parametrize(
    "criteria0, criteria1",
    [
        (
            UnitaryGateCriteria(h_unitary(), range(3)),
            UnitaryGateCriteria(i_unitary(), range(3)),
        ),
        (
            UnitaryGateCriteria(h_unitary(), [1, 2, 3]),
            UnitaryGateCriteria(h_unitary(), range(3)),
        ),
        (UnitaryGateCriteria(h_unitary()), UnitaryGateCriteria(h_unitary(), range(3))),
        (UnitaryGateCriteria(h_unitary(), range(3)), float(3)),
        (
            UnitaryGateCriteria(h_unitary(), range(3)),
            ObservableCriteria(Observable.X, range(3)),
        ),
    ],
)
def test_not_equal_criteria(criteria0, criteria1):
    assert criteria0 != criteria1
