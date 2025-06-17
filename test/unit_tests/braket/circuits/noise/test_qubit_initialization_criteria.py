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

from braket.circuits.noise_model import CriteriaKey, CriteriaKeyResult, QubitInitializationCriteria


@pytest.mark.parametrize(
    "qubits",
    [1, range(3), None, [1], [[1]]],
)
def test_happy_case(qubits):
    criteria = QubitInitializationCriteria(qubits=qubits)
    assert criteria.applicable_key_types() == [CriteriaKey.QUBIT]
    if qubits is None:
        assert CriteriaKeyResult.ALL == criteria.get_keys(CriteriaKey.QUBIT)
    else:
        assert 1 in criteria.get_keys(CriteriaKey.QUBIT)


@pytest.mark.parametrize(
    "qubits",
    [
        1,
        range(3),
        [1],
        [[1]],
        [0, 1],
        [[1, 2]],
        [[3, 4], [5, 6]],
        None,
    ],
)
def test_serialization(qubits):
    test_criteria = QubitInitializationCriteria(qubits=qubits)
    serialized_criteria = test_criteria.to_dict()
    assert serialized_criteria["__class__"] == "QubitInitializationCriteria"
    assert "qubits" in serialized_criteria
    deserialized_criteria = QubitInitializationCriteria.from_dict(serialized_criteria)
    assert test_criteria == deserialized_criteria


@pytest.mark.parametrize(
    "qubits, input_qubits, expected_result",
    [
        (
            range(3),
            [0, 1, 2, [2], [[2]], 4, [5], [[6]], [0, 1]],
            {0, 1, 2},
        ),
        (
            None,
            [0, 1, 2, [2], [[2]], 4, [5], [[6]], [0, 1]],
            {0, 1, 2, 4, 5, 6},
        ),
    ],
)
def test_matcher(qubits, input_qubits, expected_result):
    criteria = QubitInitializationCriteria(qubits=qubits)
    result = criteria.qubit_intersection(input_qubits)
    assert result == expected_result


@pytest.mark.parametrize(
    "qubits",
    [
        ([[0, 1], 2]),
    ],
)
@pytest.mark.xfail(raises=TypeError)
def test_invalid_param_types(qubits):
    QubitInitializationCriteria(qubits=qubits)


@pytest.mark.parametrize(
    "qubits",
    [
        ([[0, 1], [2]]),
    ],
)
@pytest.mark.xfail(raises=ValueError)
def test_invalid_params(qubits):
    QubitInitializationCriteria(qubits=qubits)


def test_representation():
    criteria = QubitInitializationCriteria(qubits=range(4))
    str_representation = criteria.__repr__()
    assert str_representation == "QubitInitializationCriteria(qubits={0, 1, 2, 3})"


def test_string():
    criteria = QubitInitializationCriteria(qubits=range(4))
    str_representation = criteria.__str__()
    assert str_representation == "QubitInitializationCriteria({0, 1, 2, 3})"


def test_get_keys_for_unknown_keytypes():
    criteria = QubitInitializationCriteria(qubits=0)
    result = criteria.get_keys(CriteriaKey.UNITARY_GATE)
    assert len(result) == 0
