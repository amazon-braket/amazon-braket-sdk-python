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

from functools import reduce

import braket.circuits.circuit as cir
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.measure import Measure
from braket.circuits.moments import MomentType
from braket.circuits.noise import Noise
from braket.circuits.result_type import ResultType
from braket.registers.qubit_set import QubitSet


def _add_footers(
    lines: list,
    circuit: cir.Circuit,
    global_phase: float | None,
    additional_result_types: list[str],
) -> str:
    if global_phase:
        lines.append(f"\nGlobal phase: {global_phase}")

    # Additional result types line on bottom
    if additional_result_types:
        lines.append(f"\nAdditional result types: {', '.join(additional_result_types)}")

    # A list of parameters in the circuit to the currently assigned values.
    if circuit.parameters:
        lines.append(
            f"\nUnassigned parameters: {sorted(circuit.parameters, key=lambda param: param.name)}."
        )

    return "\n".join(lines)


def _prepare_qubit_identifier_column(
    circuit: cir.Circuit,
    circuit_qubits: QubitSet,
    vdelim: str,
    qubit_line_char: str,
    line_spacing_before: int,
    line_spacing_after: int,
) -> tuple[str, float | None]:
    # Y Axis Column
    y_axis_width = len(str(int(max(circuit_qubits))))
    y_axis_str = "{0:{width}} : {vdelim}\n".format("T", width=y_axis_width + 1, vdelim=vdelim)

    global_phase = None
    if any(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
        y_axis_str += "{0:{width}} : {vdelim}\n".format("GP", width=y_axis_width, vdelim=vdelim)
        global_phase = 0

    for qubit in circuit_qubits:
        for _ in range(line_spacing_before):
            y_axis_str += "{0:{width}}\n".format(" ", width=y_axis_width + 5)

        y_axis_str += "q{0:{width}} : {qubit_line_char}\n".format(
            str(int(qubit)),
            width=y_axis_width,
            qubit_line_char=qubit_line_char,
        )

        for _ in range(line_spacing_after):
            y_axis_str += "{0:{width}}\n".format(" ", width=y_axis_width + 5)
    return y_axis_str, global_phase


def _unite_strings(first_column: str, column_strs: list[str]) -> list:
    lines = first_column.split("\n")
    for col_str in column_strs:
        for i, line_in_col in enumerate(col_str.split("\n")):
            lines[i] += line_in_col
    return lines


def _compute_moment_global_phase(
    global_phase: float | None, items: list[Instruction]
) -> float | None:
    """
    Compute the integrated phase at a certain moment.

    Args:
        global_phase (float | None): The integrated phase up to the computed moment
        items (list[Instruction]): list of instructions

    Returns:
        float | None: The updated integrated phase.
    """
    moment_phase = sum(
        item.operator.angle
        for item in items
        if (
            isinstance(item, Instruction)
            and isinstance(item.operator, Gate)
            and item.operator.name == "GPhase"
        )
    )
    return global_phase + moment_phase if global_phase is not None else None


def _group_items(
    circuit_qubits: QubitSet,
    items: list[Instruction | ResultType],
) -> list[tuple[QubitSet, list[Instruction]]]:
    """
    Group instructions in a moment

    Args:
        circuit_qubits (QubitSet): set of qubits in circuit
        items (list[Union[Instruction, ResultType]]): list of instructions or result types

    Returns:
        list[tuple[QubitSet, list[Instruction]]]: list of grouped instructions or result types.
    """
    groupings = []
    for item in items:
        # Can only print Gate, Noise and Measure operators for instructions at the moment
        if isinstance(item, Instruction) and not isinstance(
            item.operator, (Gate, Noise, CompilerDirective, Measure)
        ):
            continue

        # As a zero-qubit gate, GPhase can be grouped with anything. We set qubit_range
        # to an empty list and we just add it to the first group below.
        if (
            isinstance(item, Instruction)
            and isinstance(item.operator, Gate)
            and item.operator.name == "GPhase"
        ):
            qubit_range = QubitSet()
        elif (isinstance(item, ResultType) and not item.target) or (
            isinstance(item, Instruction) and isinstance(item.operator, CompilerDirective)
        ):
            qubit_range = circuit_qubits
        else:
            if isinstance(item.target, list):
                target = reduce(QubitSet.union, map(QubitSet, item.target), QubitSet())
            else:
                target = item.target
            control = getattr(item, "control", QubitSet())
            target_and_control = target.union(control)
            qubit_range = QubitSet(range(min(target_and_control), max(target_and_control) + 1))

        found_grouping = False
        for group in groupings:
            qubits_added = group[0]
            instr_group = group[1]
            # Take into account overlapping multi-qubit gates
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
    """
    Categorize result types into result types with target and those without.

    Args:
        result_types (list[ResultType]): list of result types

    Returns:
        tuple[list[str], list[ResultType]]: first element is a list of result types
        without `target` attribute; second element is a list of result types with
        `target` attribute
    """
    additional_result_types = []
    target_result_types = []
    for result_type in result_types:
        if hasattr(result_type, "target"):
            target_result_types.append(result_type)
        else:
            additional_result_types.extend(result_type.ascii_symbols)
    return additional_result_types, target_result_types
