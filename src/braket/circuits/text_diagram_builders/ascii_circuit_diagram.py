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
from braket.circuits.result_type import ResultType
from braket.circuits.text_diagram_builders.text_circuit_diagram import TextCircuitDiagram
from braket.registers.qubit_set import QubitSet


class AsciiCircuitDiagram(TextCircuitDiagram):
    """Builds ASCII string circuit diagrams."""

    _vdelim = "|"  # Character that connects qubits of multi-qubit gates
    _qubit_line_char = "-"  # Character used for the qubit line
    _box_pad = 0  # number of blank space characters around the gate name
    _qubit_line_spacing = {"before": 1, "after": 0}  # number of empty lines around the qubit line

    @staticmethod
    def build_diagram(circuit: cir.Circuit) -> str:
        """
        Build a text circuit diagram.

        Args:
            circuit (Circuit): Circuit for which to build a diagram.

        Returns:
            str: string circuit diagram.
        """
        return AsciiCircuitDiagram._build(circuit)

    @classmethod
    def _vertical_delimiter(cls) -> str:
        return cls._vdelim

    @classmethod
    def _qubit_line_character(cls) -> str:
        return cls._qubit_line_char

    @classmethod
    def _box_padding(cls) -> int:
        return cls._box_pad

    @classmethod
    def _qubit_line_spacing_before(cls) -> int:
        return cls._qubit_line_spacing["before"]

    @classmethod
    def _qubit_line_spacing_after(cls) -> int:
        return cls._qubit_line_spacing["after"]

    @classmethod
    def _duplicate_time_at_bottom(cls, lines: str) -> None:
        # duplicate times after an empty line
        lines.append(lines[0])

    @classmethod
    def _create_diagram_column(
        cls,
        circuit_qubits: QubitSet,
        items: list[Union[Instruction, ResultType]],
        global_phase: float | None = None,
    ) -> str:
        """Return a column in the ASCII string diagram of the circuit for a given list of items.

        Args:
            circuit_qubits (QubitSet): qubits in circuit
            items (list[Union[Instruction, ResultType]]): list of instructions or result types
            global_phase (float | None): the integrated global phase up to this column

        Returns:
            str: an ASCII string diagram for the specified moment in time for a column.
        """
        symbols = {qubit: cls._qubit_line_char for qubit in circuit_qubits}
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
                ascii_symbols = [ascii_symbol, *after]
            elif (
                isinstance(item, Instruction)
                and isinstance(item.operator, Gate)
                and item.operator.name == "GPhase"
            ):
                target_qubits = circuit_qubits
                control_qubits = QubitSet()
                target_and_control = QubitSet()
                qubits = circuit_qubits
                ascii_symbols = cls._qubit_line_char * len(circuit_qubits)
            else:
                if isinstance(item.target, list):
                    target_qubits = reduce(QubitSet.union, map(QubitSet, item.target), QubitSet())
                else:
                    target_qubits = item.target
                control_qubits = getattr(item, "control", QubitSet())
                control_state = getattr(item, "control_state", "1" * len(control_qubits))
                map_control_qubit_states = {
                    qubit: state for qubit, state in zip(control_qubits, control_state)
                }

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
                if target_and_control and qubit != min(target_and_control):
                    margins[qubit] = "|"

        output = cls._create_output(symbols, margins, circuit_qubits, global_phase)
        return output

    @classmethod
    def _draw_symbol(cls, symbol: str, symbols_width: int, connection: str) -> str:
        """
        Create a string representing the symbol.

        Args:
            symbol (str): the gate name
            symbols_width (int): size of the expected output. The ouput will be filled with
                cls._qubit_line_char if needed.
            connection (str): character indicating if the gate also involve a qubit with a lower
                index.

        Returns:
            str: a string representing the symbol.
        """
        output = "{0:{width}}\n".format(connection, width=symbols_width + 1)
        output += "{0:{fill}{align}{width}}\n".format(
            symbol, fill=cls._qubit_line_char, align="<", width=symbols_width + 1
        )
        return output