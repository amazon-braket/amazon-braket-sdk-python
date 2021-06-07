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
import pytest

from braket.circuits import Circuit
import braket.circuits.state_preparation.basic as basic
from braket.devices import LocalSimulator

def _eq_up_to_global_phase(sv1:np.ndarray, sv2:np.ndarray) -> bool:
    """
    Helper function to determine if two state vectors are equal
    (up to a global phase).

    Args:
        sv1 (ndarray): First state vector to compare.
        sv2 (ndarray): Second state vector to compare.
    
    Return:
        eq (bool): If the two state vectors are equal
                   (up to a global phase).
    """
    
    non_zero_ind = np.nonzero(sv1)
    scalar = sv2[non_zero_ind] / sv1[non_zero_ind]
    sv1 = scalar * sv1

    return np.allclose(sv1, sv2)

@pytest.mark.parametrize("one_q_test_cases", [
    np.array([0, 1]),
    np.array([1, 0]),
    np.array([1j, 0]),
    np.array([1j, 0]),
    np.array([0, 1j]),
    np.array([0, np.exp(np.pi / 3)]),
    np.array([math.sqrt(2) * 0.5, math.sqrt(2) * 0.5]),
    np.array([math.sqrt(2) * 0.5, -math.sqrt(2) * 0.5]),
    np.array([math.sqrt(2) * 0.5, 1j * math.sqrt(2) * 0.5]),
    np.array([math.sqrt(2) * 0.5, -1j * math.sqrt(2) * 0.5]),
    np.array([0.6, 0.8]),
    np.array([0.6, 0.8j]),
    np.array([0.6j, -0.8j])
    ])


@pytest.fixture
def qubit_0():
    return [0]

def test_prepare_1q_state(one_q_test_cases, qubit_0):

    ret_gates = basic.prepare_1q_state(np.array([0, 1]), [0])

    circ = Circuit() 
    for i in ret_gates:
        circ += i
    circ.state_vector()

    device = LocalSimulator()
    result = device.run(circ).result()
    expect = result.result_types[0].value

    assert _eq_up_to_global_phase(expect, one_q_test_cases)
