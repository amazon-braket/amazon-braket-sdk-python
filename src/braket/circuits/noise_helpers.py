from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Iterable, Optional, Type

from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.noise import Noise
from braket.circuits.qubit_set import QubitSet, QubitSetInput

if TYPE_CHECKING:  # pragma: no cover
    from braket.circuits.circuit import Circuit


def check_noise_target_gates(noise: Noise, target_gates: Iterable[Type[Gate]]):
    """Helper function to check
    1. whether all the elements in target_gates are a Gate type;
    2. if `noise` is multi-qubit noise and `target_gates` contain gates
    with the number of qubits is the same as `noise.qubit_count`.
    Args:
        noise (Noise): A Noise class object to be applied to the circuit.
        target_gates (Union[Type[Gate], Iterable[Type[Gate]]]): Gate class or
            List of Gate classes which `noise` is applied to.
    """

    if not all(isinstance(g, type) and issubclass(g, Gate) for g in target_gates):
        raise TypeError("All elements in target_gates must be an instance of the Gate class")

    if noise.qubit_count > 1:
        for g in target_gates:
            if g().qubit_count != noise.qubit_count:
                raise ValueError(
                    "The target_targets must be gates that have the same number of \
qubits as defined by the multi-qubit noise channel."
                )


def check_noise_target_qubits(
    circuit: Circuit, target_qubits: Optional[QubitSetInput] = None
) -> QubitSet:
    """
    Helper function to check whether all the target_qubits are positive integers.
    Args:
        target_qubits (Optional[QubitSetInput] = None): Index or indices of qubit(s).
    Returns:
        target_qubits: QubitSet
    """
    if target_qubits is None:
        target_qubits = circuit.qubits
    else:
        if not isinstance(target_qubits, list):
            target_qubits = [target_qubits]
        if not all(isinstance(q, int) for q in target_qubits):
            raise TypeError("target_qubits must be integer(s)")
        if not all(q >= 0 for q in target_qubits):
            raise ValueError("target_qubits must contain only non-negative integers.")

        target_qubits = QubitSet(target_qubits)

    return target_qubits


def apply_noise_to_moments(
    circuit: Circuit, noise: Iterable[Type[Noise]], target_qubits: QubitSet, position: str
) -> Circuit:
    """Apply initialization/readout noise to the circuit.

    When `noise.qubit_count` == 1, `noise` is added to all qubits in `target_qubits`.

    When `noise.qubit_count` > 1, `noise.qubit_count` must be the same as the length of
    `target_qubits`.

    Args:
        circuit (Circuit): A ciruit where `noise` is applied to.
        noise (Iterable[Type[Noise]]): Noise channel(s) to be applied
        to the circuit.
        target_qubits (QubitSet): Index or indices of qubits. `noise` is applied to.

    Returns:
        Circuit: modified circuit.
    """
    noise_instructions = []
    for noise_channel in noise:
        if noise_channel.qubit_count == 1:
            new = [Instruction(noise_channel, qubit) for qubit in target_qubits]
            noise_instructions = noise_instructions + new
        else:
            noise_instructions.append(Instruction(noise_channel, target_qubits))

    new_moments = Moments()

    if position == "initialization":
        for noise in noise_instructions:
            new_moments.add_noise(noise, "initialization_noise")

    # add existing instructions
    for moment_key in circuit.moments:
        instruction = circuit.moments[moment_key]
        # if the instruction is noise instruction
        if isinstance(instruction.operator, Noise):
            new_moments.add_noise(instruction, moment_key.moment_type, moment_key.noise_index)
        # if the instruction is a gate instruction
        else:
            new_moments.add([instruction], moment_key.noise_index)

    if position == "readout":
        for noise in noise_instructions:
            new_moments.add_noise(noise, "readout_noise")

    circuit._moments = new_moments

    return circuit


def apply_noise_to_gates(
    circuit: Circuit,
    noise: Iterable[Type[Noise]],
    target_gates: Iterable[Type[Gate]],
    target_qubits: QubitSet,
) -> Circuit:
    """Apply noise after target gates in target qubits.

    When `noise.qubit_count` == 1, `noise` is applied to target_qubits after `target_gates`.

    When `noise.qubit_count` > 1, all elements in `target_gates`, if is given, must have
    the same number of qubits as `noise.qubit_count`.

    Args:
        circuit (Circuit): A ciruit where `noise` is applied to.
        noise (Iterable[Type[Noise]]): Noise channel(s) to be applied
        to the circuit.
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
                for noise_channel in noise:
                    if noise_channel.qubit_count == 1:
                        intersection = list(set(instruction.target) & set(target_qubits))
                        for qubit in intersection:
                            # apply noise to the qubit if it is in target_qubits
                            noise_index = noise_index + 1
                            new_noise_instruction.append(
                                (Instruction(noise_channel, qubit), noise_index)
                            )
                            noise_applied = True
                    else:
                        # only apply noise to the gates that have the same qubit_count as the noise.
                        if (
                            instruction.operator.qubit_count == noise_channel.qubit_count
                            and instruction.target.issubset(target_qubits)
                        ):
                            noise_index = noise_index + 1
                            new_noise_instruction.append(
                                (Instruction(noise_channel, instruction.target), noise_index)
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
