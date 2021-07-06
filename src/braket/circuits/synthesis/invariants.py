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

from braket.circuits.synthesis.constants import magic_basis
from braket.circuits.synthesis.predicates import is_unitary
from braket.circuits.synthesis.util import char_poly, to_su
from braket.circuits.gates import Y

# Pauli Y
y = Y().to_matrix()


def makhlin_invariants(
    U: np.ndarray, validate_input: bool = True, atol: float = 1e-8, rtol: float = 1e-5
) -> np.dtype:
    """
    Calculate the Makhlin invariants of a 2q gate.

    Args:
        U (np.ndarray): matrix to calculate the Makelin invariant.
        validate_input (bool): if validate input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.

    Returns:
        makhlin_invariants (np.dtype): the calculated Makhlin invariants.
    """

    if validate_input:
        is_unitary(U, raise_exception=True)

    U_magic = magic_basis.conj().T @ U @ magic_basis
    det = np.linalg.det(U_magic)
    m = U_magic.T @ U_magic

    makhlin_invariants = (
        np.real(np.trace(m) ** 2 / (16 * det)),
        np.imag(np.trace(m) ** 2 / (16 * det)),
        np.real((np.trace(m) ** 2 - np.trace(m @ m)) / (4 * det)),
    )

    return makhlin_invariants


def gamma_invariants(
    U: np.ndarray, validate_input: bool = True, atol: float = 1e-8, rtol: float = 1e-5
) -> np.dtype:
    """
    Calculate the gamma invariants of a 2q gate, first defined in
    Reference 1 & 2.

    References:
    1. Recognizing Small-Circuit Structure in Two-Qubit Operators
    and Timing Hamiltonians to Compute Controlled-Not Gates,
    Vivek V. Shende, Stephen S. Bullock, Igor L. Markov,
    arXiv:quant-ph/0308045
    2. Minimal Universal Two-qubit Quantum Circuits,
    Vivek V. Shende, Igor L. Markov, Stephen S. Bullock,
    arXiv:quant-ph/0308033

    Args:
        U (np.ndarray): matrix to calculate the gamma invariants.
        validate_input (bool): if validate input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.

    Returns:
        gamma_invariants (np.dtype): the calculated gamma invariants.
    """
    if validate_input:
        is_unitary(U, atol=atol, rtol=rtol)

    U = to_su(U)

    gamma = U @ np.kron(y, y) @ U.T @ np.kron(y, y)
    gamma_invariants = char_poly(gamma)

    return gamma_invariants
