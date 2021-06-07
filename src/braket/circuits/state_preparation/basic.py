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

import numpy as np
import math
from typing import List, Type

from braket.circuits import Circuit
from braket.circuits.gate import Gate
from braket.circuits.qubit import Qubit
from braket.circuits.gates import Ry, Rz

_ABS_TOL = 1E-6

def prepare_1q_state(qstate: np.ndarray, qubits: List[int]) -> List[Type[Gate]]:
    """
    Use a --Ry--Rz-- gate sequence to prepare
    arbitrary 1-qubit quantum states (up to a global phase).
    
    Args:
        qstate (ndarray): The quantum state to be prepared.
        qubits (list): The qubits to prepare quantum states on.

    Returns:
        ret_gates (list): The gate sequence to prepare the quantum state.

    Raises:
        ValueError: If incorrect quantum state dimension or incorrect
                    qubit count is given.
    """

    if len(qubits) != 1 or np.shape(qstate) != (2,):
        raise ValueError("Incorrect quantum state dimension or incorrect qubit count to initialize.")

    ret_gates = []

    theta = 2 * np.arccos(np.absolute(qstate[0]))

    if not math.isclose(theta, 0, abs_tol=_ABS_TOL):
        ret_gates.append(Ry.ry(Qubit(qubits[0]), theta)[0])
        
        phi = np.angle(qstate[1] / np.sin(theta))
        if (not math.isclose(np.sin(theta), 0, abs_tol=_ABS_TOL)) and (not math.isclose(phi, 0, abs_tol=_ABS_TOL)):
            ret_gates.append(Rz.rz(Qubit(qubits[0]), phi)[0])

    return ret_gates

def prepare_2q_state(qstate: np.ndarray, qubits: List[int]) -> List[Type[Gate]]:
    """
    Find the 2-qubit circuit to prepare
    an arbitrary 2-qubit quantum states
    (up to a global phase).
    
    Args:
        qstate (ndarray): The quantum state to be prepared.
        qubits (list): The qubits to prepare quantum states on.

    Returns:
        ret_gates (list): The gate sequence to prepare the quantum state.

    Raises:
        ValueError: If incorrect quantum state dimension or incorrect
                    qubit count is given.
    """

    if len(qubits) != 2 or np.shape(qstate) != (4,):
        raise ValueError("Incorrect quantum state dimension or incorrect qubit count to initialize.")


