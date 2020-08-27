from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.noise import Noise
from braket.circuits.qubit_set import QubitSet, QubitSetInput

if TYPE_CHECKING:  # pragma: no cover
    from braket.circuits.circuit import Circuit


def _add_noise(
    circuit: Circuit,
    noise: Noise,
    target_gates: Iterable[str],
    target_qubits: QubitSetInput,
    target_times: Iterable[int],
) -> Circuit:
    """Insert noise into circuit.
    Add the provided `noise` to gates, qubits and time specified by `target_gates`,
    `target_qubits` and `target_times`. See the description of circuit.add_noise().

    Args:
        circuit (Circuit): A circuit where `noise` is added to.
        noise (Noise): A `Noise` class object to be added to the circuit.
        target_gates (Iterable[str] or None): List of name of gates which `noise` is
            added to. If None, `noise` is added only according to `target_qubits` and
            `target_times`. None should be used when users want to add `noise` to
            a ciruit moment that has no gate.
        target_qubits (QubitSet or None): Index or indices of qubits. When `target_gates` is
            not None, the usage of `target_qubits` is determined by `insert_strategy`.
        target_times (Iterable[int] or None): List of time which `noise` is added to.

    Returns:
        Circuit: modified circuit.
    """
    if target_gates is None:
        if noise.qubit_count > 1 and not noise.qubit_count == len(target_qubits):
            raise ValueError(
                "the qubit count of multiple-qubit noise must be the same "
                "as the length of target qubits"
            )
        circuit = _add_noise_to_qubits(circuit, noise, target_qubits, target_times)
    else:
        if noise.qubit_count > 1:
            for instr in circuit.instructions:
                if (
                    instr.operator.name in target_gates
                    and not instr.operator.qubit_count == noise.qubit_count
                ):
                    raise ValueError(
                        "the qubit count of multiple-qubit noise must be "
                        "the same as the qubit count of target gates"
                    )
        circuit = _add_noise_to_gates(circuit, noise, target_gates, target_qubits, target_times)

    return circuit


def _add_noise_to_qubits(
    circuit: Circuit, noise: Noise, target_qubits: QubitSet, target_times: Iterable[int]
) -> Circuit:
    """Insert noise to the given time and qubits.

    Args:
        circuit (Circuit): A ciruit where `noise` is added to.
        noise (Noise): A Noise class object to be added to the circuit.
        target_qubits (QubitSet): Index or indices of qubits. `noise` is added to.
        target_times (List[int]): List of time which `noise` is added to.

    Returns:
        Circuit: modified circuit.
    """
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
        if target_times is None or time in target_times:
            new_moments.add(noise_instructions)

    circuit._moments = new_moments
    return circuit


def _add_noise_to_gates(
    circuit: Circuit,
    noise: Noise,
    target_gates: Iterable[str],
    target_qubits: QubitSet,
    target_times: Iterable[int],
) -> Circuit:
    """Insert noise to the given time, qubits and gates.

    Args:
        circuit (Circuit): A ciruit where `noise` is added to.
        noise (Noise): A `Noise` class object to be added to the circuit.
        target_gates (Iterable[str]): List of name of gates which `noise` is added to.
        target_qubits (QubitSet): Index or indices of qubits which `noise` is added to.
        target_times (Iterable[int]): List of time which `noise` is added to.
        insert_strategy (str): Rule of how `target_qubit` is used.

    Returns:
        Circuit: modified circuit.
    """
    new_moments = Moments()
    for moment_key in circuit.moments:
        # add existing instruction
        instruction = circuit.moments[moment_key]
        new_moments.add([instruction])
        # add noise
        # (If adding different insert strategies in the future, consider moving these rules
        # to a separate function or class.)
        gate_rule = instruction.operator.name in target_gates
        qubit_rule = target_qubits is None or instruction.target.issubset(target_qubits)
        time_rule = target_times is None or moment_key.time in target_times
        if gate_rule and qubit_rule and time_rule:
            if noise.qubit_count == 1:
                for qubit in instruction.target:
                    new_moments.add([Instruction(noise, qubit)])
            else:
                new_moments.add([Instruction(noise, instruction.target)])
    circuit._moments = new_moments
    return circuit
