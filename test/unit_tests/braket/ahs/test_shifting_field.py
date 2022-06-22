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

import pytest

from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.shifting_field import ShiftingField


@pytest.fixture
def default_shifting_field():
    return ShiftingField(Mock())


def test_create():
    mock0 = Mock()
    field = ShiftingField(magnitude=mock0)
    assert mock0 == field.magnitude


def test_add_hamiltonian(default_shifting_field):
    expected = [default_shifting_field, Mock(), Mock(), Mock()]
    result = expected[0] + Hamiltonian([expected[1], expected[2], expected[3]])
    assert result.terms == expected


def test_add_to_hamiltonian(default_shifting_field):
    expected = [Mock(), Mock(), Mock(), default_shifting_field]
    result = Hamiltonian([expected[0], expected[1], expected[2]]) + expected[3]
    assert result.terms == expected


def test_add_to_other():
    field0 = ShiftingField(Mock())
    field1 = ShiftingField(Mock())
    result = field0 + field1
    assert type(result) is Hamiltonian
    assert result.terms == [field0, field1]


def test_add_to_self(default_shifting_field):
    result = default_shifting_field + default_shifting_field
    assert type(result) is Hamiltonian
    assert result.terms == [default_shifting_field, default_shifting_field]


def test_iadd_to_other(default_shifting_field):
    expected = [Mock(), Mock(), Mock(), default_shifting_field]
    other = Hamiltonian([expected[0], expected[1], expected[2]])
    other += expected[3]
    assert other.terms == expected


@pytest.mark.xfail(raises=ValueError)
def test_iadd_to_itself(default_shifting_field):
    default_shifting_field += Hamiltonian(Mock())
