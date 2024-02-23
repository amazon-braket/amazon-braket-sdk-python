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
from typing import Union

import braket.circuits.circuit as cir
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType
from braket.circuits.noise import Noise
from braket.circuits.result_type import ResultType
from braket.registers.qubit import Qubit
from braket.registers.qubit_set import QubitSet


def _build_diagram_internal(target_class: type, circuit: cir.Circuit) -> str:
    """
    Build a text circuit diagram.

    The procedure follows as:
    1. Prepare the first column composed of the qubit identifiers
    2. Construct the circuit as a list of columns by looping through the
        time slices. A column is a string with rows separated via '\n'
        a. compute the instantaneous global phase
        b. create the column corresponding to the current moment
    3. Add result types at the end of the circuit
    4. Join the columns to get a list of qubit lines
    5. Add a list of optional parameters:
        a. the total global phase
        b. results types that do not have any target such as statevector
        c. the list of unassigned parameters

    Args:
        target_class (type): type of the diagram builder
        circuit (Circuit): Circuit for which to build a diagram.

    Returns:
        str: ASCII string circuit diagram.
    """

    if not circuit.instructions:
        return ""

    if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
        return f"Global phase: {circuit.global_phase}"

    circuit_qubits = circuit.qubits
    circuit_qubits.sort()

    y_axis_str, global_phase = _prepare_qubit_identifier_column(
        target_class, circuit, circuit_qubits
    )

    time_slices = circuit.moments.time_slices()
    column_strs = []

    # Moment columns
    for time, instructions in time_slices.items():
        global_phase = _compute_moment_global_phase(global_phase, instructions)
        moment_str = _ascii_diagram_column_set(
            target_class, str(time), circuit_qubits, instructions, global_phase
        )
        column_strs.append(moment_str)

    # Result type columns
    additional_result_types, target_result_types = _categorize_result_types(circuit.result_types)
    if target_result_types:
        column_strs.append(
            _ascii_diagram_column_set(
                target_class, "Result Types", circuit_qubits, target_result_types, global_phase
            )
        )

    # Unite strings
    lines = _unite_strings(y_axis_str, column_strs)
    target_class._duplicate_time_at_bottom(lines)

    if global_phase:
        lines.append(f"\nGlobal phase: {global_phase}")

    # Additional result types line on bottom
    if additional_result_types:
        lines.append(f"\nAdditional result types: {', '.join(additional_result_types)}")

    # A list of parameters in the circuit to the currently assigned values.
    if circuit.parameters:
        lines.append(
            "\nUnassigned parameters: "
            f"{sorted(circuit.parameters, key=lambda param: param.name)}."
        )

    return "\n".join(lines)


def _prepare_qubit_identifier_column(
    target_class: type, circuit: cir.Circuit, circuit_qubits: QubitSet
) -> tuple[str, float | None]:
    # Y Axis Column
    y_axis_width = len(str(int(max(circuit_qubits))))
    y_axis_str = "{0:{width}} : {vdelim}\n".format(
        "T", width=y_axis_width + 1, vdelim=target_class._vdelim
    )

    global_phase = None
    if any(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
        y_axis_str += "{0:{width}} : {vdelim}\n".format(
            "GP", width=y_axis_width, vdelim=target_class._vdelim
        )
        global_phase = 0

    for qubit in circuit_qubits:
        for _ in range(target_class._qubit_line_spacing["before"]):
            y_axis_str += "{0:{width}}\n".format(" ", width=y_axis_width + 5)

        y_axis_str += "q{0:{width}} : {qubit_line_char}\n".format(
            str(int(qubit)),
            width=y_axis_width,
            qubit_line_char=target_class._qubit_line_char,
        )

        for _ in range(target_class._qubit_line_spacing["after"]):
            y_axis_str += "{0:{width}}\n".format(" ", width=y_axis_width + 5)
    return y_axis_str, global_phase


def _unite_strings(first_column: str, column_strs: list[str]) -> str:
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
    moment_phase = 0
    for item in items:
        if (
            isinstance(item, Instruction)
            and isinstance(item.operator, Gate)
            and item.operator.name == "GPhase"
        ):
            moment_phase += item.operator.angle
    return global_phase + moment_phase if global_phase is not None else None


def _group_items(
    circuit_qubits: QubitSet,
    items: list[Union[Instruction, ResultType]],
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
        # Can only print Gate and Noise operators for instructions at the moment
        if isinstance(item, Instruction) and not isinstance(
            item.operator, (Gate, Noise, CompilerDirective)
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


def _ascii_diagram_column_set(
    target_class: type,
    col_title: str,
    circuit_qubits: QubitSet,
    items: list[Union[Instruction, ResultType]],
    global_phase: float | None,
) -> str:
    """
    Return a set of columns in the ASCII string diagram of the circuit for a list of items.

    Args:
        target_class (type): type of the diagram builder
        col_title (str): title of column set
        circuit_qubits (QubitSet): qubits in circuit
        items (list[Union[Instruction, ResultType]]): list of instructions or result types
        global_phase (float | None): the integrated global phase up to this set

    Returns:
        str: An ASCII string diagram for the column set.
    """

    # Group items to separate out overlapping multi-qubit items
    groupings = _group_items(circuit_qubits, items)

    column_strs = [
        target_class._ascii_diagram_column(circuit_qubits, grouping[1], global_phase)
        for grouping in groupings
    ]

    # Unite column strings
    lines = _unite_strings(column_strs[0], column_strs[1:])

    # Adjust for column title width
    col_title_width = len(col_title)
    symbols_width = len(lines[0]) - 1
    if symbols_width < col_title_width:
        diff = col_title_width - symbols_width
        for i in range(len(lines) - 1):
            if lines[i].endswith(target_class._qubit_line_char):
                lines[i] += target_class._qubit_line_char * diff
            else:
                lines[i] += " "

    first_line = "{:^{width}}{vdelim}\n".format(
        col_title, width=len(lines[0]) - 1, vdelim=target_class._vdelim
    )

    return first_line + "\n".join(lines)


def _create_output(
    target_class: type,
    symbols: dict[Qubit, str],
    margins: dict[Qubit, str],
    qubits: QubitSet,
    global_phase: float | None,
) -> str:
    """
    Creates the ouput for a single colum:
        a. If there was one or more gphase gate, create a first line with the total global
        phase shift ending with target_class.vdelim, e.g. 0.14|
        b. for each qubit, append the text representation produces by target_class.draw_symbol

    Args:
        target_class (type): type of the diagram builder
        symbols (dict[Qubit, str]): dictionary of the gate name for each qubit
        margins (dict[Qubit, str]): map of the qubit interconnections. Specific to the
            `target_class.draw_symbol` method.
        qubits (QubitSet): set of the circuit qubits
        global_phase (float | None): total global phase shift added during the moment

    Returns:
        str: a string representing a diagram column.
    """
    symbols_width = max([len(symbol) for symbol in symbols.values()]) + target_class._box_padding
    output = ""

    if global_phase is not None:
        global_phase_str = (
            f"{global_phase:.2f}" if isinstance(global_phase, float) else str(global_phase)
        )
        symbols_width = max([symbols_width, len(global_phase_str)])
        output += "{0:{fill}{align}{width}}{vdelim}\n".format(
            global_phase_str,
            fill=" ",
            align="^",
            width=symbols_width,
            vdelim=target_class._vdelim,
        )

    for qubit in qubits:
        output += target_class._draw_symbol(symbols[qubit], symbols_width, margins[qubit])
    return output
