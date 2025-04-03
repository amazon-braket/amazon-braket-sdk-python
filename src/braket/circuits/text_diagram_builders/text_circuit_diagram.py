from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

import braket.circuits.circuit as cir
from braket.circuits.circuit_diagram import CircuitDiagram
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType
from braket.circuits.result_type import ResultType
from braket.circuits.text_diagram_builders.text_circuit_diagram_utils import (
    _add_footers,
    _categorize_result_types,
    _compute_moment_global_phase,
    _group_items,
    _prepare_qubit_identifier_column,
    _unite_strings,
)
from braket.registers.qubit import Qubit
from braket.registers.qubit_set import QubitSet


class TextCircuitDiagram(CircuitDiagram, ABC):
    """Abstract base class for text circuit diagrams."""

    @classmethod
    @abstractmethod
    def _vertical_delimiter(cls) -> str:
        """Character that connects qubits of multi-qubit gates."""

    @classmethod
    @abstractmethod
    def _qubit_line_character(cls) -> str:
        """Character used for the qubit line."""

    @classmethod
    @abstractmethod
    def _box_pad(cls) -> int:
        """number of blank space characters around the gate name."""

    @classmethod
    @abstractmethod
    def _qubit_line_spacing_above(cls) -> int:
        """number of empty lines above the qubit line."""

    @classmethod
    @abstractmethod
    def _qubit_line_spacing_below(cls) -> int:
        """number of empty lines below the qubit line."""

    @classmethod
    @abstractmethod
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

    # Ignore flake8 issue caused by Literal["above", "below", "both", "none"]
    # flake8: noqa: BCS005
    @classmethod
    @abstractmethod
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

    @classmethod
    def _build(cls, circuit: cir.Circuit) -> str:
        """Build a text circuit diagram.

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
            circuit (Circuit): Circuit for which to build a diagram.

        Returns:
            str: string circuit diagram.
        """
        if not circuit.instructions:
            return ""

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            return f"Global phase: {circuit.global_phase}"

        circuit_qubits = circuit.qubits
        circuit_qubits.sort()

        y_axis_str, global_phase = _prepare_qubit_identifier_column(
            circuit,
            circuit_qubits,
            cls._vertical_delimiter(),
            cls._qubit_line_character(),
            cls._qubit_line_spacing_above(),
            cls._qubit_line_spacing_below(),
        )

        column_strs = []

        global_phase, additional_result_types = cls._build_columns(
            circuit, circuit_qubits, global_phase, column_strs
        )

        # Unite strings
        lines = _unite_strings(y_axis_str, column_strs)
        cls._duplicate_time_at_bottom(lines)

        return _add_footers(lines, circuit, global_phase, additional_result_types)

    @classmethod
    def _build_columns(
        cls,
        circuit: cir.Circuit,
        circuit_qubits: QubitSet,
        global_phase: float | None,
        column_strs: list,
    ) -> tuple[float | None, list[str]]:
        time_slices = circuit.moments.time_slices()

        # Moment columns
        for time, instructions in time_slices.items():
            global_phase = _compute_moment_global_phase(global_phase, instructions)
            moment_str = cls._create_diagram_column_set(
                str(time), circuit_qubits, instructions, global_phase
            )
            column_strs.append(moment_str)

        # Result type columns
        additional_result_types, target_result_types = _categorize_result_types(
            circuit.result_types
        )
        if target_result_types:
            column_strs.append(
                cls._create_diagram_column_set(
                    "Result Types", circuit_qubits, target_result_types, global_phase
                )
            )
        return global_phase, additional_result_types

    @classmethod
    def _create_diagram_column_set(
        cls,
        col_title: str,
        circuit_qubits: QubitSet,
        items: list[Instruction | ResultType],
        global_phase: float | None,
    ) -> str:
        """Return a set of columns in the string diagram of the circuit for a list of items.

        Args:
            col_title (str): title of column set
            circuit_qubits (QubitSet): qubits in circuit
            items (list[Union[Instruction, ResultType]]): list of instructions or result types
            global_phase (float | None): the integrated global phase up to this set

        Returns:
            str: A string diagram for the column set.
        """

        # Group items to separate out overlapping multi-qubit items
        groupings = _group_items(circuit_qubits, items)

        column_strs = [
            cls._create_diagram_column(circuit_qubits, grouping[1], global_phase)
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
                if lines[i].endswith(cls._qubit_line_character()):
                    lines[i] += cls._qubit_line_character() * diff
                else:
                    lines[i] += " "

        first_line = "{:^{width}}{vdelim}\n".format(
            col_title, width=len(lines[0]) - 1, vdelim=cls._vertical_delimiter()
        )

        return first_line + "\n".join(lines)

    @classmethod
    def _create_output(
        cls,
        symbols: dict[Qubit, str],
        margins: dict[Qubit, str],
        qubits: QubitSet,
        global_phase: float | None,
    ) -> str:
        """Creates the output for a single column:
            a. If there was one or more gphase gate, create a first line with the total global
            phase shift ending with the _vertical_delimiter() class attribute, e.g. 0.14|
            b. for each qubit, append the text representation produces by cls._draw_symbol

        Args:
            symbols (dict[Qubit, str]): dictionary of the gate name for each qubit
            margins (dict[Qubit, str]): map of the qubit interconnections. Specific to the
                `_draw_symbol` classmethod.
            qubits (QubitSet): set of the circuit qubits
            global_phase (float | None): total global phase shift added during the moment

        Returns:
            str: a string representing a diagram column.
        """
        symbols_width = max(len(symbol) for symbol in symbols.values()) + cls._box_pad()
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
                vdelim=cls._vertical_delimiter(),
            )

        for qubit in qubits:
            output += cls._draw_symbol(symbols[qubit], symbols_width, margins[qubit])
        return output
