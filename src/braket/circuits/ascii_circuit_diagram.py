# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from typing import List, Tuple

from braket.circuits.circuit_diagram import CircuitDiagram
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.qubit_set import QubitSet


class AsciiCircuitDiagram(CircuitDiagram):
    """Builds ASCII string circuit diagrams."""

    @staticmethod
    def build_diagram(circuit) -> str:
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

        # Moment columns
        moments_strs = []
        for time, instructions in time_slices.items():
            moment_str = AsciiCircuitDiagram._ascii_diagram_moment(
                time, circuit_qubits, instructions
            )
            moments_strs.append(moment_str)

        # Unite strings
        lines = y_axis_str.split("\n")
        for moment_str in moments_strs:
            for i, moment_line in enumerate(moment_str.split("\n")):
                lines[i] += moment_line

        # Time on top and bottom
        lines.append(lines[0])

        return "\n".join(lines)

    @staticmethod
    def _ascii_moment_group_instructions(
        instructions: List[Instruction],
    ) -> List[Tuple[QubitSet, List[Instruction]]]:
        """
        Group instructions in a moment for ASCII diagram

        Args:
            instructions (List[Instruction]): list of instructions

        Returns:
            List[(QubitSet, List[Instruction])]: list of grouped instructions
        """
        groupings = []
        for instr in instructions:
            # Can only print Gate operators at the moment
            if not isinstance(instr.operator, Gate):
                continue

            qubit_range = QubitSet(range(min(instr.target), max(instr.target) + 1))

            found_grouping = False
            for group in groupings:
                qubits_added = group[0]
                instr_group = group[1]
                # Take into account overlapping multi-qubit gates
                if not qubits_added.intersection(set(qubit_range)):
                    instr_group.append(instr)
                    qubits_added.update(qubit_range)
                    found_grouping = True
                    break

            if not found_grouping:
                groupings.append((qubit_range, [instr]))

        return groupings

    @staticmethod
    def _ascii_diagram_moment(
        time: int, circuit_qubits: QubitSet, instructions: List[Instruction]
    ) -> str:
        """
        Return an ASCII string diagram of the circuit at a particular moment in time.

        Args:
            time (int): time of moment
            circuit_qubits (QubitSet): qubits in circuit
            instructions (List[Instruction]): list of instructions

        Returns:
            str: An ASCII string diagram for the specified moment in time.
        """

        # Group instructions to separate out overlapping multi-qubit gates
        groupings = AsciiCircuitDiagram._ascii_moment_group_instructions(instructions)

        column_strs = [
            AsciiCircuitDiagram._ascii_diagram_moment_column(circuit_qubits, grouping[1])
            for grouping in groupings
        ]

        # Unite column strings
        lines = column_strs[0].split("\n")
        for column_str in column_strs[1:]:
            for i, moment_line in enumerate(column_str.split("\n")):
                lines[i] += moment_line

        # Adjust for time width
        time_width = len(str(time))
        symbols_width = len(lines[0]) - 1
        if symbols_width < time_width:
            diff = time_width - symbols_width
            for i in range(len(lines) - 1):
                if lines[i].endswith("-"):
                    lines[i] += "-" * diff
                else:
                    lines[i] += " "

        first_line = "{:^{width}}|\n".format(str(time), width=len(lines[0]) - 1)

        return first_line + "\n".join(lines)

    @staticmethod
    def _ascii_diagram_moment_column(
        circuit_qubits: QubitSet, instructions: List[Instruction]
    ) -> str:
        """
        Return an ASCII string diagram of the circuit at a particular moment in time for a column.

        Args:
            circuit_qubits (QubitSet): qubits in circuit
            instructions (List[Instruction]): list of instructions

        Returns:
            str: An ASCII string diagram for the specified moment in time for a column.
        """
        symbols = {qubit: "-" for qubit in circuit_qubits}
        margins = {qubit: " " for qubit in circuit_qubits}

        for instr in instructions:

            qubits = circuit_qubits.intersection(
                set(range(min(instr.target), max(instr.target) + 1))
            )
            for qubit in qubits:
                # Determine if the qubit is part of the instruction or in the middle of a
                # multi qubit gate.
                if qubit in instr.target:
                    instr_qubit_index = [
                        index for index, q in enumerate(instr.target) if q == qubit
                    ][0]
                    symbols[qubit] = instr.operator.ascii_symbols[instr_qubit_index]
                else:
                    symbols[qubit] = "|"

                # Set the margin to be a connector if not on the first qubit
                if qubit != min(instr.target):
                    margins[qubit] = "|"

        symbols_width = max([len(symbol) for symbol in symbols.values()])

        output = ""
        for qubit in circuit_qubits:
            output += "{0:{width}}\n".format(margins[qubit], width=symbols_width + 1)
            output += "{0:{fill}{align}{width}}\n".format(
                symbols[qubit], fill="-", align="<", width=symbols_width + 1
            )
        return output
