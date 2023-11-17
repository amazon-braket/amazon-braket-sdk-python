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
from braket.circuits.circuit_diagram import CircuitDiagram
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.noise import Noise
from braket.circuits.result_type import ResultType
from braket.registers.qubit import Qubit
from braket.registers.qubit_set import QubitSet


class AsciiCircuitDiagram(CircuitDiagram):
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

        circuit_qubits = circuit.qubits
        circuit_qubits.sort()

        # Y Axis Column
        y_axis_width = len(str(int(max(circuit_qubits))))
        y_axis_str = "{0:{width}} : |\n".format("T", width=y_axis_width + 1)
        for qubit in circuit_qubits:
            y_axis_str += "{0:{width}}\n".format(" ", width=y_axis_width + 5)
            y_axis_str += "q{0:{width}} : -\n".format(str(int(qubit)), width=y_axis_width)

        time_slices = circuit.moments.time_slices()
        column_strs = []

        # Moment columns
        for time, instructions in time_slices.items():
            moment_str = AsciiCircuitDiagram._ascii_diagram_column_set(
                str(time), circuit_qubits, instructions
            )
            column_strs.append(moment_str)

        # Result type columns
        additional_result_types, target_result_types = AsciiCircuitDiagram._categorize_result_types(
            circuit.result_types
        )
        if target_result_types:
            column_strs.append(
                AsciiCircuitDiagram._ascii_diagram_column_set(
                    "Result Types", circuit_qubits, target_result_types
                )
            )

        # Unite strings
        lines = y_axis_str.split("\n")
        for col_str in column_strs:
            for i, line_in_col in enumerate(col_str.split("\n")):
                lines[i] += line_in_col

        # Time on top and bottom
        lines.append(lines[0])

        if circuit.global_phase:
            lines.append(f"\nGlobal phase: {circuit.global_phase}")

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
            if isinstance(item, Instruction) and (
                not isinstance(item.operator, (Gate, Noise, CompilerDirective))
            ):
                continue

            if (isinstance(item, ResultType) and not item.target) or (
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
        col_title: str, circuit_qubits: QubitSet, items: list[Union[Instruction, ResultType]]
    ) -> str:
        """
        Return a set of columns in the ASCII string diagram of the circuit for a list of items.

        Args:
            col_title (str): title of column set
            circuit_qubits (QubitSet): qubits in circuit
            items (list[Union[Instruction, ResultType]]): list of instructions or result types

        Returns:
            str: An ASCII string diagram for the column set.
        """

        # Group items to separate out overlapping multi-qubit items
        groupings = AsciiCircuitDiagram._ascii_group_items(circuit_qubits, items)

        column_strs = [
            AsciiCircuitDiagram._ascii_diagram_column(circuit_qubits, grouping[1])
            for grouping in groupings
        ]

        # Unite column strings
        lines = column_strs[0].split("\n")
        for column_str in column_strs[1:]:
            for i, moment_line in enumerate(column_str.split("\n")):
                lines[i] += moment_line

        # Adjust for column title width
        col_title_width = len(col_title)
        symbols_width = len(lines[0]) - 1
        if symbols_width < col_title_width:
            diff = col_title_width - symbols_width
            for i in range(len(lines) - 1):
                if lines[i].endswith("-"):
                    lines[i] += "-" * diff
                else:
                    lines[i] += " "

        first_line = "{:^{width}}|\n".format(col_title, width=len(lines[0]) - 1)

        return first_line + "\n".join(lines)

    @staticmethod
    def _ascii_diagram_column(
        circuit_qubits: QubitSet, items: list[Union[Instruction, ResultType]]
    ) -> str:
        """
        Return a column in the ASCII string diagram of the circuit for a given list of items.

        Args:
            circuit_qubits (QubitSet): qubits in circuit
            items (list[Union[Instruction, ResultType]]): list of instructions or result types

        Returns:
            str: An ASCII string diagram for the specified moment in time for a column.
        """
        symbols = {qubit: "-" for qubit in circuit_qubits}
        margins = {qubit: " " for qubit in circuit_qubits}

        for item in items:
            if isinstance(item, ResultType) and not item.target:
                target_qubits = circuit_qubits
                control_qubits = QubitSet()
                target_and_control = target_qubits.union(control_qubits)
                qubits = circuit_qubits
                ascii_symbols = [item.ascii_symbols[0]] * len(circuit_qubits)
            elif isinstance(item, Instruction) and isinstance(item.operator, CompilerDirective):
                target_qubits = circuit_qubits
                control_qubits = QubitSet()
                target_and_control = target_qubits.union(control_qubits)
                qubits = circuit_qubits
                ascii_symbol = item.ascii_symbols[0]
                marker = "*" * len(ascii_symbol)
                num_after = len(circuit_qubits) - 1
                after = ["|"] * (num_after - 1) + ([marker] if num_after else [])
                ascii_symbols = [ascii_symbol] + after
            else:
                if isinstance(item.target, list):
                    target_qubits = reduce(QubitSet.union, map(QubitSet, item.target), QubitSet())
                else:
                    target_qubits = item.target
                control_qubits = getattr(item, "control", QubitSet())
                map_control_qubit_states = AsciiCircuitDiagram._build_map_control_qubits(
                    item, control_qubits
                )

                target_and_control = target_qubits.union(control_qubits)
                qubits = QubitSet(range(min(target_and_control), max(target_and_control) + 1))

                ascii_symbols = item.ascii_symbols

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
                        f"({ascii_symbols[item_qubit_index]}{power_string})"
                        if power_string
                        else ascii_symbols[item_qubit_index]
                    )
                elif qubit in control_qubits:
                    symbols[qubit] = "C" if map_control_qubit_states[qubit] else "N"
                else:
                    symbols[qubit] = "|"

                # Set the margin to be a connector if not on the first qubit
                if qubit != min(target_and_control):
                    margins[qubit] = "|"

        symbols_width = max([len(symbol) for symbol in symbols.values()])

        output = ""
        for qubit in circuit_qubits:
            output += "{0:{width}}\n".format(margins[qubit], width=symbols_width + 1)
            output += "{0:{fill}{align}{width}}\n".format(
                symbols[qubit], fill="-", align="<", width=symbols_width + 1
            )
        return output

    @staticmethod
    def _build_map_control_qubits(item: Instruction, control_qubits: QubitSet) -> dict(Qubit, int):
        control_state = getattr(item, "control_state", None)
        if control_state is not None:
            map_control_qubit_states = {
                qubit: state for qubit, state in zip(control_qubits, control_state.as_tuple)
            }
        else:
            map_control_qubit_states = {qubit: 1 for qubit in control_qubits}

        return map_control_qubit_states
