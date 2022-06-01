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

from braket.circuits import Observable, ResultType
from braket.circuits.noise_model import CriteriaKey, CriteriaKeyResult, ObservableCriteria


@pytest.mark.parametrize(
    "observables, qubits",
    [
        (None, range(3)),
        (None, None),
        (Observable.X, range(3)),
        ([Observable.X], range(3)),
        ([Observable.X, Observable.Y], range(3)),
        (Observable.X, 1),
        ([Observable.X], [1]),
        ([Observable.X, Observable.Y], [1, 0]),
        (Observable.X, None),
    ],
)
def test_happy_case(observables, qubits):
    criteria = ObservableCriteria(observables=observables, qubits=qubits)
    assert criteria.applicable_key_types() == [
        CriteriaKey.OBSERVABLE,
        CriteriaKey.QUBIT,
    ]
    if observables is None:
        assert CriteriaKeyResult.ALL == criteria.get_keys(CriteriaKey.OBSERVABLE)
    else:
        assert Observable.X in criteria.get_keys(CriteriaKey.OBSERVABLE)
    if qubits is None:
        assert CriteriaKeyResult.ALL == criteria.get_keys(CriteriaKey.QUBIT)
    else:
        assert 1 in criteria.get_keys(CriteriaKey.QUBIT)


@pytest.mark.parametrize(
    "observables, qubits",
    [
        (None, range(3)),
        (None, None),
        (Observable.X, range(3)),
        ([Observable.X], 1),
        ([Observable.X], [1]),
        ([Observable.X], [[1]]),
        ([Observable.X, Observable.Y], range(3)),
        ([Observable.X, Observable.Y], None),
    ],
)
def test_serialization(observables, qubits):
    test_criteria = ObservableCriteria(observables=observables, qubits=qubits)
    serialized_criteria = test_criteria.to_dict()
    assert serialized_criteria["__class__"] == "ObservableCriteria"
    assert "observables" in serialized_criteria
    assert "qubits" in serialized_criteria
    deserialized_criteria = ObservableCriteria.from_dict(serialized_criteria)
    assert test_criteria == deserialized_criteria


@pytest.mark.parametrize(
    "observables, qubits, matching_result_type, non_matching_result_type",
    [
        (
            None,
            range(3),
            [
                ResultType.Sample(Observable.X(), 0),
                ResultType.Sample(Observable.Z(), 2),
            ],
            [ResultType.Sample(Observable.X(), 4)],
        ),
        (
            None,
            None,
            [
                ResultType.Sample(Observable.X(), 0),
                ResultType.Sample(Observable.Z(), 10),
            ],
            [ResultType.Probability(0)],
        ),
        (
            Observable.X,
            range(3),
            [
                ResultType.Sample(Observable.X(), 0),
                ResultType.Sample(Observable.X(), 1),
                ResultType.Sample(Observable.X()),
            ],
            [
                ResultType.Sample(Observable.X(), 3),
                ResultType.Sample(Observable.Y(), 1),
            ],
        ),
        (
            Observable.X,
            1,
            [ResultType.Sample(Observable.X(), 1)],
            [ResultType.Sample(Observable.X(), 0)],
        ),
        (
            [Observable.X],
            [1],
            [ResultType.Sample(Observable.X(), 1)],
            [ResultType.Sample(Observable.X(), 0)],
        ),
        (
            [Observable.X, Observable.Y],
            range(3),
            [
                ResultType.Sample(Observable.X(), 0),
                ResultType.Sample(Observable.Y(), 2),
            ],
            [
                ResultType.Sample(Observable.X(), 3),
                ResultType.Sample(Observable.Z(), 1),
            ],
        ),
        (
            Observable.X,
            None,
            [
                ResultType.Sample(Observable.X(), 0),
                ResultType.Sample(Observable.X(), 10),
            ],
            [
                ResultType.Sample(Observable.Y(), 1),
                ResultType.Sample(Observable.Z(), 3),
            ],
        ),
        (
            Observable.X,
            [],
            [
                ResultType.Sample(Observable.X(), 0),
                ResultType.Sample(Observable.X(), 10),
            ],
            [
                ResultType.Sample(Observable.Y(), 1),
                ResultType.Sample(Observable.Z(), 3),
            ],
        ),
    ],
)
def test_matcher(observables, qubits, matching_result_type, non_matching_result_type):
    criteria = ObservableCriteria(observables=observables, qubits=qubits)
    for result_type in matching_result_type:
        assert criteria.result_type_matches(result_type)
    for instruction in non_matching_result_type:
        assert not criteria.result_type_matches(instruction)


@pytest.mark.parametrize(
    "observables, qubits",
    [
        ([Observable.X], [[0, 1]]),
    ],
)
@pytest.mark.xfail(raises=ValueError)
def test_invalid_params(observables, qubits):
    ObservableCriteria(observables=observables, qubits=qubits)


def test_representation():
    criteria = ObservableCriteria(observables=[Observable.X], qubits=0)
    str_representation = criteria.__repr__()
    assert str_representation == "ObservableCriteria(observables={'X'}, qubits={0})"


def test_string():
    criteria = ObservableCriteria(observables=[Observable.X], qubits=0)
    str_representation = criteria.__str__()
    assert str_representation == "ObservableCriteria({'X'}, {0})"


def test_get_keys_for_unknown_keytypes():
    criteria = ObservableCriteria(observables=[Observable.X], qubits=0)
    result = criteria.get_keys(CriteriaKey.UNITARY_GATE)
    assert len(result) == 0
