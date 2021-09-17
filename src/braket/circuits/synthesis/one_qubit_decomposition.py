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
import braket.circuits as braket_circ

from braket.circuits.synthesis.util import to_su
from braket.circuits.synthesis.predicates import is_unitary
from braket.circuits import Circuit
from braket.circuits.gates import X, Y, Z, Rx, Ry, Rz
from braket.circuits.instruction import Instruction

y = Y().to_matrix()
z = Z().to_matrix()


class OneQubitDecomposition:
    """
    Class for decomposition of 1-qubit gates.

    Args:
        U (np.ndarray): the unitary matrix to decompose.

    Attributes:
        phase (np.dtype): the global phase.
        canonical_vector (np.ndarray): the axis w.r.t. which the rotation is
            performed.
        rotation_angle (np.dtype): the amplitude of the rotation.
        quaternion (np.ndarray): the quaternion representation
            of the rotation.
        rotation_matrix (np.ndarray): the matrix representation
            of the rotation.
    """

    def __init__(self, U: np.ndarray, atol: float = 1e-8, rtol: float = 1e-5):

        self.atol = atol
        self.rtol = rtol

        if U.shape != (2, 2):
            raise ValueError("Input matrix has to be 2x2.")

        is_unitary(U, atol=self.atol, rtol=self.rtol, raise_exception=True)

        self.U = U
        su = to_su(self.U)
        self.phase = np.linalg.det(U) ** 0.5

        # Calculate zyz Euler angles.
        weight_matrix = np.array([[1, 1], [-1, 1]])

        r1 = 2 * np.arctan2(abs(su[1, 0]), abs(su[0, 0]))

        if r1 < 0:
            r1 += 2 * np.pi

        r0r2 = np.angle(su[1, :])

        # have to check if r2 is 0 to avoid gimbal lock.
        if abs(su[0, 1]) < self.atol:
            r0 = 2 * np.angle(su[1, 1])
            r2 = 0
        else:
            r0r2 = weight_matrix @ np.angle(su[1, :])
            r0, r2 = np.where(r0r2 < 0, r0r2 + 2 * np.pi, r0r2)

        self._euler = np.array([r0, r1, r2])

        # Calculate the quaternion representation.

        q0 = np.real(su[0, 0])
        q1 = -np.imag(su[0, 1])
        q2 = -np.real(su[0, 1])
        q3 = -np.imag(su[0, 0])

        self._quat = np.array([q0, q1, q2, q3])

    def euler_angles(self, axes: str = "zyz"):
        """
        Find the Euler angle of 1-qubit gates.

        Default is the following zyz decomposition:

            SU(2) = exp(i * phase) *

                    [[exp(-1j*r1), 0],
                     [0,  exp(1j*r1)]] @

                    [[cos(r2), -sin(r2)],
                     [sin(r2),  cos(r2)]] @

                    [[exp(-1j*r3), 0],
                     [0,  exp(1j*r3)]]

        Args:
            axes (str): the decomposed axes.

        Raises:
            NotImplementedError: if the decomposition method is not
            implemented.
        """

        if axes == "zyz":
            return self._euler

        elif axes == "zxz":
            r0, r1, r2 = self._euler
            return np.array([r0 + 0.5 * np.pi, r1, r2 - 0.5 * np.pi])

        else:
            raise NotImplementedError("The decomposition method is not implemented.")

    @property
    def quaternion(self):
        """
        Quaternion representation of 1-q decomposition.
        """

        return self._quat

    @property
    def canonical_vector(self):
        """
        Return the rotation axis for the
        axis decomposition of 1-qubit gates.

        SU(2) = exp(-0.5j * theta * (xX + yY + zZ))

        To align with 2-qubit gate decomposition, we name it
        the canonical_vector.
        """
        norm = np.linalg.norm(self._quat[1:])

        if norm < self.atol:
            return np.array([1, 0, 0])

        return self._quat[1:] / norm

    @property
    def rotation_angle(self):
        """
        Return the rotation angle of the axis decomposition
        of 1-qubit gates.

        SU(2) = exp(-0.5j * theta * (xX + yY + zZ))
        """
        return 2 * np.arccos(self._quat[0])

    def __repr__(self):

        repr_str = (
            "OneQubitDecomposition(\n"
            + f"  global phase: {self.phase},\n"
            + "  ZYZ decomposition:\n"
            + "    ------Rz--Ry--Rz------\n"
            + f"    euler angles: {self.euler_angles('zyz')})\n"
            + "  Axis-angle decomposition:\n"
            + "    SU(2) = exp(-0.5j * theta * (xX + yY + zZ))\n"
            + f"    canonical vector (x, y, z): {self.canonical_vector},\n"
            + f"    theta: {self.rotation_angle},\n"
            + f"    quaternion representation: {self.quaternion}\n"
            + ")\n"
        )
        return repr_str

    def build_circuit(self, qubit: int = 0, method: str = "zyz") -> braket_circ.Circuit:
        """
        Build the Braket circuit for the input unitary.

        Args:
            qubit (int): on which qubit the rotations are applied.
            method (str): the decomposition method.

        Returns:
            circ (braket_circ.Circuit): the generated circuit.
        """

        circ = Circuit()

        XYZ = [X, Y, Z]
        Rxyz = [Rx, Ry, Rz]
        pauli_str = "xyz"

        for i in range(3):

            angles = self.euler_angles(method)[::-1]

            if abs(angles[i]) < self.atol or abs(angles[i] - 2 * np.pi) < self.atol:
                continue

            elif abs(angles[i] - np.pi) < self.atol:
                gate = XYZ[pauli_str.index(method[i])]()
                ins = Instruction(gate, [qubit])
                circ = circ.add_instruction(ins)

            else:
                gate = Rxyz[pauli_str.index(method[i])](angles[i])
                ins = Instruction(gate, [qubit])
                circ = circ.add_instruction(ins)

        return circ
