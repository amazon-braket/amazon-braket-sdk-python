from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from enum import StrEnum
from typing import TYPE_CHECKING, Union

from braket.circuits.moments import MomentType
from braket.circuits.operator import Operator
from braket.registers.qubit import QubitInput
from braket.registers.qubit_set import QubitSet

if TYPE_CHECKING:
    from braket.circuits.circuit import Circuit


class QubitMatch(StrEnum):
    """Controls how multiple qubits are matched in count_instructions."""

    ANY = "ANY"
    ALL = "ALL"


OperatorIdentifier = Union[str, type[Operator], Operator]


def _normalize_operator_name(identifier: OperatorIdentifier) -> str:
    if isinstance(identifier, type):
        return identifier.__name__.upper()
    if isinstance(identifier, str):
        return identifier.upper()
    return identifier.name.upper()


def _to_operator_names(
    operators: OperatorIdentifier | Iterable[OperatorIdentifier] | None,
) -> list[str]:
    if operators is None:
        return []
    if isinstance(operators, (str, type)) or isinstance(operators, Operator):
        return [_normalize_operator_name(operators)]
    return [_normalize_operator_name(op) for op in operators]


def count_instructions(
    circuit: Circuit,
    operators: OperatorIdentifier | Iterable[OperatorIdentifier] | None = None,
    qubits: QubitInput | Iterable[QubitInput] | None = None,
    qubit_match: QubitMatch = QubitMatch.ANY,
    include_types: Iterable[MomentType] = (MomentType.GATE,),
) -> Counter[str]:
    """
    Count instructions in a circuit with optional filtering.

    When both ``operators`` and ``qubits`` are specified, an instruction must satisfy
    both filters to be counted (AND semantics).

    Args:
        circuit (Circuit): The circuit to analyse.
        operators: Filter by operator name or type. Defaults to None (no filter).
        qubits: Filter by qubit. Matched against the union of target and control qubits.
        qubit_match (QubitMatch): How multiple qubits relate. ANY = instruction on
        any specified qubit; ALL = instruction on all specified qubits. Default ANY.
        include_types (Iterable[MomentType]): Moment types to count. Default: GATE only.
            Pass additional MomentType values to include noise, measures, etc.

    Returns:
        Counter[str]: Operator names mapped to occurrence counts.
    """
    include_types_set = set(include_types)
    operator_names_set = set(_to_operator_names(operators))
    _qs = QubitSet(qubits) if qubits is not None else None
    filter_qubits = _qs if _qs else None  # empty QubitSet treated as no filter

    result: Counter[str] = Counter()

    for key, instruction in circuit.moments.items():
        if key.moment_type not in include_types_set:
            continue

        instr_qubits = instruction.target.union(instruction.control)
        instr_name_upper = instruction.operator.name.upper()

        qubit_pass = filter_qubits is None or (
            any(q in instr_qubits for q in filter_qubits)
            if qubit_match == QubitMatch.ANY
            else all(q in instr_qubits for q in filter_qubits)
        )
        operator_pass = not operator_names_set or instr_name_upper in operator_names_set

        if qubit_pass and operator_pass:
            result[instruction.operator.name] += 1

    return result
