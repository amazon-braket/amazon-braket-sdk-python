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
from typing import Literal

import braket.circuits.circuit as cir
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.result_type import ResultType
from braket.circuits.text_diagram_builders.text_circuit_diagram import TextCircuitDiagram
from braket.registers.qubit import Qubit
from braket.registers.qubit_set import QubitSet


class UnicodeCircuitDiagram(TextCircuitDiagram):
    """Builds string circuit diagrams using box-drawing characters."""

    @staticmethod
    def build_diagram(circuit: cir.Circuit) -> str:
        """Build a text circuit diagram.

        Args:
            circuit (Circuit): Circuit for which to build a diagram.

        Returns:
            str: string circuit diagram.
        """
        return UnicodeCircuitDiagram._build(circuit)

    @classmethod
    def _vertical_delimiter(cls) -> str:
        """Character that connects qubits of multi-qubit gates."""
        return "│"

    @classmethod
    def _qubit_line_character(cls) -> str:
        """Character used for the qubit line."""
        return "─"

    @classmethod
    def _box_pad(cls) -> int:
        """number of blank space characters around the gate name."""
        return 4

    @classmethod
    def _qubit_line_spacing_above(cls) -> int:
        """number of empty lines above the qubit line."""
        return 1

    @classmethod
    def _qubit_line_spacing_below(cls) -> int:
        """number of empty lines below the qubit line."""
        return 1

    @classmethod
    def _duplicate_time_at_bottom(cls, lines: list) -> None:
        # Do not add a line after the circuit
        # It is safe to do because the last line is empty: _qubit_line_spacing["after"] = 1
        lines[-1] = lines[0]

    @classmethod
    def _create_diagram_column(
        cls,
        circuit_qubits: QubitSet,
        items: list[Instruction | ResultType],
        global_phase: float | None = None,
    ) -> str:
        """Return a column in the string diagram of the circuit for a given list of items.

        Args:
            circuit_qubits (QubitSet): qubits in circuit
            items (list[Instruction | ResultType]): list of instructions or result types
            global_phase (float | None): the integrated global phase up to this column

        Returns:
            str: a string diagram for the specified moment in time for a column.
        """
        symbols = {qubit: cls._qubit_line_character() for qubit in circuit_qubits}
        connections = dict.fromkeys(circuit_qubits, "none")

        for item in items:
            (
                target_qubits,
                control_qubits,
                qubits,
                connections,
                ascii_symbols,
                map_control_qubit_states,
            ) = cls._build_parameters(circuit_qubits, item, connections)

            for qubit in qubits:
                # Determine if the qubit is part of the item or in the middle of a
                # multi qubit item.
                if qubit in target_qubits:
                    item_qubit_index = [  # noqa: RUF015
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

                elif qubit in control_qubits:
                    symbols[qubit] = "C" if map_control_qubit_states[qubit] else "N"
                else:
                    symbols[qubit] = "┼"

        return cls._create_output(symbols, connections, circuit_qubits, global_phase)

    @classmethod
    def _build_parameters(
        cls, circuit_qubits: QubitSet, item: ResultType | Instruction, connections: dict[Qubit, str]
    ) -> tuple:
        map_control_qubit_states = {}

        if (isinstance(item, ResultType) and not item.target) or (
            isinstance(item, Instruction) and isinstance(item.operator, CompilerDirective)
        ):
            target_qubits = circuit_qubits
            control_qubits = QubitSet()
            qubits = circuit_qubits
            ascii_symbols = [item.ascii_symbols[0]] * len(qubits)
            cls._update_connections(qubits, connections)
        elif (
            isinstance(item, Instruction)
            and isinstance(item.operator, Gate)
            and item.operator.name == "GPhase"
        ):
            target_qubits = circuit_qubits
            control_qubits = QubitSet()
            qubits = circuit_qubits
            ascii_symbols = cls._qubit_line_character() * len(circuit_qubits)
        else:
            if isinstance(item.target, list):
                target_qubits = reduce(QubitSet.union, map(QubitSet, item.target), QubitSet())
            else:
                target_qubits = item.target
            control_qubits = getattr(item, "control", QubitSet())
            control_state = getattr(item, "control_state", "1" * len(control_qubits))
            map_control_qubit_states = dict(zip(control_qubits, control_state))

            target_and_control = target_qubits.union(control_qubits)
            qubits = QubitSet(range(min(target_and_control), max(target_and_control) + 1))
            ascii_symbols = item.ascii_symbols
            cls._update_connections(qubits, connections)

        return (
            target_qubits,
            control_qubits,
            qubits,
            connections,
            ascii_symbols,
            map_control_qubit_states,
        )

    @staticmethod
    def _update_connections(qubits: QubitSet, connections: dict[Qubit, str]) -> None:
        if len(qubits) > 1:
            connections |= dict.fromkeys(qubits[1:-1], "both")
            connections[qubits[-1]] = "above"
            connections[qubits[0]] = "below"

    # Ignore flake8 issue caused by Literal["above", "below", "both", "none"]
    # flake8: noqa: BCS005
    @classmethod
    def _draw_symbol(
        cls,
        symbol: str,
        symbols_width: int,
        connection: Literal["above", "below", "both", "none"],
    ) -> str:
        """Create a string representing the symbol inside a box.

        Args:
            symbol (str): the gate name
            symbols_width (int): size of the expected output. The output will be filled with
                cls._qubit_line_character() if needed.
            connection (Literal["above", "below", "both", "none"]): specifies if a connection
                will be drawn above and/or below the box.

        Returns:
            str: a string representing the symbol.
        """
        top = ""
        bottom = ""
        if symbol in {"C", "N", "SWAP"}:
            if connection in {"above", "both"}:
                top = _fill_symbol(cls._vertical_delimiter(), " ")
            if connection in {"below", "both"}:
                bottom = _fill_symbol(cls._vertical_delimiter(), " ")
            new_symbol = {"C": "●", "N": "◯", "SWAP": "x"}
            # replace SWAP by x
            # the size of the moment remains as if there was a box with 4 characters inside
            symbol = _fill_symbol(new_symbol[symbol], cls._qubit_line_character())
        elif symbol in {"StartVerbatim", "EndVerbatim"}:
            top, symbol, bottom = cls._build_verbatim_box(symbol, connection)
        elif symbol == "┼":
            top = bottom = _fill_symbol(cls._vertical_delimiter(), " ")
            symbol = _fill_symbol(f"{symbol}", cls._qubit_line_character())
        elif symbol != cls._qubit_line_character():
            top, symbol, bottom = cls._build_box(symbol, connection)

        output = f"{_fill_symbol(top, ' ', symbols_width)} \n"
        output += (
            f"{_fill_symbol(symbol, cls._qubit_line_character(), symbols_width)}"
            f"{cls._qubit_line_character()}\n"
        )
        output += f"{_fill_symbol(bottom, ' ', symbols_width)} \n"
        return output

    @staticmethod
    def _build_box(
        symbol: str, connection: Literal["above", "below", "both", "none"]
    ) -> tuple[str, str, str]:
        top_edge_symbol = "┴" if connection in {"above", "both"} else "─"
        top = f"┌─{_fill_symbol(top_edge_symbol, '─', len(symbol))}─┐"

        bottom_edge_symbol = "┬" if connection in {"below", "both"} else "─"
        bottom = f"└─{_fill_symbol(bottom_edge_symbol, '─', len(symbol))}─┘"

        symbol = f"┤ {symbol} ├"
        return top, symbol, bottom

    @classmethod
    def _build_verbatim_box(
        cls,
        symbol: Literal["StartVerbatim", "EndVerbatim"],
        connection: Literal["above", "below", "both", "none"],
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
        top = _fill_symbol(top, " ")
        symbol = _fill_symbol(symbol, cls._qubit_line_character())
        bottom = _fill_symbol(bottom, " ")

        return top, symbol, bottom


def _fill_symbol(symbol: str, filler: str, width: int | None = None) -> str:
    return "{0:{fill}{align}{width}}".format(
        symbol,
        fill=filler,
        align="^",
        width=width if width is not None else len(symbol),
    )
