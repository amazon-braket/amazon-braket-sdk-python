# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from scipy.linalg import block_diag

from braket.circuits.gates import X, Y, Z, Rx, Ry, Rz
from braket.circuits.synthesis.multiplexors import pauli_multiplexor

PI = np.pi

@pytest.mark.parametrize(
    "angles, control_bits, target_bit, reverse",
    [([0.2 * PI, 0.4 * PI], [1], 0, False),
     ([0.3 * PI, 0.5 * PI], [1], 0, True),
     ([0.4 * PI, 0.2 * PI, 0.7 * PI, 0.8 * PI], [2, 1], 0, False),
     ([0.4 * PI, 0.2 * PI, 0.7 * PI, 0.8 * PI], [2, 1], 0, True),
     ([0.1 * PI, 1.2 * PI, 0.3 * PI, 1.7 * PI,
       1.1 * PI, 1.4 * PI, 0.6 * PI, 0.9 * PI], [3, 2, 1], 0, False),
    ]
)
def test_multiplexed_ry(angles, control_bits, target_bit, reverse):
    rotation_matrices = [Ry(angle).to_matrix() for angle in angles]
    expected = block_diag(*rotation_matrices)
    circ = pauli_multiplexor(Y(), angles, control_bits, target_bit, reverse=reverse)
    assert np.allclose(circ.as_unitary(), expected)


@pytest.mark.parametrize(
    "angles, control_bits, target_bit, reverse",
    [([0.4 * PI, 0.2 * PI, 0.7 * PI, 0.8 * PI], [1, 2], 0, False)]
    )
def test_multiplexed_ry_control_order(angles, control_bits, target_bit, reverse): 
    swapped_angles = angles.copy()
    swapped_angles[1], swapped_angles[2] = swapped_angles[2], swapped_angles[1]
    rotation_matrices = [Ry(angle).to_matrix() for angle in swapped_angles]
    expected = block_diag(*rotation_matrices)
    circ = pauli_multiplexor(Y(), angles, control_bits, target_bit, reverse=reverse)
    assert np.allclose(circ.as_unitary(), expected)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize(
    "angles, control_bits, target_bit, reverse",
    [([0.2 * PI, 0.4 * PI], [2, 1], 0, False),
     ([0.2 * PI], [1], 0, False)]
)
def test_multiplexed_fail(angles, control_bits, target_bit, reverse):
    circ = pauli_multiplexor(Y(), angles, control_bits, target_bit, reverse=reverse)

@pytest.mark.parametrize(
    "angles, control_bits, target_bit, reverse",
    [([0.2 * PI, 0.4 * PI], [1], 0, False),
     ([0.3 * PI, 0.5 * PI], [1], 0, True),
     ([0.4 * PI, 0.2 * PI, 0.7 * PI, 0.8 * PI], [2, 1], 0, False),
     ([0.4 * PI, 0.2 * PI, 0.7 * PI, 0.8 * PI], [2, 1], 0, True),
     ([0.1 * PI, 1.2 * PI, 0.3 * PI, 1.7 * PI,
       1.1 * PI, 1.4 * PI, 0.6 * PI, 0.9 * PI], [3, 2, 1], 0, False),
    ]
)
def test_multiplexed_rz(angles, control_bits, target_bit, reverse):
    rotation_matrices = [Rz(angle).to_matrix() for angle in angles]
    expected = block_diag(*rotation_matrices)
    circ = pauli_multiplexor(Z(), angles, control_bits, target_bit, reverse=reverse)
    assert np.allclose(circ.as_unitary(), expected)
