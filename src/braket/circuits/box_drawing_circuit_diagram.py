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
from typing import Literal, Union

import braket.circuits.circuit as cir
from braket.circuits.circuit_diagram import CircuitDiagram
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType
from braket.circuits.noise import Noise
from braket.circuits.result_type import ResultType
from braket.registers.qubit import Qubit
from braket.registers.qubit_set import QubitSet


class BoxDrawingCircuitDiagram(CircuitDiagram):
    """Builds ASCII string circuit diagrams."""

    @staticmethod
    def build_diagram(circuit: cir.Circuit) -> str:
        """
        Build an ASCII string circuit diagram.

        Args:
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

        y_axis_str, global_phase = BoxDrawingCircuitDiagram._prepare_diagram_vars(
            circuit, circuit_qubits
        )

        time_slices = circuit.moments.time_slices()
        column_strs = []

        # Moment columns
        for time, instructions in time_slices.items():
            global_phase = BoxDrawingCircuitDiagram._compute_moment_global_phase(
                global_phase, instructions
            )
            moment_str = BoxDrawingCircuitDiagram._ascii_diagram_column_set(
                str(time), circuit_qubits, instructions, global_phase
            )
            column_strs.append(moment_str)

        # Result type columns
        (
            additional_result_types,
            target_result_types,
        ) = BoxDrawingCircuitDiagram._categorize_result_types(circuit.result_types)
        if target_result_types:
            column_strs.append(
                BoxDrawingCircuitDiagram._ascii_diagram_column_set(
                    "Result Types", circuit_qubits, target_result_types, global_phase
                )
            )

        # Unite strings
        lines = y_axis_str.split("\n")
        for col_str in column_strs:
            for i, line_in_col in enumerate(col_str.split("\n")):
                lines[i] += line_in_col

        # Replace the last (empty) line with time
        lines[-1] = lines[0]

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

    @staticmethod
    def _prepare_diagram_vars(
        circuit: cir.Circuit, circuit_qubits: QubitSet
    ) -> tuple[str, float | None]:
        # Y Axis Column
        y_axis_width = len(str(int(max(circuit_qubits))))
        y_axis_str = "{0:{width}} : │\n".format("T", width=y_axis_width + 1)

        global_phase = None
        if any(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            y_axis_str += "{0:{width}} : │\n".format("GP", width=y_axis_width)
            global_phase = 0

        for qubit in circuit_qubits:
            y_axis_str += "{0:{width}}\n".format(" ", width=y_axis_width + 5)
            y_axis_str += "q{0:{width}} : ─\n".format(str(int(qubit)), width=y_axis_width)
            y_axis_str += "{0:{width}}\n".format(" ", width=y_axis_width + 5)

        return y_axis_str, global_phase

    @staticmethod
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

    @staticmethod
    def _ascii_group_items(
        circuit_qubits: QubitSet,
        items: list[Union[Instruction, ResultType]],
    ) -> list[tuple[QubitSet, list[Instruction]]]:
        """
        Group instructions in a moment for ASCII diagram

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

    @staticmethod
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

    @staticmethod
    def _ascii_diagram_column_set(
        col_title: str,
        circuit_qubits: QubitSet,
        items: list[Union[Instruction, ResultType]],
        global_phase: float | None,
    ) -> str:
        """
        Return a set of columns in the ASCII string diagram of the circuit for a list of items.

        Args:
            col_title (str): title of column set
            circuit_qubits (QubitSet): qubits in circuit
            items (list[Union[Instruction, ResultType]]): list of instructions or result types
            global_phase (float | None): the integrated global phase up to this set

        Returns:
            str: An ASCII string diagram for the column set.
        """

        # Group items to separate out overlapping multi-qubit items
        groupings = BoxDrawingCircuitDiagram._ascii_group_items(circuit_qubits, items)

        column_strs = [
            BoxDrawingCircuitDiagram._ascii_diagram_column(
                circuit_qubits, grouping[1], global_phase
            )
            for grouping in groupings
        ]

        # Unite column strings
        lines = column_strs[0].split("\n")
        for column_str in column_strs[1:]:
            for i, moment_line in enumerate(column_str.split("\n")):
                lines[i] += moment_line

        first_line = "{:^{width}}│\n".format(col_title, width=len(lines[0]) - 1)

        return first_line + "\n".join(lines)

    @staticmethod
    def _build_parameters(
        circuit_qubits: QubitSet, item: ResultType | Instruction, connections: dict[Qubit, str]
    ) -> tuple:
        map_control_qubit_states = {}

        if isinstance(item, ResultType) and not item.target:
            target_qubits = circuit_qubits
            control_qubits = QubitSet()
            qubits = circuit_qubits
            if len(qubits) > 1:
                connections |= {qubit: "both" for qubit in qubits[1:-1]}
                connections[qubits[-1]] = "above"
                connections[qubits[0]] = "below"
            ascii_symbols = [item.ascii_symbols[0]] * len(circuit_qubits)
        elif isinstance(item, Instruction) and isinstance(item.operator, CompilerDirective):
            target_qubits = circuit_qubits
            control_qubits = QubitSet()
            qubits = circuit_qubits
            ascii_symbol = item.ascii_symbols[0]
            ascii_symbols = [ascii_symbol] * len(circuit_qubits)
            if len(circuit_qubits) > 1:
                connections = {qubit: "both" for qubit in circuit_qubits[1:-1]}
                connections[circuit_qubits[-1]] = "above"
                connections[circuit_qubits[0]] = "below"
        elif (
            isinstance(item, Instruction)
            and isinstance(item.operator, Gate)
            and item.operator.name == "GPhase"
        ):
            target_qubits = circuit_qubits
            control_qubits = QubitSet()
            qubits = circuit_qubits
            ascii_symbols = "─" * len(circuit_qubits)
        else:
            if isinstance(item.target, list):
                target_qubits = reduce(QubitSet.union, map(QubitSet, item.target), QubitSet())
            else:
                target_qubits = item.target
            control_qubits = getattr(item, "control", QubitSet())
            map_control_qubit_states = BoxDrawingCircuitDiagram._build_map_control_qubits(
                item, control_qubits
            )

            target_and_control = target_qubits.union(control_qubits)
            qubits = QubitSet(range(min(target_and_control), max(target_and_control) + 1))
            if len(qubits) > 1:
                connections |= {qubit: "both" for qubit in qubits[1:-1]}
                connections[qubits[-1]] = "above"
                connections[qubits[0]] = "below"

            ascii_symbols = item.ascii_symbols

        return (
            target_qubits,
            control_qubits,
            qubits,
            connections,
            ascii_symbols,
            map_control_qubit_states,
        )

    @staticmethod
    def _ascii_diagram_column(
        circuit_qubits: QubitSet,
        items: list[Instruction | ResultType],
        global_phase: float | None = None,
    ) -> str:
        """
        Return a column in the ASCII string diagram of the circuit for a given list of items.

        Args:
            circuit_qubits (QubitSet): qubits in circuit
            items (list[Instruction | ResultType]): list of instructions or result types
            global_phase (float | None): the integrated global phase up to this column

        Returns:
            str: an ASCII string diagram for the specified moment in time for a column.
        """
        symbols = {qubit: "─" for qubit in circuit_qubits}
        connections = {qubit: "none" for qubit in circuit_qubits}

        for item in items:
            (
                target_qubits,
                control_qubits,
                qubits,
                connections,
                ascii_symbols,
                map_control_qubit_states,
            ) = BoxDrawingCircuitDiagram._build_parameters(circuit_qubits, item, connections)
            target_and_control = target_qubits.union(control_qubits)

            for qubit in qubits:
                # Determine if the qubit is part of the item or in the middle of a
                # multi qubit item.
                if qubit in target_qubits:
                    item_qubit_index = [
                        index for index, q in enumerate(target_qubits) if q == qubit
                    ][0]
                    power_string = (
                        f"^{power}"
                        if (
                            (power := getattr(item, "power", 1)) != 1
                            # this has the limitation of not printing the power
                            # when a user has a gate genuinely named C, but
                            # is necessary to enable proper printing of custom
                            # gates with built-in control qubits
                            and ascii_symbols[item_qubit_index] != "C"
                        )
                        else ""
                    )
                    symbols[qubit] = (
                        f"{ascii_symbols[item_qubit_index]}{power_string}"
                        if power_string
                        else ascii_symbols[item_qubit_index]
                    )
                    if symbols[qubit] in ["C", "N"]:
                        if min(target_and_control) < qubit < max(target_and_control):
                            connections[qubit] = "both"
                        elif qubit == max(target_and_control):
                            connections[qubit] = "above"
                        else:
                            connections[qubit] = "below"

                elif qubit in control_qubits:
                    symbols[qubit] = "C" if map_control_qubit_states[qubit] else "N"
                    if min(target_and_control) < qubit < max(target_and_control):
                        connections[qubit] = "both"
                    elif qubit == max(target_and_control):
                        connections[qubit] = "above"
                    else:
                        connections[qubit] = "below"
                else:
                    symbols[qubit] = "┼"

        output = BoxDrawingCircuitDiagram._create_output(
            symbols, connections, circuit_qubits, global_phase
        )
        return output

    @staticmethod
    def _create_output(
        symbols: dict[Qubit, str],
        connections: dict[Qubit, str],
        qubits: QubitSet,
        global_phase: float | None,
    ) -> str:
        # We add 4 because of the edges of the box, i.e. "┤ " and " ├"
        symbols_width = max([len(symbol) for symbol in symbols.values()]) + 4
        output = ""

        if global_phase is not None:
            global_phase_str = (
                f"{global_phase:.2f}" if isinstance(global_phase, float) else str(global_phase)
            )
            symbols_width = max([symbols_width, len(global_phase_str)])
            output += "{0:{fill}{align}{width}}│\n".format(
                global_phase_str,
                fill=" ",
                align="^",
                width=symbols_width,
            )

        for qubit in qubits:
            output += BoxDrawingCircuitDiagram._draw_symbol(
                symbols[qubit], symbols_width, connections[qubit]
            )
        return output

    @staticmethod
    def _fill_symbol(symbol: str, filler: str, width: int | None = None) -> str:
        return "{0:{fill}{align}{width}}".format(
            symbol,
            fill=filler,
            align="^",
            width=width if width is not None else len(symbol) + 1,
        )

    @staticmethod
    def _draw_symbol(
        symbol: str, symbols_width: int, connection: Literal["above, below, both, none"] = "none"
    ) -> str:
        fill_symbol = BoxDrawingCircuitDiagram._fill_symbol

        top = ""
        bottom = ""
        if symbol in ["C", "N"]:
            if connection in ["above", "both"]:
                top = fill_symbol("│", " ")
            if connection in ["below", "both"]:
                bottom = fill_symbol("│", " ")
            symbol = fill_symbol("●" if symbol == "C" else "◯", "─")
        elif symbol in ["StartVerbatim", "EndVerbatim"]:
            top, symbol, bottom = BoxDrawingCircuitDiagram._build_verbatim_box(symbol, connection)
        elif symbol == "┼":
            top = fill_symbol("│", " ")
            bottom = fill_symbol("│", " ")
            symbol = fill_symbol(f"{symbol}", "─")
        elif symbol == "─":
            # We do not box when no gate is applied.
            pass
        else:
            top_edge_symbol = "┴" if connection == "above" or connection == "both" else "─"
            top = f"┌─{fill_symbol(top_edge_symbol, '─', len(symbol))}─┐"

            bottom_edge_symbol = "┬" if connection == "below" or connection == "both" else "─"
            bottom = f"└─{fill_symbol(bottom_edge_symbol, '─', len(symbol))}─┘"

            symbol = f"┤ {symbol} ├"

        output = fill_symbol(top, " ", symbols_width + 1) + "\n"
        output += fill_symbol(symbol, "─", symbols_width + 1) + "\n"
        output += fill_symbol(bottom, " ", symbols_width + 1) + "\n"
        return output

    @staticmethod
    def _build_verbatim_box(
        symbol: Literal["StartVerbatim", "EndVerbatim"],
        connection: Literal["above, below, both, none"] = "none",
    ) -> str:
        top = ""
        bottom = ""
        if connection == "below":
            bottom = "║"
        elif connection == "both":
            top = bottom = "║"
            symbol = "║"
        elif connection == "above":
            top = "║"
            symbol = "╨"
        top = BoxDrawingCircuitDiagram._fill_symbol(top, " ")
        bottom = BoxDrawingCircuitDiagram._fill_symbol(bottom, " ")
        symbol = BoxDrawingCircuitDiagram._fill_symbol(symbol, "─")

        return top, symbol, bottom

    @staticmethod
    def _build_map_control_qubits(item: Instruction, control_qubits: QubitSet) -> dict(Qubit, int):
        control_state = getattr(item, "control_state", None)
        if control_state is not None:
            map_control_qubit_states = {
                qubit: state for qubit, state in zip(control_qubits, control_state)
            }
        else:
            map_control_qubit_states = {qubit: 1 for qubit in control_qubits}

        return map_control_qubit_states
