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

from braket.program_sets.parameter_sets import ParameterSets


def test_dict():
    parameter_sets = ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]})
    assert parameter_sets.as_dict() == {"theta": [1, 2, 3], "phi": [4, 5, 6]}
    assert len(parameter_sets) == 3


def test_list():
    parameter_sets = ParameterSets([
        {"theta": 1, "phi": 4},
        {"theta": 2, "phi": 5},
        {"theta": 3, "phi": 6},
    ])
    assert parameter_sets.as_dict() == {"theta": [1, 2, 3], "phi": [4, 5, 6]}
    assert len(parameter_sets) == 3


def test_keys_values():
    parameter_sets = ParameterSets(keys=("theta", "phi"), values=np.array([[1, 2, 3], [4, 5, 6]]))
    assert parameter_sets.as_dict() == {"theta": [1, 2, 3], "phi": [4, 5, 6]}
    assert len(parameter_sets) == 3


def test_kwargs():
    parameter_sets = ParameterSets(theta=[1, 2, 3], phi=[4, 5, 6])
    assert parameter_sets.as_dict() == {"theta": [1, 2, 3], "phi": [4, 5, 6]}
    assert len(parameter_sets) == 3


def test_other_parameter_sets():
    parameter_sets = ParameterSets(ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]}))
    assert parameter_sets.as_dict() == {"theta": [1, 2, 3], "phi": [4, 5, 6]}
    assert len(parameter_sets) == 3


def test_empty():
    parameter_sets = ParameterSets()
    assert parameter_sets.as_dict() is None
    assert len(parameter_sets) == 0


def test_add():
    parameter_sets = (
        ParameterSets(keys=("theta", "phi"), values=np.array([[1, 2], [8, 9]]))
        + [{"theta": 3, "phi": 10}, {"theta": 4, "phi": 11}]
        + {"theta": [5, 6, 7], "phi": [12, 13, 14]}
    )
    assert parameter_sets.as_dict() == {
        "theta": [1, 2, 3, 4, 5, 6, 7],
        "phi": [8, 9, 10, 11, 12, 13, 14],
    }
    assert len(parameter_sets) == 7


def test_equality():
    assert ParameterSets(theta=[1, 2, 3], phi=[4, 5, 6]) == ParameterSets(
        keys=("theta", "phi"), values=np.array([[1, 2, 3], [4, 5, 6]])
    )
    assert ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]}) == [
        {"theta": 1, "phi": 4},
        {"theta": 2, "phi": 5},
        {"theta": 3, "phi": 6},
    ]
    assert ParameterSets(keys=("theta", "phi"), values=np.array([[1, 2, 3], [4, 5, 6]])) != [
        {"theta": 1, "phi": 4},
        {"theta": 2, "phi": 5},
        {"theta": 3, "phi": 7},
    ]
    assert ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]}) != "foo"


def test_parameter_sets_wrong_type():
    with pytest.raises(TypeError):
        ParameterSets(1234)


def test_inputs_and_keys():
    with pytest.raises(ValueError):
        ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]}, keys=["lam"])


def test_inputs_and_values():
    with pytest.raises(ValueError):
        ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]}, values=[[7, 8, 9]])


def test_inputs_and_kwargs():
    with pytest.raises(ValueError):
        ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]}, lam=[7, 8, 9])


def test_kwargs_and_keys():
    with pytest.raises(ValueError):
        ParameterSets(theta=[1, 2, 3], phi=[4, 5, 6], keys=["lam"])


def test_kwargs_and_values():
    with pytest.raises(ValueError):
        ParameterSets(theta=[1, 2, 3], phi=[4, 5, 6], values=[[7, 8, 9]])


def test_keys_values_mismatch():
    with pytest.raises(ValueError):
        ParameterSets(theta=[1, 2, 3], phi=[4, 5])


def test_keys_no_values():
    with pytest.raises(ValueError):
        ParameterSets(keys=("theta", "phi"))


def test_values_no_keys():
    with pytest.raises(ValueError):
        ParameterSets(values=np.array([[1, 2, 3], [4, 5, 6]]))


def test_list_mismatched_missing():
    with pytest.raises(ValueError):
        ParameterSets([{"theta": 1, "phi": 4}, {"theta": 2, "phi": 5}, {"theta": 3}])


def test_list_mismatched_extra():
    with pytest.raises(ValueError):
        ParameterSets([{"theta": 1}, {"theta": 2}, {"theta": 3, "phi": 6}])


def test_dict_mismatched():
    with pytest.raises(ValueError):
        ParameterSets({"theta": [1, 2, 3], "phi": [4, 5]})


def test_kwargs_mismatched():
    with pytest.raises(ValueError):
        ParameterSets({"theta": [1, 2, 3], "phi": [4, 5]})


def test_add_mismatch():
    with pytest.raises(ValueError):
        ParameterSets({"theta": [1, 2, 3], "phi": [4, 5, 6]}) + [{"theta": 3}, {"theta": 10}]
