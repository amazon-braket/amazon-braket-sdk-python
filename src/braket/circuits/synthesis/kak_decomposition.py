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
from scipy.linalg import expm
from typing import Tuple

from braket.circuits.synthesis.util import (diagonalize_two_matrices_with_hermitian_products,
                                            decompose_one_qubit_product,
                                            magic_basis,
                                            is_diag)

from braket.circuits.gates import X, Y, Z

x = X.to_matrix()
y = Y.to_matrix()
z = Z.to_matrix()

kak_theta_transform = np.array([[1,  1, -1,  1], 
                              [1,  1,  1, -1],
                              [1, -1, -1, -1],
                              [1, -1,  1,  1]])

def odo_decomposition(U: np.ndarray,
                      validate_input: bool=True,
                      atol: float=1E-8,
                      rtol: float=1E-5) -> Tuple[np.ndarray]:

    """
    Decompose a unitary matrix U into QL * exp(i * theta) * QR.T,
    where QL, QR are orthogonal matrices and theta is a 1-d vector
    of angles. This decomposition can be derived from the
    Eckhart-Young simultaneuous diagonalization of Hermitian matrices.
    We call it orthogonal-diagonal-orthogonal (odo) decomposition.

    Args:
        U (np.ndarray): input matrix to decompose.
        validate_input (bool): if check input.
        atol: absolute tolerance parameter.
        rtol: relative tolerance parameter.

    Returns:
        QL (np.ndarray): first orthogonal matrix in the decomposition.
        theta (np.ndarray): the vector of diagonal elements.
        QR (np.ndarray): second orthogonal matrix in the decomposition.
    """

    if validate_input:
        try:
            dim1, dim2 = np.shape(U)

        except ValueError:
            print("The input need to be a 2d numpy array.")

        if (np.shape(U)[0] != np.shape(U)[1] or
            (not np.allclose(np.linalg.det(U.conj().T @ U),
                             1,
                             atol=atol,
                             rtol=rtol))):
            raise ValueError("The input matrix has to be unitary.")

    XR = np.real(U)
    XI = np.imag(U)

    QL, QR = diagonalize_two_matrices_with_hermitian_products(XR,
                                                              XI,
                                                              atol=atol,
                                                              rtol=rtol)

    if np.linalg.det(QL) < 0:
        QL[0, :] = -1 * QL[0, :]
    if np.linalg.det(QR) < 0:
        QR[:, 0] = -1 * QR[:, 0]
         
    theta = np.diag(np.angle(QL @ U @ QR))

    return (QL.T, theta, QR.T)


class KAKDecomposition:
    """
    Container of KAK decompositions for displaying information,
    constructing related circuits, visualizing KAK vectors.

    Attributes:
        

    """

    def __init__(self, U:np.ndarray):

        self.decompose(U)
        self.move_to_weyl_chamber()

    def decompose(self,
                  U: np.ndarray,
                  validate_input: bool=True,
                  atol: float=1E-8,
                  rtol: float=1E-5):
        """
        KAK decomposition of a 4x4 unitary matrix U:
        U = (u1 ⊗ u2) · exp(i(a·XX + b·YY+c·ZZ))·(u3 ⊗ u4)
        
        References:
            1. Byron Drury, Peter J. Love, Constructive Quantum Shannon 
            Decomposition from Cartan Involutions, arXiv:quant-ph/0806.4015
            2. Robert R. Tucci, An introduction to Cartan's KAK decomposition
            for QC programmers, arXiv:quant-ph/0507171

        Args:
            U (np.ndarray): input 4x4 unitary matrix to decompose.
            validate_input (bool): if check input.
            atol: absolute tolerance parameter.
            rtol: relative tolerance parameter.
        """

        if validate_input:
            try:
                dim1, dim2 = np.shape(U)

            except ValueError:
                print("The input need to be a 2d numpy array.")

            if (np.shape(U)[0] != 4 or
                np.shape(U)[1] != 4 or
                (not np.allclose(U.conj().T @ U,
                                 np.eye(np.shape(U)[0]),
                                 atol=atol,
                                 rtol=rtol))):
                raise ValueError("The input matrix has to be 4x4 unitary.")

        magic_u = magic_basis.conj().T @ U @ magic_basis
        ql, theta, qr = odo_decomposition(magic_u,
                                          atol=atol,
                                          rtol=rtol)

        kak_4vector = 0.25 * kak_theta_transform.T @ theta
        
        g1, u1, u2 = decompose_one_qubit_product(magic_basis @ 
                                                 ql @ 
                                                 magic_basis.conj().T,
                                                 atol=atol,
                                                 rtol=rtol)

        g2, u3, u4 = decompose_one_qubit_product(magic_basis @
                                                 qr @ 
                                                 magic_basis.conj().T,
                                                 atol=atol,
                                                 rtol=rtol)

        self.phase = g1 * g2 * np.exp(1j*kak_4vector[0])
        self.su2 = [u1, u2, u3, u4]
        self.kak_vector = kak_4vector[1:]

    def move_to_weyl_chamber(self):
        """
        Move the KAK vector to the Weyl chamber.
        """
        
        self.move_within_0_half_pi(0)
        self.move_within_0_half_pi(1)
        self.move_within_0_half_pi(2)

        self.descent_order()
        
        if self.kak_vector[0] + self.kak_vector[1] > np.pi * 0.5:
            self.swap(0, 1)
            self.reverse(0, 1)
            self.shift(0, 1)
            self.shift(1, 1)

        if self.kak_vector[2] == 0 and self.kak_vector[0] > np.pi * 0.25:
            self.reverse(0, 2)
            self.shift(0, 1)

    def shift(self, ind: int, direction: int):
        """
        Shift a component preserves the KAK vector equivalent class.
        
        Args:
            ind (int): the index of the component to shift by 0.5pi.
            direction (int): the direction to shift
        """

        prefix = [x, y, z]
        self.kak_vector[ind] += 0.5 * np.pi * direction
        self.su2[0] = self.su2[0] @ prefix[ind]
        self.su2[1] = self.su2[1] @ prefix[ind]
        self.phase *= 1j * direction

    def reverse(self, ind1: int, ind2: int):
        """
        Reverse two components preserves the KAK vector equivalent class.

        Args:
            ind1 (int): the 1st index to revert.
            ind2 (int): the 2nd index of revert.
        """

        prefix = [z, y, x]
        self.kak_vector[ind1] *= -1
        self.kak_vector[ind2] *= -1
        self.su2[0] = self.su2[0] @ prefix[ind1 + ind2 - 1]
        self.su2[3] = prefix[ind1 + ind2 - 1] @ self.su2[3]

    def swap(self, ind1: int, ind2: int):
        """
        Swap two components preserves the KAK vector equivalent class.

        Args:
            ind1 (int): the 1st index to swap.
            ind2 (int): the 2nd index of swap.
        """
        
        prefix = [z, y, x]
        self.kak_vector[ind1], self.kak_vector[ind2] = self.kak_vector[ind2], self.kak_vector[ind1]
        self.su2[0] *= expm(-0.25j * np.pi * prefix[ind1 + ind2 - 1])
        self.su2[1] *= expm(-0.25j * np.pi * prefix[ind1 + ind2 - 1])
        self.su2[3] *= expm(0.25j * np.pi * prefix[ind1 + ind2 - 1])
        self.su2[4] *= expm(0.25j * np.pi * prefix[ind1 + ind2 - 1])

    def move_within_0_half_pi(self, ind: int):
        """
        Keep shifting util the vector is within [0, 0.5pi).

        Args:
            ind (int): the index to move.
        """

        while self.su2[ind] >= np.pi * 0.5:
            self.shift(ind, -1)
        while self.su2[ind] < 0:
            self.shift(ind, 1)

    def descent_order(self):
        """
        Permute the indices so that the vector strengths are in descent order.
        """
        
        max_ind = self.kak_vector.index(max(self.kak_vector))

        if max_ind != 0:
            self.swap(0, max_ind)

        if self.kak_vector[1] < self.kak_vector[2]:
            self.swap(1, 2)
