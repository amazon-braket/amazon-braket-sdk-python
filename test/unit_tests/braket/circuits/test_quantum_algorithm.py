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

from braket.circuits import Gate, QuantumAlgorithm, QuantumOperator


@pytest.fixture
def algorithm():
    return QuantumAlgorithm(qubit_set=[0, 1], ascii_symbols=["*", "Test"])


def test_is_operator(algorithm):
    assert isinstance(algorithm, QuantumOperator)


def test_qubit_set(algorithm):
    expected = [0, 1]
    assert algorithm.qubit_set == expected


@pytest.mark.xfail(raises=NotImplementedError)
def test_algo_generator(algorithm):
    # Tox was complaining unless it tested this proteced member?
    algorithm._generator(algorithm.qubit_set)


@pytest.mark.xfail(raises=NotImplementedError)
def test_algo_decompose(algorithm):
    algorithm.decompose()


def test_algo_equivalence():
    algo_1 = QuantumAlgorithm.QFT(qubit_set=[0, 1])
    algo_2 = QuantumAlgorithm.QFT(qubit_set=[0, 1])
    non_algo = Gate.H()

    assert algo_1 == algo_1
    assert algo_1 == algo_2
    assert algo_1 != non_algo
