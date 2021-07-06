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

import math
import numpy as np
from scipy.linalg import expm
import pytest
import random

import braket.circuits.synthesis.predicates as predicates
from braket.circuits.gates import X, Y, Z, H, S, CNot, CZ

x = X().to_matrix()
y = Y().to_matrix()
z = Z().to_matrix()
h = H().to_matrix()
s = S().to_matrix()
cx = CNot().to_matrix()
cz = CZ().to_matrix()

partial_rank_diag_3d = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 0]], dtype=np.complex128)

partial_rank_3d = np.array([[3, 1, 0], [1, 3, 0], [0, 0, 0]], dtype=np.complex128)

partial_diag_numeric = np.array(
    [
        [2.00000000e00, 3.99346924e-16, 0.00000000e00],
        [3.54604637e-16, 4.00000000e00, 0.00000000e00],
        [0.00000000e00, 0.00000000e00, 0.00000000e00],
    ],
    dtype=np.complex128,
)

matrix_3d = np.array([[3, 1, 0], [1, 3, 0], [0, 0, 4]], dtype=np.complex128)

diag_matrix_3d = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 1]], dtype=np.complex128)

cx_re = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=np.complex128)

# Test is_diag function
@pytest.mark.parametrize(
    "diag_test_input, diag_test_output",
    [
        (x, False),
        (z, True),
        (y, False),
        (s, True),
        (partial_rank_diag_3d, True),
        (partial_rank_3d, False),
        (diag_matrix_3d, True),
        (matrix_3d, False),
        (partial_diag_numeric, True),
    ],
)
def test_diag(diag_test_input, diag_test_output):
    assert predicates.is_diag(diag_test_input) == diag_test_output


@pytest.mark.parametrize("diag_test_input", [x, y, partial_rank_3d])
@pytest.mark.xfail
def test_diag_edge_cases(diag_test_input):
    predicates.is_diag(diag_test_input, raise_exception=True)


# Test commute function
@pytest.mark.parametrize(
    "commute_test_input1, commute_test_input2, commute_test_output",
    [
        (x, y, False),
        (x, x, True),
        (cx, np.kron(z, np.eye(2)), True),
        (cx, np.kron(np.eye(2), x), True),
        (z, s, True),
    ],
)
def test_commute(commute_test_input1, commute_test_input2, commute_test_output):
    assert predicates.commute(commute_test_input1, commute_test_input2) == commute_test_output


@pytest.mark.parametrize(
    "commute_test_input1, commute_test_input2", [(x, y), (x, z), (y, z), (cx, y), (h, x), (h, cx)]
)
@pytest.mark.xfail
def test_commute_edge_cases(commute_test_input1, commute_test_input2):
    predicates.commute(commute_test_input1, commute_test_input2, raise_exception=True)


def u(a, b, c):
    return np.array(
        [
            [np.cos(0.5 * a), -np.exp(1j * c) * np.sin(0.5 * a)],
            [np.sin(0.5 * a) * np.exp(1j * b), np.cos(0.5 * a) * np.exp(1j * (b + c))],
        ],
        dtype=np.complex128,
    )


def random_kron_u():
    return np.kron(
        u(2 * np.pi * random.random(), 2 * np.pi * random.random(), 2 * np.pi * random.random()),
        u(2 * np.pi * random.random(), 2 * np.pi * random.random(), 2 * np.pi * random.random()),
    )


# Test is_unitary function
@pytest.mark.parametrize(
    "unitary_test, unitary_output",
    [(random_kron_u(), True) for _ in range(10)]
    + [
        (
            u(
                2 * np.pi * random.random(),
                2 * np.pi * random.random(),
                2 * np.pi * random.random(),
            ),
            True,
        )
        for _ in range(10)
    ]
    + [(matrix_3d, False), (diag_matrix_3d, False), (partial_rank_diag_3d, False)],
)
def test_is_unitary(unitary_test, unitary_output):
    assert predicates.is_unitary(unitary_test) == unitary_output
