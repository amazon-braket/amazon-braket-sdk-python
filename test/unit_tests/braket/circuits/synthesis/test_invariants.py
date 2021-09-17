# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import numpy as np

import braket.circuits.synthesis.invariants as inv
from braket.circuits.gates import CNot, CZ, CY, ISwap, Swap

cnot = CNot().to_matrix()
cz = CZ().to_matrix()
cy = CY().to_matrix()
iswap = ISwap().to_matrix()
swap = Swap().to_matrix()


@pytest.mark.parametrize(
    "unitary_test_cases, expected",
    [(cnot, (0, 0, 1)), (cz, (0, 0, 1)), (cy, (0, 0, 1)), (iswap, (0, 0, -1)), (swap, (-1, 0, -3))],
)
def test_makhlin(unitary_test_cases, expected):
    m_inv = inv.makhlin_invariants(unitary_test_cases)
    assert np.allclose(m_inv, expected)


@pytest.mark.parametrize(
    "unitary_test_cases, expected",
    [
        (cnot, [1, 0, 2, 0, 1]),
        (cz, [1, 0, 2, 0, 1]),
        (cy, [1, 0, 2, 0, 1]),
        (iswap, [1, 0, -2, 0, 1]),
        (swap, [1, 4j, -6, -4j, 1]),
    ],
)
def test_makhlin(unitary_test_cases, expected):
    m_inv = inv.gamma_invariants(unitary_test_cases)
    assert np.allclose(m_inv, expected)
