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

from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from typing import TYPE_CHECKING

from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.result_type import ResultType
from braket.registers.qubit_set import QubitSet

if TYPE_CHECKING:
    from braket.circuits import Circuit


@dataclass
class GateBox:
    """A gate drawn as a labelled box."""

    col: int
    row: int
    label: str
    metadata_key: str | None = None
    parameter_text: str | None = None


@dataclass
class ControlDot:
    """A control qubit indicator (filled = control, open = anti-control)."""

    col: int
    row: int
    filled: bool


@dataclass
class SwapMarker:
    """A SWAP gate drawn as an 'x' on a qubit wire."""

    col: int
    row: int


@dataclass
class Connection:
    """A vertical wire connecting qubits of a multi-qubit gate."""

    col: int
    row_start: int
    row_end: int


@dataclass
class BarrierMarker:
    """A barrier indicator on a single qubit wire."""

    col: int
    row: int


@dataclass
class CircuitLayout:
    """Complete layout description produced by GraphicalCircuitDiagram._compute_layout()."""

    num_qubits: int
    num_moments: int
    qubit_labels: list[str]
    moment_labels: list[str]
    elements: list = field(default_factory=list)
    global_phase: float | None = None
    additional_result_types: list[str] = field(default_factory=list)
    unassigned_parameters: list[str] = field(default_factory=list)


def _compute_moment_global_phase(
    global_phase: float | None, items: list[Instruction]
) -> float | None:
    moment_phase = sum(
        item.operator.angle * item.power
        for item in items
        if (
            isinstance(item, Instruction)
            and isinstance(item.operator, Gate)
            and item.operator.name == "GPhase"
        )
    )
    return global_phase + moment_phase if global_phase is not None else None


def _get_qubit_range_for_item(item: Instruction | ResultType, circuit_qubits: QubitSet) -> QubitSet:
    if (
        isinstance(item, Instruction)
        and isinstance(item.operator, Gate)
        and item.operator.name == "GPhase"
    ):
        return QubitSet()

    if isinstance(item, ResultType) and not item.target:
        return circuit_qubits

    if isinstance(item, Instruction) and isinstance(item.operator, CompilerDirective):
        return _get_compiler_directive_qubit_range(item, circuit_qubits)

    return _get_standard_qubit_range(item)


def _get_compiler_directive_qubit_range(item: Instruction, circuit_qubits: QubitSet) -> QubitSet:
    if item.operator.name == "Barrier":
        if not item.target or len(item.target) == 0:
            return circuit_qubits
        return QubitSet(item.target)
    return circuit_qubits


def _get_standard_qubit_range(item: Instruction | ResultType) -> QubitSet:
    if isinstance(item.target, list):
        target = reduce(QubitSet.union, map(QubitSet, item.target), QubitSet())
    else:
        target = item.target
    control = getattr(item, "control", QubitSet())
    target_and_control = target.union(control)
    return QubitSet(range(min(target_and_control), max(target_and_control) + 1))


def _group_items(
    circuit_qubits: QubitSet,
    items: list[Instruction | ResultType],
) -> list[tuple[QubitSet, list[Instruction]]]:
    groupings = []
    for item in items:
        if isinstance(item, Instruction) and not isinstance(
            item.operator, CompilerDirective | QuantumOperator
        ):
            continue

        qubit_range = _get_qubit_range_for_item(item, circuit_qubits)

        found_grouping = False
        for group in groupings:
            qubits_added = group[0]
            instr_group = group[1]
            if not qubits_added.intersection(set(qubit_range)):
                instr_group.append(item)
                qubits_added.update(qubit_range)
                found_grouping = True
                break

        if not found_grouping:
            groupings.append((qubit_range, [item]))

    return groupings


def _categorize_result_types(
    result_types: list[ResultType],
) -> tuple[list[str], list[ResultType]]:
    additional_result_types = []
    target_result_types = []
    for result_type in result_types:
        if hasattr(result_type, "target"):
            target_result_types.append(result_type)
        else:
            additional_result_types.extend(result_type.ascii_symbols)
    return additional_result_types, target_result_types


def _has_global_phase(circuit: Circuit) -> bool:
    return any(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments)
