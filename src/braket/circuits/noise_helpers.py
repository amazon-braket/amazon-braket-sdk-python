from __future__ import annotations

from typing import TYPE_CHECKING, List, Iterable

from braket.circuits.instruction import Instruction
from braket.circuits.moments import Moments
from braket.circuits.noise import Noise
from braket.circuits.qubit_set import QubitSet, QubitSetInput

if TYPE_CHECKING: # pragma: no cover
    from braket.circuits.circuit import Circuit


def _add_noise(
    circ: Circuit,
    noise: Noise,
    target_gates: Iterable[str],
    target_qubits: QubitSetInput,
    target_times: Iterable[int],
    insert_strategy: str,
) -> Circuit:
    """ Insert noise into circuit.
    Add the provided `noise` to gates, qubits and time specified by `target_gates`
    , `target_qubits` and `target_times`. See the description of circuit.add_noise().

    Args:
        circ (Circuit): A ciruit where `noise` is added to.
        noise (Noise): A `Noise` class object to be added to the circuit.
        target_gates (Iterable[str] or None): List of name of gates which `noise` is added to.
            If None, `noise` is added only according to `target_qubits` and
            `target_times`. None should be used when users want to add `noise` to
            a ciruit moment that has no gate.
        target_qubits (QubitSet): Index or indices of qubit. When `target_gates` is
            not None, the usage of `target_qubits` is determined by `insert_strategy`.
        target_times (Iterable[int]): List of time which `noise` is added to.
        insert_strategy (str): Rule of how `target_qubit` is used. `insert_strategy`
            is usded only when `target_gates` is not None.
            "strict": Insert noise to a gate when `gate.target` exactly matches
                `target_qubits`. Sensitive to order of qubits.
            "inclusive":Insert noise to a gate when the target of the gate is a subset
                of `target_qubits`.

    Returns:
        Circuit: modified circuit.
    """
    if target_gates:
        circ = _add_noise_to_gates(
            circ, noise, target_gates, target_qubits, target_times, insert_strategy
        )
    else:
        circ = _add_noise_to_qubits(circ, noise, target_qubits, target_times)

    return circ


def _add_noise_to_qubits(
    circ: Circuit, noise: Noise, target_qubits: QubitSet, target_times: Iterable[int]
) -> Circuit:
    """ Insert noise to the given time and qubits.

    Args:
        circ (Circuit): A ciruit where `noise` is added to.
        noise (Noise): A Noise class object to be added to the circuit.
        target_qubits (QubitSet): Index or indices of qubit. `noise` is added to.
        target_times (List[int]): List of time which `noise` is added to.

    Returns:
        Circuit: modified circuit.
    """
    if noise.qubit_count == 1:
        noise_instructions = [Instruction(noise, qubit) for qubit in target_qubits]
    else:
        noise_instructions = [Instruction(noise, target_qubits)]

    new_moments = Moments()
    time_slices = circ.moments.time_slices()
    for time in range(circ.depth):
        # add existing instructions
        new_moments.add(time_slices[time])
        # add noise
        if time in target_times:
            new_moments.add(noise_instructions)

    circ._moments = new_moments
    return circ


def _add_noise_to_gates(
    circ: Circuit,
    noise: Noise,
    target_gates: Iterable[str],
    target_qubits: QubitSet,
    target_times: Iterable[int],
    insert_strategy: str,
) -> Circuit:
    """ Insert noise to the given time, qubits and gates.

    Args:
        circ (Circuit): A ciruit where `noise` is added to.
        noise (Noise): A `Noise` class object to be added to the circuit.
        target_gates (Iterable[str]): List of name of gates which `noise` is added to.
        target_qubits (QubitSet): Index or indices of qubit which `noise` is added to.
        target_times (Iterable[int]): List of time which `noise` is added to.
        insert_strategy (str): Rule of how `target_qubit` is used.

    Returns:
        Circuit: modified circuit.
    """
    strategy = getattr(NoiseInsertStrategy, insert_strategy)
    new_moments = Moments()
    for moment_key in circ.moments:
        # add existing instruction
        instruction = circ.moments[moment_key]
        new_moments.add([instruction])
        # add noise
        if instruction.operator.name in target_gates and moment_key.time in target_times:
            if noise.qubit_count == 1:
                strategy._add_1qubit_noise(new_moments, instruction, noise, target_qubits)
            else:
                strategy._add_Nqubit_noise(new_moments, instruction, noise, target_qubits)

    circ._moments = new_moments
    return circ


def type_check_target_gates(target_gates):
    """ Validate the type of `target_gates`
    Valid types: None, Iterable[str]

    Returns: bool
    """
    if target_gates == None:
        return True
    if (isinstance(target_gates, Iterable)
        and all(isinstance(s, str) for s in target_gates)
    ):
        return True
    return False


def type_check_target_times(target_times):
    """ Validate the type of `target_gates`
    Valid types: Iterable[int]

    Returns: bool
    """
    return (isinstance(target_times, Iterable)
            and all(isinstance(time, int) for time in target_times)
    )


class NoiseInsertStrategy:
    """ Base class of noise insert strategy.
    """

    @staticmethod
    def _add_1qubit_noise():
        raise NotImplementedError("_add_1qubit_noise has not been implemented yet.")

    @staticmethod
    def _add_Nqubit_noise():
        raise NotImplementedError("_add_Nqubit_noise has not been implemented yet.")

    @classmethod
    def register_strategy(cls, name: str, strategy: "NoiseInsertStrategy"):
        """Register a insert strategy.

        Args:
            strategy (NoiseInsertStrategy): NoiseInsertStrategy class to register.
        """
        setattr(cls, name, strategy)


class InclusiveStrategy(NoiseInsertStrategy):
    """ Inclusive strategy for noise insertion.
    Insert noise to a gate when the target of the gate is a subset of `target_qubits`.
    """

    @staticmethod
    def _add_1qubit_noise(
        new_moments: Moments, instruction: Instruction, noise: Noise, target_qubits: QubitSet
    ):
        for qubit in instruction.target.intersection(target_qubits):
            new_moments.add([Instruction(noise, qubit)])

    @staticmethod
    def _add_Nqubit_noise(
        new_moments: Moments, instruction: Instruction, noise: Noise, target_qubits: QubitSet
    ):
        if (instruction.operator.qubit_count == noise.qubit_count
            and instruction.target.issubset(target_qubits)
        ):
            new_moments.add([Instruction(noise, instruction.target)])


NoiseInsertStrategy.register_strategy("inclusive", InclusiveStrategy)


class StrictStrategy(NoiseInsertStrategy):
    """ Strict strategy for noise insertion.
    Insert noise to a gate when `gate.target` exactly matches `target_qubits`.
    Sensitive to order of qubits.
    """

    @staticmethod
    def _add_1qubit_noise(
        new_moments: Moments, instruction: Instruction, noise: Noise, target_qubits: QubitSet
    ):
        if instruction.target == target_qubits:
            for qubit in target_qubits:
                new_moments.add([Instruction(noise, qubit)])

    @staticmethod
    def _add_Nqubit_noise(
        new_moments: Moments, instruction: Instruction, noise: Noise, target_qubits: QubitSet
    ):
        if instruction.target == target_qubits:
            new_moments.add([Instruction(noise, instruction.target)])


NoiseInsertStrategy.register_strategy("strict", StrictStrategy)
