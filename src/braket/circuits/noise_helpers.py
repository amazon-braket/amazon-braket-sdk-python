from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Iterable, Type

from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.noise import Noise
from braket.circuits.qubit_set import QubitSet

if TYPE_CHECKING:  # pragma: no cover
    from braket.circuits.circuit import Circuit


def apply_noise_to_moments(
    circuit: Circuit, noise: Noise, target_qubits: QubitSet, position: str
) -> Circuit:
    """Apply initialization/readout noise to the circuit.

    When `noise.qubit_count` == 1, `noise` is added to all qubits in `target_qubits`.

    When `noise.qubit_count` > 1, `noise.qubit_count` must be the same as the length of
    `target_qubits`.

    Args:
        circuit (Circuit): A ciruit where `noise` is applied to.
        noise (Noise): A Noise class object to be applied to the circuit.
        target_qubits (QubitSet): Index or indices of qubits. `noise` is applied to.

    Returns:
        Circuit: modified circuit.
    """

    if noise.qubit_count == 1:
        noise_instructions = [Instruction(noise, qubit) for qubit in target_qubits]
    else:
        noise_instructions = [Instruction(noise, target_qubits)]

    new_moments = Moments()

    # add existing instructions
    for moment_key in circuit.moments:
        instruction = circuit.moments[moment_key]
        # if the instruction is noise instruction
        if isinstance(instruction.operator, Noise):
            new_moments.add_noise(instruction, moment_key.moment_type, moment_key.noise_index)
        # if the instruction is a gate instruction
        else:
            new_moments.add([instruction], moment_key.noise_index)

    if position == "initialization":
        for noise in noise_instructions:
            new_moments.add_noise(noise, "initialization_noise")

    if position == "readout":
        for noise in noise_instructions:
            new_moments.add_noise(noise, "readout_noise")

    circuit._moments = new_moments
    return circuit


def apply_noise_to_gates(
    circuit: Circuit,
    noise: Noise,
    target_gates: Iterable[Type[Gate]],
    target_qubits: QubitSet,
) -> Circuit:
    """Apply noise after target gates in target qubits.

    When `noise.qubit_count` == 1, `noise` is applied to target_qubits after `target_gates`.

    When `noise.qubit_count` > 1, all elements in `target_gates`, if is given, must have
    the same number of qubits as `noise.qubit_count`.

    Args:
        circuit (Circuit): A ciruit where `noise` is applied to.
        noise (Noise): A `Noise` channel to be applied to the circuit.
        target_gates (Iterable[Type[Gate]]): List of Gate classes which `noise` is applied to.
        target_qubits (QubitSet): Index or indices of qubits which `noise` is applied to.

    Returns:
        Circuit: modified circuit.

    Raises:
        Warning:
            If `noise` is multi-qubit noise while there is no gate with the same
            number of qubits in `target_qubits` or in the whole circuit when
            `target_qubits` is not given.
            If no `target_gates` exist in `target_qubits` or in the whole circuit
            when `target_qubits` is not given.
    """

    new_moments = Moments()
    noise_applied = False
    for moment_key in circuit.moments:
        instruction = circuit.moments[moment_key]

        # add the instruction to new_moments if it is noise instruction
        if isinstance(instruction.operator, Noise):
            new_moments.add_noise(instruction, moment_key.moment_type, moment_key.noise_index)

        # if the instruction is a gate instruction
        else:
            new_noise_instruction = []
            noise_index = moment_key.noise_index
            if (target_gates is None) or (
                instruction.operator.name in [g.__name__ for g in target_gates]
            ):
                if noise.qubit_count == 1:
                    for qubit in instruction.target:
                        # apply noise to the qubit if it is in target_qubits
                        if qubit in target_qubits:
                            noise_index = noise_index + 1
                            new_noise_instruction.append((Instruction(noise, qubit), noise_index))
                            noise_applied = True
                else:
                    # only apply noise to the gates that have the same qubit_count as the noise.
                    if (
                        instruction.operator.qubit_count == noise.qubit_count
                        and instruction.target.issubset(target_qubits)
                    ):
                        noise_index = noise_index + 1
                        new_noise_instruction.append(
                            (Instruction(noise, instruction.target), noise_index)
                        )
                        noise_applied = True

            # add the gate and gate noise instructions to new_moments
            new_moments.add([instruction], noise_index=noise_index)
            for instruction, noise_index in new_noise_instruction:
                new_moments.add_noise(instruction, "gate_noise", noise_index)

    if noise_applied is False:
        warnings.warn(
            "Noise is not applied to any gate, as there is no eligible gate \
in the circuit with the input criteria or there is no multi-qubit gate to apply the multi-qubit \
noise."
        )
    circuit._moments = new_moments
    return circuit
