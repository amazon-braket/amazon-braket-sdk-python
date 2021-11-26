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

from typing import List, Union
from functools import singledispatch
import numpy as np

from braket.circuits import Circuit, circuit, Instruction, Qubit
from braket.circuits.gates import Y, Z, Ry, Rz, CNot, CZ


@circuit.subroutine(register=True)
@singledispatch
def _multiplexor_entangler(pauli, control:Qubit, target:Qubit):
    raise NotImplementedError("Pauli multiplexor type not supported.")

@_multiplexor_entangler.register(Y)
def _(pauli, control:Qubit, target:Qubit):
    return Instruction(CZ(), target=[control, target])

@_multiplexor_entangler.register(Z)
def _(pauli, control:Qubit, target:Qubit):
    return Instruction(CNot(), target=[control, target])


@circuit.subroutine(register=True)
@singledispatch
def _multiplexor_rotation(pauli, angle:float, target:Qubit):
    raise NotImplementedError("Pauli multiplexor type not supported.")

@_multiplexor_rotation.register(Y)
def _(pauli, angle:float, target:Qubit):
    return Instruction(Ry(angle), target=target)

@_multiplexor_rotation.register(Z)
def _(pauli, angle:float, target:Qubit):
    return Instruction(Rz(angle), target=target)


@circuit.subroutine(register=True)
def pauli_multiplexor(
    pauli,
    angles: Union[List[float], np.ndarray],
    control_bits: List[int],
    target_bit: int = 0,
    reverse=False,
    manually_optimized=False,
):
    """
    Function to compute the circuit for a Multiplexed Pauli rotation operation.

    Arguments:
        pauli (Union[Y, Z]): The pauli rotation axis, can only be Y or Z.
        angles (List[float]): Pauli rotation angles.
        control_bits (List[int]): List of control qubits for the multiplexor gate.
        target_bit (int): The target qubit index.
        reverse (bool): Whether reverse the gate order in the syntheized circuit.
        manually_optimized (bool): A flag to indicate that the optimized but 
            non-semantics-preserving result will be correctly handled by the caller. 
            Default is set to False. Inappropriate use might result in incorrect circuit.
            This optimization can be replaced by a general circuit optimizer while keep 
            the circuit semantics unchanged at all time.

    Returns:
        circ (Circuit): The synthesized circuit for the multiplexed Ry gate.
    """

    num_ctrl = len(control_bits)

    if len(angles) != 2 ** num_ctrl:
        raise ValueError("The number of Ry angles doesn't match the number of control bits.")

    circ = Circuit()

    weight = 0.5 * np.array([[1, 1], [1, -1]])
    pauli_angles = weight @ np.array(angles).reshape(2, len(angles) // 2)

    # Base case
    if num_ctrl == 1:
        pauli_angles = np.squeeze(pauli_angles)

        if not reverse:
            circ._multiplexor_rotation(pauli, pauli_angles[0], target_bit)
            circ._multiplexor_entangler(pauli, control_bits[0], target_bit)
            circ._multiplexor_rotation(pauli, pauli_angles[1], target_bit)
            if not manually_optimized:
                circ._multiplexor_entangler(pauli, control_bits[0], target_bit)

        else:  # reverse
            if not manually_optimized:
                circ._multiplexor_entangler(pauli, control_bits[0], target_bit)
            circ._multiplexor_rotation(pauli, pauli_angles[1], target_bit)
            circ._multiplexor_entangler(pauli, control_bits[0], target_bit)
            circ._multiplexor_rotation(pauli, pauli_angles[0], target_bit)

    else:
        if not reverse:
            circ.pauli_multiplexor(
                pauli, 
                pauli_angles[0],
                control_bits[1:],
                target_bit,
                reverse=False,
                manually_optimized=True,
            )
            circ._multiplexor_entangler(pauli, control_bits[0], target_bit)
            circ.pauli_multiplexor(
                pauli,
                pauli_angles[1],
                control_bits[1:],
                target_bit,
                reverse=True,
                manually_optimized=True,
            )
            if not manually_optimized:
                circ._multiplexor_entangler(pauli, control_bits[0], target_bit)

        else:
            if not manually_optimized:
                circ._multiplexor_entangler(pauli, control_bits[0], target_bit)
            circ.pauli_multiplexor(
                pauli,
                pauli_angles[1],
                control_bits[1:],
                target_bit,
                reverse=False,
                manually_optimized=True,
            )
            circ._multiplexor_entangler(pauli, control_bits[0], target_bit)
            circ.pauli_multiplexor(
                pauli,
                pauli_angles[0],
                control_bits[1:],
                target_bit,
                reverse=True,
                manually_optimized=True,
            )

    return circ
