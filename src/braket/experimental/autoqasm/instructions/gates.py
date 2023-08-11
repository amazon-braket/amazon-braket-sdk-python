# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
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


"""Quantum gates, unitary instructions, that apply to qubits.
"""
from inspect import Parameter, Signature
from typing import Dict, Tuple

from braket.experimental.autoqasm import program

from .qubits import _qubit


def define_gate(name: str, n_control: int, n_target: int, n_angle: int, description: str) -> None:
    """Define a quantum gate.

    Args:
        name (str): Gate name.
        n_control (int): Number of control qubits.
        n_target (int): Number of target qubits.
        n_angle (int): Number of angles.
        description (str): Description of the gate.
    """

    def quantum_gate(*args):
        n_qubits = n_control + n_target
        qubits = [_qubit(q) for q in args[:n_qubits]]
        angles = args[n_qubits : (n_qubits + n_angle)]
        oqpy_program = program.get_program_conversion_context().get_oqpy_program()
        oqpy_program.gate(qubits, name, *angles)

    quantum_gate.__name__ = name
    quantum_gate.__doc__ = _gate_doc(n_control, n_target, n_angle, description)

    signature, annotations = _gate_annotations(n_control, n_target, n_angle)
    quantum_gate.__annotations__ = annotations
    quantum_gate.__signature__ = signature

    globals()[name] = quantum_gate


def _gate_doc(n_control: int, n_target: int, n_angle: int, description: str) -> str:
    """Return docstring of the gate.

    Args:
        n_control (int): Number of control qubits.
        n_target (int): Number of target qubits.
        n_angle (int): Number of angles.
        description (str): Description of the gate.

    Returns:
        str: docstring of the gate.
    """
    gate_doc = description + "\n\n Args:"
    for i in range(n_control):
        gate_doc += f"\n\tcontrol_{i} (QubitIdentifierType): Control qubit {i}."
    for i in range(n_target):
        gate_doc += f"\n\ttarget_{i} (QubitIdentifierType): Target qubit {i}."
    for i in range(n_angle):
        gate_doc += f"\n\tangle_{i} (float): Rotation angle {i} in radians."
    return gate_doc


def _gate_annotations(n_control: int, n_target: int, n_angle: int) -> Tuple[Signature, Dict]:
    """Return function signature and type annotations of the gate.

    Args:
        n_control (int): Number of control qubits.
        n_target (int): Number of target qubits.
        n_angle (int): Number of angles.

    Returns:
        Signature, dict: signature and type annotations of the gate.
    """
    parameters = []
    annotations = {}

    for i in range(n_control):
        name = f"control_{i}"
        parameters.append(
            Parameter(name=name, annotation=int, kind=Parameter.POSITIONAL_OR_KEYWORD)
        )
        annotations[name] = int
    for i in range(n_target):
        name = f"target_{i}"
        parameters.append(
            Parameter(name=name, annotation=int, kind=Parameter.POSITIONAL_OR_KEYWORD)
        )
        annotations[name] = int
    for i in range(n_angle):
        name = f"angle_{i}"
        parameters.append(
            Parameter(name=name, annotation=float, kind=Parameter.POSITIONAL_OR_KEYWORD)
        )
        annotations[name] = float

    signature = Signature(parameters)
    return signature, annotations


define_gate("h", 0, 1, 0, "Hadamard gate.")
define_gate("i", 0, 1, 0, "Identity gate.")
define_gate("x", 0, 1, 0, "Pauli-X gate.")
define_gate("y", 0, 1, 0, "Pauli-Y gate.")
define_gate("z", 0, 1, 0, "Pauli-Z gate.")
define_gate("s", 0, 1, 0, "S gate.")
define_gate("si", 0, 1, 0, "Conjugate transpose of S gate.")
define_gate("t", 0, 1, 0, "T gate.")
define_gate("ti", 0, 1, 0, "Conjugate transpose of T gate.")
define_gate("v", 0, 1, 0, "Square root of not gate.")
define_gate("vi", 0, 1, 0, "Conjugate transpose of square root of not gate.")
define_gate("cnot", 1, 1, 0, "Controlled NOT gate.")
define_gate("swap", 0, 2, 0, "Swap gate.")
define_gate("iswap", 0, 2, 0, "ISwap gate.")
define_gate("cv", 1, 1, 0, "Controlled Sqrt of NOT gate.")
define_gate("cy", 1, 1, 0, "Controlled Pauli-Y gate.")
define_gate("cz", 1, 1, 0, "Controlled Pauli-Z gate.")
define_gate("ecr", 0, 2, 0, "An echoed RZX(pi/2) gate.")
define_gate("ccnot", 2, 1, 0, "CCNOT gate or Toffoli gate.")
define_gate("cswap", 1, 2, 0, "Controlled Swap gate.")
define_gate("rx", 0, 1, 1, "X-axis rotation gate.")
define_gate("ry", 0, 1, 1, "Y-axis rotation gate.")
define_gate("rz", 0, 1, 1, "Z-axis rotation gate.")
define_gate("phaseshift", 0, 1, 1, "Phase shift gate.")
define_gate("pswap", 0, 2, 1, "PSwap gate.")
define_gate("xy", 0, 2, 1, "XY gates")
define_gate("cphaseshift", 1, 1, 1, "Controlled phase shift gate.")
define_gate("cphaseshift00", 1, 1, 1, "Controlled phase shift gate for phasing the \\|00> state.")
define_gate("cphaseshift01", 1, 1, 1, "Controlled phase shift gate for phasing the \\|01> state.")
define_gate("cphaseshift10", 1, 1, 1, "Controlled phase shift gate for phasing the \\|10> state.")
define_gate("xx", 0, 2, 1, "Ising XX coupling gate.")
define_gate("yy", 0, 2, 1, "Ising YY coupling gate.")
define_gate("zz", 0, 2, 1, "Ising ZZ coupling gate.")
define_gate("gpi", 0, 1, 1, "IonQ GPi gate.")
define_gate("gpi2", 0, 1, 1, "IonQ GPi2 gate.")
define_gate("ms", 0, 2, 3, "IonQ Mølmer-Sørenson gate.")
