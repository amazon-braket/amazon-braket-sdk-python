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

from braket.ahs.hamiltonian import Hamiltonian


def test_create():
    hamiltonian = Hamiltonian()
    assert hamiltonian.terms == []


def test_add():
    mocks = [Mock(), Mock(), Mock(), Mock()]
    result = Hamiltonian([mocks[0], mocks[1], mocks[2]]) + Hamiltonian([mocks[3]])
    assert result.terms == mocks


def test_iadd():
    mocks = [Mock(), Mock(), Mock(), Mock()]
    hamiltonian = Hamiltonian([mocks[0]])
    hamiltonian += Hamiltonian([mocks[1], mocks[2], mocks[3]])
    assert hamiltonian.terms == mocks


def test_discretize():
    mocks = [Mock(), Mock(), Mock()]
    mock_properties = Mock()
    hamiltonian = Hamiltonian(mocks)
    discretized_hamiltonian = hamiltonian.discretize(mock_properties)
    for index in range(len(mocks)):
        mocks[index].discretize.assert_called_with(mock_properties)
        assert discretized_hamiltonian.terms[index] == mocks[index].discretize.return_value
    assert hamiltonian is not discretized_hamiltonian
