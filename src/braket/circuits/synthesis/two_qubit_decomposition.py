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

# Numerical
import numpy as np
from scipy.linalg import expm

# Typing
from typing import Tuple, Sequence, Union

# Plotting
import matplotlib
import matplotlib.pyplot as plt

# Braket
from braket.circuits.qubit_set import QubitSet
from braket.circuits import Circuit

from braket.circuits.gates import X, Y, Z, CNot
from braket.circuits.synthesis.invariants import makhlin_invariants, gamma_invariants
from braket.circuits.synthesis.one_qubit_decomposition import OneQubitDecomposition
from braket.circuits.synthesis.constants import magic_basis, kak_so4_transform_matrix
from braket.circuits.quantum_operator_helpers import is_unitary
from braket.circuits.synthesis.util import (
    rx,
    rz,
    to_su,
    diagonalize_two_matrices_with_hermitian_products,
)

matplotlib.rcParams["text.usetex"] = True

x = X().to_matrix()
y = Y().to_matrix()
z = Z().to_matrix()
cnot = CNot().to_matrix()
I = np.eye(2)  # noqa: E741
cnot_re = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=np.complex128)

"""
Gamma invariants for unitaries requiring 0, 1, 2 CNOTs to synthesize.
"""

_ZERO_CNOT_GAMMA_INV1 = (1, 4, 6, 4, 1)
_ZERO_CNOT_GAMMA_INV2 = (1, -4, 6, -4, 1)
_ONE_CNOT_GAMMA_INV = (1, 0, 2, 0, 1)
_TWO_CNOT_GAMMA_INV = (0, 0, 0, 0, 0)


class TwoQubitDecomposition:
    """
    Canonical decompositions of 2-qubit unitaries.

    Attributes:
        U (np.ndarray): unitary to decompose.
        su2 (list): 1-qubit unitaries after decomposition.
        canonical_vector (np.ndarray): the KAK vector after
            decomposition.
        atol (float): absolute tolerance of less.
        rtol (float): relative tolerance of less.
    """

    def __init__(self, U: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5):

        self.atol = atol
        self.rtol = rtol
        self.U = U
        self.num_cnots = self.count_num_cnots()

        self.build(U)
        _move_to_weyl_chamber(self)

    def build(self, U: np.ndarray, validate_input: bool = True):
        """
        Cartan's KAK decomposition of a 4x4 unitary matrix U:
        U = (u_1 otimes u_2) cdot exp(i(a cdot XX + b cdot YY + c cdot ZZ)) cdot(u_3 otimes u_4)

        References:
            1. Byron Drury, Peter J. Love, Constructive Quantum Shannon
            Decomposition from Cartan Involutions, arXiv:quant-ph/0806.4015
            2. Robert R. Tucci, An introduction to Cartan's KAK decomposition
            for QC programmers, arXiv:quant-ph/0507171

        Args:
            U (np.ndarray): input 4x4 unitary matrix to decompose.
            validate_input (bool): if check input.
            atol (float): absolute tolerance parameter.
            rtol (float): relative tolerance parameter.
        """

        if validate_input:
            is_unitary(U, raise_exception=True)

        if np.allclose(
            makhlin_invariants(U, atol=self.atol, rtol=self.rtol),
            (1, 0, 3),
            atol=self.atol,
            rtol=self.rtol,
        ):
            g, u1, u2 = decompose_one_qubit_product(U, atol=self.atol, rtol=self.rtol)

            self.phase = g
            self.su2 = [u1, u2, I, I]
            self.canonical_vector = np.array([0, 0, 0])

            self.cnot_circuit_phase = 0.0

            return

        magic_u = magic_basis.conj().T @ U @ magic_basis
        ql, theta, qr = odo_decomposition(magic_u, atol=self.atol, rtol=self.rtol)

        kak_4vector = 0.25 * kak_so4_transform_matrix.T @ theta

        g1, u1, u2 = decompose_one_qubit_product(
            magic_basis @ ql @ magic_basis.conj().T, atol=self.atol, rtol=self.rtol
        )

        g2, u3, u4 = decompose_one_qubit_product(
            magic_basis @ qr @ magic_basis.conj().T, atol=self.atol, rtol=self.rtol
        )

        self.phase = g1 * g2 * np.exp(1j * kak_4vector[0])

        self.su2 = [u1, u2, u3, u4]
        self.canonical_vector = kak_4vector[1:]

    def __repr__(self):

        str_u = []
        for i in range(4):
            str_u.append(np.array2string(self.su2[i]).replace("\n", "\n     "))

        kak_str = (
            "TwoQubitDecomposition(\n"
            + "  U = (u1 ⊗ u2) · exp(i(v0·XX + v1·YY+v2·ZZ))·(u3 ⊗ u4)\n"
            + f"  global phase: {self.phase},\n"
            + f"  canonical vector v: {self.canonical_vector},\n"
            + f"  u1: {str_u[0]},\n"
            + f"  u2: {str_u[1]},\n"
            + f"  u3: {str_u[2]},\n"
            + f"  u4: {str_u[3]}\n)"
        )
        return kak_str

    @property
    def unitary(self):
        """
        The unitary matrix of this decomposition.
        """
        return self.U

    def pretty_print(self) -> None:
        """
        Helper function for printing detailed information of the
        decomposition.
        """

        str_u = []
        for i in range(4):
            str_u.append(np.array2string(self.su2[i], precision=3).replace("\n", "\n     "))
        kak_str = (
            "TwoQubitDecomposition(\n"
            + "  U = (u1 ⊗ u2) · exp(i(v0·XX + v1·YY+v2·ZZ))·(u3 ⊗ u4)\n"
            + f"  global phase: {np.array2string(self.phase, precision=3)},\n"
            + f"  canonical vector: {np.array2string(self.canonical_vector, precision=3)},\n"
            + f"  u1: {str_u[0]},\n"
            + f"  u2: {str_u[1]},\n"
            + f"  u3: {str_u[2]},\n"
            + f"  u4: {str_u[3]}\n)"
        )
        print(kak_str)

    def plot_canonical_vector(self):
        """
        Plot the canonical KAK vector of the decomposition.
        """

        _plot_canonical_vector(self.canonical_vector)

    def count_num_cnots(self):
        """
        Find the number of CNOTs required to
        synthesize self.U.

        Returns:
            num_cnots (int): The number of CNOTs required.
        """

        gamma_inv = gamma_invariants(self.U, atol=self.atol, rtol=self.rtol)

        if np.allclose(
            gamma_inv, _ZERO_CNOT_GAMMA_INV1, atol=self.atol, rtol=self.rtol
        ) or np.allclose(gamma_inv, _ZERO_CNOT_GAMMA_INV2, atol=self.atol, rtol=self.rtol):
            return 0

        if np.allclose(gamma_inv, _ONE_CNOT_GAMMA_INV, atol=self.atol, rtol=self.rtol):
            return 1

        if np.allclose(np.imag(gamma_inv), _TWO_CNOT_GAMMA_INV, atol=self.atol, rtol=self.rtol):
            return 2

        else:
            return 3

    def to_circuit(self, qubits: Union[QubitSet, Sequence[int]] = [0, 1]):
        """
        Build the synthesized circuit.

        Args:
            qubits (Union[QubitSet, Sequence[int]]): The qubit set to build the circuit on.
        """

        return self.to_cnot_circuit(qubits=qubits)

    def to_cnot_circuit(self, qubits: Union[QubitSet, Sequence[int]] = [0, 1]) -> Circuit:
        """
        Given a TwoQubitDecomposition, construct a CNOT based
        Circuit.

        Args:
            qubits (Union[QubitSet, Sequence[int]]): Input qubits.

        Returns:
            circ (Circuit): Constructed circuit based on the input
            decomposition.
        """

        if self.num_cnots == 0:
            return self._build_zero_cnot_circuit(qubits)

        elif self.num_cnots == 1:
            return self._build_one_cnot_circuit(qubits)

        elif self.num_cnots == 2:
            return self._build_two_cnot_circuit(qubits)

        elif self.num_cnots == 3:
            return self._build_three_cnot_circuit(qubits)

    def _build_zero_cnot_circuit(self, qubits: Union[QubitSet, Sequence[int]] = [0, 1]) -> Circuit:
        circ = Circuit()
        phase, u1, u2 = decompose_one_qubit_product(self.unitary)
        circ_u1 = OneQubitDecomposition(u1).to_circuit(qubit=qubits[1])
        circ_u2 = OneQubitDecomposition(u2).to_circuit(qubit=qubits[0])
        circ.add_circuit(circ_u1).add_circuit(circ_u2)

        return circ

    def _build_one_cnot_circuit(self, qubits: Union[QubitSet, Sequence[int]] = [0, 1]) -> Circuit:
        circ = Circuit()
        cnot_decomp = TwoQubitDecomposition(cnot, atol=self.atol, rtol=self.rtol)
        u1 = self.su2[0] @ cnot_decomp.su2[0].conj().T
        u2 = self.su2[1] @ cnot_decomp.su2[1].conj().T
        u3 = cnot_decomp.su2[2].conj().T @ self.su2[2]
        u4 = cnot_decomp.su2[3].conj().T @ self.su2[3]

        circ_list = []

        for i, ui in enumerate([u4, u3, u2, u1]):
            subcirc = OneQubitDecomposition(ui).to_circuit(qubit=qubits[i % 2])
            circ_list.append(subcirc)

        circ.add_circuit(circ_list[0])
        circ.add_circuit(circ_list[1])
        circ.cnot(*qubits[::-1])
        circ.add_circuit(circ_list[2])
        circ.add_circuit(circ_list[3])

        return circ

    def _build_two_cnot_circuit(self, qubits: Union[QubitSet, Sequence[int]] = [0, 1]) -> Circuit:
        circ = Circuit()
        gamma_inv = gamma_invariants(self.unitary)

        r = np.angle(np.roots(gamma_inv))
        r = np.sort(r[r > 0])

        weight_mat = 0.5 * np.array([[1, 1], [1, -1]])

        theta = weight_mat @ r

        cnot_decomp = TwoQubitDecomposition(cnot_re @ np.kron(rz(theta[0]), rx(theta[1])) @ cnot_re)

        u1 = self.su2[0] @ cnot_decomp.su2[0].conj().T
        u2 = self.su2[1] @ cnot_decomp.su2[1].conj().T
        u3 = rz(theta[0])
        u4 = rx(theta[1])
        u5 = cnot_decomp.su2[2].conj().T @ self.su2[2]
        u6 = cnot_decomp.su2[3].conj().T @ self.su2[3]

        circ_list = []

        for i, ui in enumerate([u6, u5, u4, u3, u2, u1]):
            subcirc = OneQubitDecomposition(ui).to_circuit(qubit=qubits[i % 2])
            circ_list.append(subcirc)

        circ.add_circuit(circ_list[0])
        circ.add_circuit(circ_list[1])
        circ.cnot(*qubits)
        circ.add_circuit(circ_list[2])
        circ.add_circuit(circ_list[3])
        circ.cnot(*qubits)
        circ.add_circuit(circ_list[4])
        circ.add_circuit(circ_list[5])

        return circ

    def _build_three_cnot_circuit(self, qubits: Union[QubitSet, Sequence[int]] = [0, 1]) -> Circuit:
        circ = Circuit()
        # U(4) -> SU(4)
        su = to_su(self.U)

        # Find the gamma invariants defined in
        # https://arxiv.org/pdf/quant-ph/0308033.pdf
        t = (su.T @ np.kron(y, y) @ su @ np.kron(y, y)).T

        # Find psi so that gamma(su * (I ⊗ Rz(psi)) * cnot) has
        # real trace
        t_ele = np.array([t[0, 1], t[1, 0], t[2, 3], t[3, 2]])
        psi_num = np.real(np.inner(t_ele, np.array([1, 1, -1, -1])))
        psi_denom = np.imag(np.inner(t_ele, np.array([1, -1, -1, 1])))

        psi = np.arctan2(psi_num, psi_denom)

        m = su @ np.kron(I, rz(psi)) @ cnot
        gamma_m = gamma_invariants(m)
        r_m = np.angle(np.roots(gamma_m))
        r_m = np.sort(r_m[r_m > 0])

        weight_mat = 0.5 * np.array([[1, 1], [1, -1]])

        theta = weight_mat @ r_m

        w = cnot @ np.kron(rx(theta[0]), rz(theta[1])) @ cnot

        gamma_w = gamma_invariants(w)
        r_w = np.angle(np.roots(gamma_w))
        r_w = np.sort(r_w[r_w > 0])

        w_decomp = TwoQubitDecomposition(w)
        m_decomp = TwoQubitDecomposition(m)

        u1 = m_decomp.su2[0] @ w_decomp.su2[0].conj().T
        u2 = m_decomp.su2[1] @ w_decomp.su2[1].conj().T
        u3 = rx(theta[0])
        u4 = rz(theta[1])
        u5 = w_decomp.su2[2].conj().T @ m_decomp.su2[2]
        u6 = w_decomp.su2[3].conj().T @ m_decomp.su2[3]
        u7 = rz(-psi)

        circ_list = [OneQubitDecomposition(u7).to_circuit(qubit=qubits[0])]

        for i, ui in enumerate([u6, u5, u4, u3, u2, u1]):
            subcirc = OneQubitDecomposition(ui).to_circuit(qubit=qubits[i % 2])
            circ_list.append(subcirc)

        circ.add_circuit(circ_list[0])
        circ.cnot(*qubits[::-1])
        circ.add_circuit(circ_list[1])
        circ.add_circuit(circ_list[2])
        circ.cnot(*qubits[::-1])
        circ.add_circuit(circ_list[3])
        circ.add_circuit(circ_list[4])
        circ.cnot(*qubits[::-1])
        circ.add_circuit(circ_list[5])
        circ.add_circuit(circ_list[6])

        return circ


def two_qubit_decompose(
    U: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5
) -> TwoQubitDecomposition:
    is_unitary(U, raise_exception=True)
    """
    Decompose a 2-qubit unitary.

    Args:
        U (np.ndarray): the unitary to decompose.
        atol (float): absolute tolerance parameter.
        rtol (float): relative tolerance parameter.

    """

    return TwoQubitDecomposition(U, atol=atol, rtol=rtol)


def decompose_one_qubit_product(
    U: np.ndarray, validate_input: bool = True, atol: float = 1e-8, rtol: float = 1e-5
):
    """
    Decompose a 4x4 unitary matrix to two 2x2 unitary matrices.

    Args:
        U (np.ndarray): input 4x4 unitary matrix to decompose.
        validate_input (bool): if check input.

    Returns:
        phase (float): global phase.
        U1 (np.ndarray): decomposed unitary matrix U1.
        U2 (np.ndarray): decomposed unitary matrix U2.
        atol (float): absolute tolerance of loss.
        rtol (float): relative tolerance of loss.

    Raises:
        AssertionError: if the input is not a 4x4 unitary or
        cannot be decomposed.
    """

    if validate_input:
        assert np.allclose(
            makhlin_invariants(U, atol=atol, rtol=rtol), (1, 0, 3), atol=atol, rtol=rtol
        )

    i, j = np.unravel_index(np.argmax(U, axis=None), U.shape)

    def u1_set(i):
        return (1, 3) if i % 2 else (0, 2)

    def u2_set(i):
        return (0, 1) if i < 2 else (2, 3)

    u1 = U[np.ix_(u1_set(i), u1_set(j))]
    u2 = U[np.ix_(u2_set(i), u2_set(j))]

    u1 = to_su(u1)
    u2 = to_su(u2)

    phase = U[i, j] / (u1[i // 2, j // 2] * u2[i % 2, j % 2])

    return phase, u1, u2


def odo_decomposition(
    U: np.ndarray, validate_input: bool = True, atol: float = 1e-8, rtol: float = 1e-5
) -> Tuple[np.ndarray]:

    """
    Decompose a unitary matrix U into QL * exp(i * theta) * QR.T,
    where QL, QR are orthogonal matrices and theta is a 1-d vector
    of angles. This decomposition can be derived from the
    Eckhart-Young simultaneuous diagonalization of Hermitian matrices.
    We call it orthogonal-diagonal-orthogonal (odo) decomposition.

    Args:
        U (np.ndarray): input matrix to decompose.
        validate_input (bool): if check input.
        atol (float): absolute tolerance of loss.
        rtol (float): relative tolerance of loss.

    Returns:
        QL (np.ndarray): first orthogonal matrix in the decomposition.
        theta (np.ndarray): the vector of diagonal elements.
        QR (np.ndarray): second orthogonal matrix in the decomposition.
    """

    if validate_input:
        is_unitary(U, raise_exception=True)

    XR = np.real(U)
    XI = np.imag(U)

    QL, QR = diagonalize_two_matrices_with_hermitian_products(
        XR, XI, atol=atol, rtol=rtol, validate_input=False
    )

    if np.linalg.det(QL) < 0:
        QL[0, :] = -1 * QL[0, :]
    if np.linalg.det(QR) < 0:
        QR[:, 0] = -1 * QR[:, 0]

    theta = np.angle(np.diag(QL @ U @ QR))
    return (QL.T, theta, QR.T)


def _move_to_weyl_chamber(kak: TwoQubitDecomposition) -> None:  # noqa C901
    """
    Move the canonical vector to the Weyl chamber.

    References:
        1. Robert R. Tucci, An introduction to Cartan's KAK decomposition
        for QC programmers, arXiv:quant-ph/0507171

    Args:
        kak (TwoQubitDecomposition): The two qubit decomposition to canonicalize.
    """

    def shift(ind: int, direction: int):
        """
        Shift a component preserves the canonical vector equivalent class.

        Args:
            ind (int): the index of the component to shift by 0.5pi.
            direction (int): the direction to shift
        """

        prefix = [x, y, z]
        kak.canonical_vector[ind] += 0.5 * np.pi * direction
        kak.su2[0] = kak.su2[0] @ prefix[ind]
        kak.su2[1] = kak.su2[1] @ prefix[ind]
        kak.phase *= -1j * direction

    def reverse(ind1: int, ind2: int):
        """
        Reverse two components preserves the canonical vector equivalent class.

        Args:
            ind1 (int): the 1st index to revert.
            ind2 (int): the 2nd index of revert.
        """

        prefix = [z, y, x]
        kak.canonical_vector[ind1] *= -1
        kak.canonical_vector[ind2] *= -1
        kak.su2[0] = kak.su2[0] @ prefix[ind1 + ind2 - 1]
        kak.su2[2] = prefix[ind1 + ind2 - 1] @ kak.su2[2]

    def swap(ind1: int, ind2: int):
        """
        Swap two components preserves the canonical vector equivalent class.

        Args:
            ind1 (int): the 1st index to swap.
            ind2 (int): the 2nd index of swap.
        """

        prefix = [z, y, x]
        kak.canonical_vector[ind1], kak.canonical_vector[ind2] = (
            kak.canonical_vector[ind2],
            kak.canonical_vector[ind1],
        )
        kak.su2[0] = kak.su2[0] @ expm(-0.25j * np.pi * prefix[ind1 + ind2 - 1])
        kak.su2[1] = kak.su2[1] @ expm(-0.25j * np.pi * prefix[ind1 + ind2 - 1])
        kak.su2[2] = expm(0.25j * np.pi * prefix[ind1 + ind2 - 1]) @ kak.su2[2]
        kak.su2[3] = expm(0.25j * np.pi * prefix[ind1 + ind2 - 1]) @ kak.su2[3]

    def move_within_0_half_pi(ind: int):
        """
        Keep shifting util the vector is within [0, 0.5pi).

        Args:
            ind (int): the index to move.
        """

        while kak.canonical_vector[ind] >= np.pi * 0.5:
            shift(ind, -1)
        while kak.canonical_vector[ind] < 0:
            shift(ind, 1)

    def descent_order():
        """
        Permute the indices so that the vector strengths are in descent order.
        """

        max_ind = list(kak.canonical_vector).index(max(kak.canonical_vector))

        if max_ind != 0:
            swap(0, max_ind)

        if kak.canonical_vector[1] < kak.canonical_vector[2]:
            swap(1, 2)

    move_within_0_half_pi(0)
    move_within_0_half_pi(1)
    move_within_0_half_pi(2)

    descent_order()

    if kak.canonical_vector[0] + kak.canonical_vector[1] > np.pi * 0.5:
        swap(0, 1)
        reverse(0, 1)
        shift(0, 1)
        shift(1, 1)
        descent_order()

    if np.isclose(kak.canonical_vector[2], [0]) and kak.canonical_vector[0] > np.pi * 0.25:
        reverse(0, 2)
        shift(0, 1)


def _plot_canonical_vector(vector):
    """
    Plot the canonical vector in the Weyl chamber.

    Args:
        vector (np.ndarray): The vector to plot.
    """

    fig = plt.figure(figsize=(10, 10))
    ax = plt.axes(projection="3d")

    ax.view_init(-140, -180)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

    ax.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))

    cnot_coord = (0.25 * np.pi, 0, 0)
    I_coord = (0, 0, 0)
    iswap_coord = (0.25 * np.pi, 0.25 * np.pi, 0)
    swap_coord = (0.25 * np.pi, 0.25 * np.pi, 0.25 * np.pi)
    swap_d_coord = (0.25 * np.pi, 0.25 * np.pi, -0.25 * np.pi)

    cnot_text_coord = (0.25 * np.pi + 0.03, -0.03, 0)
    I_text_coord = (0, -0.03, 0)
    iswap_text_coord = (0.25 * np.pi, 0.25 * np.pi + 0.26, 0)
    swap_text_coord = (0.25 * np.pi + 0.05, 0.25 * np.pi + 0.26, 0.25 * np.pi)
    swap_d_text_coord = (0.25 * np.pi, 0.25 * np.pi + 0.26, -0.25 * np.pi)

    ax.text(*cnot_text_coord, r"CNOT$(\frac{\pi}{4}, 0, 0)$", fontsize=17)
    ax.text(*I_text_coord, r"I$(0, 0, 0)$", fontsize=20)
    ax.text(*iswap_text_coord, r"iSWAP$(\frac{\pi}{4}, \frac{\pi}{4}, 0)$", fontsize=17)
    ax.text(*swap_text_coord, r"SWAP$(\frac{\pi}{4}, \frac{\pi}{4}, \frac{\pi}{4})$", fontsize=17)
    ax.text(
        *swap_d_text_coord,
        r"SWAP$^\dagger(\frac{\pi}{4}, \frac{\pi}{4}, -\frac{\pi}{4})$",
        fontsize=17,
    )

    tedra_front = [
        zip(cnot_coord, swap_coord),
        zip(swap_coord, swap_d_coord),
        zip(I_coord, cnot_coord),
        zip(swap_coord, I_coord),
        zip(swap_d_coord, I_coord),
        zip(iswap_coord, I_coord),
    ]
    tedra_back = [zip(swap_d_coord, cnot_coord), zip(iswap_coord, cnot_coord)]

    for line in tedra_back:
        ax.plot(*line, color="black", ls="dashed")

    ax.scatter(*vector, marker="o", color="red", s=32)
    vec_text_coord = [vector[0] - 0.02, vector[1] - 0.02, vector[2]]
    ax.text(*vec_text_coord, r"Your unitary", fontsize=20, color="red")

    for line in tedra_front:
        ax.plot(*line, color="black")

    ax.set_xlim(0.15, np.pi / 4 - 0.1)
    ax.set_zlim(-0.3, np.pi / 4 + 0.2)
    ax.set_ylim(-0.1, np.pi / 4 + 0.1)

    fig.tight_layout(pad=0.9)
