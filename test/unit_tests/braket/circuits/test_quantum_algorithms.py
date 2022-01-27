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

from braket.circuits import Circuit, QuantumAlgorithm, QuantumOperator


@pytest.fixture
def algorithm():
    return QuantumAlgorithm.QFT(qubit_set=[0, 1])


def test_is_operator(algorithm):
    assert isinstance(algorithm, QuantumOperator)


def test_algo_decompose(algorithm):
    circ = algorithm.decompose()
    expected = Circuit().h(0).cphaseshift(0, 1, 0.5 * np.pi).h(1)

    assert circ == expected
