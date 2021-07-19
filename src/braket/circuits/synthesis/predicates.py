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


def is_diag(
    M: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
) -> bool:
    """
    Find out if a matrix is diagonal.

    Args:
        M (np.ndarray): matrix to check.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        diag (bool): True if U is diagonal and False otherwise.
    """

    pred = np.allclose(M - np.diag(np.diagonal(M)), np.zeros_like(M), atol=atol, rtol=rtol)

    if raise_exception and not pred:
        raise ValueError(f"{M} is not diagonal.")

    return pred


def commute(
    M1: np.ndarray,
    M2: np.ndarray,
    atol: float = 1e-8,
    rtol: float = 1e-5,
    raise_exception: bool = False,
) -> bool:
    """
    Find out if matrix a, b commute.

    Args:
        M1 (np.ndarray): first matrix to check.
        M2 (np.ndarray): second matrix to check.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        pred (bool): True if M1, M2 commute and False otherwise.
    """

    pred = np.allclose(M1 @ M2 - M2 @ M1, 0, atol=atol, rtol=rtol)

    if raise_exception and not pred:
        raise ValueError(f"{M1}, {M2} do not commute.")

    return pred


def is_unitary(
    U: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
) -> bool:
    """
    Find out if matrix U is unitary.

    Args:
        U (np.ndarray): second matrix to check.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        pred (bool): True if U is unitary otherwise False.
    """
    pred = np.shape(U)[0] == np.shape(U)[1] and np.allclose(
        np.linalg.det(U.conj().T @ U), 1, atol=atol, rtol=rtol
    )

    if raise_exception and not pred:
        raise ValueError(f"{U} has to be unitary.")

    return pred


def is_hermitian(
    U: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
) -> bool:
    """
    Find out if matrix U is hermitian.

    Args:
        U (np.ndarray): second matrix to check.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        pred (bool): True if U is hermitian otherwise False.
    """

    pred = np.allclose(U, U.conj().T, atol=atol, rtol=rtol)

    if raise_exception and not pred:
        raise ValueError(f"{U} has to be hermitian.")

    return pred


def eq_up_to_phase(
    U1, U2, atol: float = 1e-8, rtol: float = 1e-5, raise_exception: bool = False
) -> bool:
    """
    Find out if U1 and U2 are equivalent up to a global phase.

    Args:
        U1 (np.ndarray): first 2x2 matrix to compare.
        U2 (np.ndarray): second 2x2 matrix to compare.
        atol (np.dtype): absolute tolerance parameter.
        rtol (np.dtype): relative tolerance parameter.
        raise_exception (bool): if raise an exception
        when condition is not met.

    Returns:
        eq (bool): True if U1 and U2 are equal up to a global phase.
    """

    i, j = np.unravel_index(np.argmax(abs(U1), axis=None), U1.shape)
    phase = U2[i, j] / U1[i, j]

    eq = np.allclose(U1 * phase, U2, atol=atol, rtol=rtol)

    if raise_exception and not eq:
        raise ValueError(f"{U1} and {U2} are not equal up to a phase")

    return eq
