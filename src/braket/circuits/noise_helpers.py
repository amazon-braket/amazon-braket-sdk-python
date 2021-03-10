from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Type

from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.noise import Noise
from braket.circuits.qubit_set import QubitSet

if TYPE_CHECKING:  # pragma: no cover
    from braket.circuits.circuit import Circuit


def add_noise_to_moments(
    circuit: Circuit, noise: Noise, target_qubits: QubitSet, target_moments: Iterable[int]
) -> Circuit:
    """Insert noise to the given time and qubits.

    When `noise.qubit_count` == 1, `noise` is added to all qubits in `target_qubits`.

    When `noise.qubit_count` > 1, `noise.qubit_count` must be the same as the length of
    `target_qubits`.

    Args:
        circuit (Circuit): A ciruit where `noise` is added to.
        noise (Noise): A Noise class object to be added to the circuit.
        target_qubits (QubitSet): Index or indices of qubits. `noise` is added to.
        target_moments (List[int]): List of moments which `noise` is added in.

    Returns:
        Circuit: modified circuit.

    Raises:
        ValueError:
            If `noise.qubit_count` is not equal to `len(target_qubits)`.
    """
    if noise.qubit_count > 1 and not noise.qubit_count == len(target_qubits):
        raise ValueError(
            "the qubit count of multiple-qubit noise must be the same "
            "as the length of target qubits"
        )

    if target_qubits is None:
        target_qubits = circuit.qubits

    if noise.qubit_count == 1:
        noise_instructions = [Instruction(noise, qubit) for qubit in target_qubits]
    else:
        noise_instructions = [Instruction(noise, target_qubits)]

    new_moments = Moments()
    time_slices = circuit.moments.time_slices()
    for time in range(circuit.depth):
        # add existing instructions
        new_moments.add(time_slices[time])
        # add noise
        if target_moments is None or time in target_moments:
            for instruction in noise_instructions:
                new_moments._add_noise(instruction, time)

    circuit._moments = new_moments
    return circuit


def add_noise_to_gates(
    circuit: Circuit,
    noise: Noise,
    target_gates: Iterable[Type[Gate]],
    target_qubits: QubitSet,
    target_moments: Iterable[int],
) -> Circuit:
    """Insert noise after the given gates at the given time, qubits.

    When `noise.qubit_count` == 1, `noise` is added to all qubits in `target_gates`.

    When `noise.qubit_count` > 1, `noise.qubit_count` must be the same as `qubit_count` of
    gates specified by `target_gates`.

    Args:
        circuit (Circuit): A ciruit where `noise` is added to.
        noise (Noise): A `Noise` class object to be added to the circuit.
        target_gates (Iterable[Type[Gate]]): List of Gate classes which `noise` is added to.
        target_qubits (QubitSet): Index or indices of qubits which `noise` is added to.
        target_moments (Iterable[int]): List of time which `noise` is added to.

    Returns:
        Circuit: modified circuit.

    Raises:
        ValueError:
            If `noise.qubit_count` is not equal to `len(gate.target)` for gates in `target_gates`.
    """
    new_moments = Moments()
    for moment_key in circuit.moments:
        # add existing instruction
        instruction = circuit.moments[moment_key]
        new_moments.add([instruction])
        # add noise
        # (If adding different insert strategies in the future, consider moving these rules
        # to a separate function or class.)
        gate_rule = instruction.operator.name in [g.__name__ for g in target_gates]
        qubit_rule = target_qubits is None or instruction.target.issubset(target_qubits)
        time_rule = target_moments is None or moment_key.time in target_moments
        if gate_rule and qubit_rule and time_rule:
            if noise.qubit_count == 1:
                for qubit in instruction.target:
                    new_moments.add([Instruction(noise, qubit)])
            else:
                if instruction.operator.qubit_count == noise.qubit_count:
                    new_moments.add([Instruction(noise, instruction.target)])
                else:
                    raise ValueError(
                        "the qubit count of multiple-qubit noise must be "
                        "the same as the qubit count of target gates"
                    )
    circuit._moments = new_moments
    return circuit
