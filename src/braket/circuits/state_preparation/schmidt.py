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
from typing import List

from braket.circuits import Circuit
from braket.circuits.gate import Gate

ABS_TOL = 1E-7 # Tolerance of absolute error in state normalization.

def schmidt_decomposition(qstate: np.ndarray, qubits: List[int]) -> List[Type[Gate]]
    """
    Using Schmidt decomposition to find the circuit to prepare
    an arbitrary quantum states.
    
    Args:
        qstate (ndarray): The quantum state to be prepared.
        qubits (list): The qubits to prepare quantum states on.

    Returns:
        ret_gates (list): The gate sequence to prepare the quantum state.
    """

    if np.shape(qstate) != (2,) or np.shape(qstate)[0] != 2 ** len(qubits):
        raise ValueError("Incorrect dimension of the state vector or incorrect qubit counts.")

    if not math.isclose(np.sum(np.absolute(qstate) ** 2), 1.0, abs_tol=ABS_TOL):
        raise ValueError("Quantum state to prepare is not normalized.")

    dim = 2 ** len(qubits)
    dim_1 = 2 ** (len(qubits) // 2)
    dim_2 = dim // dim_1

    qsquare = qstate.reshape((dim_1, dim_2))



        

