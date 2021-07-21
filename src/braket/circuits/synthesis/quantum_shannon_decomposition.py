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
from scipy.linalg import cossin, eig

from braket.circuits.synthesis.one_qubit_decomposition import OneQubitDecomposition
from braket.circuits.synthesis.two_qubit_decomposition import TwoQubitDecomposition

def qsd_decompose(U: np.ndarray,
                  validate_input: bool = True,
                  atol: float):
    """
    Perform Quantum Shannon decomposition.

    Args:
        U (np.ndarray): input unitary matrix to decompose.
        validate_input (bool): if check input.
        atol (float): absolute tolerance parameter.
        rtol (float): relative tolerance parameter.

    Returns:
        circ (braket.circuits.Circuit): The decomposed circuit.
    """
    dim = U.shape[0]

    if validate_input:
        is_unitary(U, raise_exception=True)
        
        if (dim & (dim-1) != 0) or dim == 0:
            raise ValueError("Input matrix does not have valid dimension.")
        

    u, cs, vdh = cossin(U, p= dim // 2, q= dim // 2)

    u11 = u[:q_num1, :q_num1]
    u12 = u[q_num1:, q_num1:]
    u21 = vdh[:q_num1, :q_num1]
    u22 = vdh[q_num1:, q_num1:]

    d1, v1 = np.linalg.eig(u11 @ u12.conj().T)
    d2, v2 = np.linalg.eig(u21 @ u22.conj().T)
    d1 = np.sqrt(d1)
    d2 = np.sqrt(d2)
    v1 = v1.conj().T
    v2 = v2.conj().T

    w1 = d1 @ v1.conj.T() @ u12
    w2 = d2 @ v2.conj.T() @ u22

    






class QuantumShannonDecomposition:
    """
    Quantum Shannon decomposition of arbitrary unitaries.

    Attributes:
        TODO
    """

    def __init__(self, U: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5):

        self.atol = atol
        self.rtol = rtol
        self.U = U

        self.build(U)

    def build(self, U: np.ndarray):

        is_unitary(U, raise_exception=True)

        


