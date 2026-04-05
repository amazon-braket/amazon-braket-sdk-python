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

from abc import abstractmethod
from functools import reduce

import braket.circuits.circuit as cir
from braket.circuits.circuit_diagram import CircuitDiagram
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.graphical_diagram_builders.graphical_diagram_utils import (
    BarrierLine,
    CircuitLayout,
    Connection,
    ControlDot,
    GateBox,
    JunctionDot,
    SwapMarker,
    _categorize_result_types,
    _compute_moment_global_phase,
    _group_items,
    _has_global_phase,
)
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType
from braket.circuits.result_type import ResultType
from braket.registers.qubit import Qubit
from braket.registers.qubit_set import QubitSet


class GraphicalCircuitDiagram(CircuitDiagram):
    """Abstract base class for graphical circuit diagrams.

    Subclasses must implement ``_render_layout`` which converts a
    :class:`CircuitLayout` into a visual output (e.g. a matplotlib Figure).

    The layout-computation pipeline mirrors
    ``TextCircuitDiagram._build()`` so that maintainers familiar with
    the text path can follow along easily.
    """

    @classmethod
    @abstractmethod
    def _render_layout(cls, layout: CircuitLayout):
        """Convert a CircuitLayout into a visual output."""

    @classmethod
    def _compute_layout(cls, circuit: cir.Circuit) -> CircuitLayout:
        """Compute a :class:`CircuitLayout` for *circuit*.

        Pipeline (parallel to ``TextCircuitDiagram._build``):
        1. Collect qubit labels and initialise metadata.
        2. Walk time-slices and convert each moment into layout primitives.
        3. Append result-type columns.
        4. Return a ``CircuitLayout`` ready for rendering.
        """
        circuit_qubits = circuit.qubits
        circuit_qubits.sort()

        qubit_labels = [f"q{int(q)}" for q in circuit_qubits]
        qubit_index = {q: i for i, q in enumerate(circuit_qubits)}

        global_phase: float | None = 0 if _has_global_phase(circuit) else None

        elements: list = []
        moment_labels: list[str] = []
        col = 0  # current column index

        # --- moment columns ---
        time_slices = circuit.moments.time_slices()
        for time, instructions in time_slices.items():
            global_phase = _compute_moment_global_phase(global_phase, instructions)

            groupings = _group_items(circuit_qubits, instructions)
            for grouping in groupings:
                cls._compute_column_elements(
                    col, circuit_qubits, qubit_index, grouping[1], global_phase, elements
                )
                moment_labels.append(str(time))
                col += 1

        # --- result-type columns ---
        additional_result_types, target_result_types = _categorize_result_types(
            circuit.result_types
        )
        if target_result_types:
            groupings = _group_items(circuit_qubits, target_result_types)
            for grouping in groupings:
                cls._compute_column_elements(
                    col, circuit_qubits, qubit_index, grouping[1], global_phase, elements
                )
                moment_labels.append("Result Types")
                col += 1

        # --- unassigned parameters ---
        unassigned = (
            [str(p) for p in sorted(circuit.parameters, key=lambda p: p.name)]
            if circuit.parameters
            else []
        )

        return CircuitLayout(
            num_qubits=len(circuit_qubits),
            num_moments=col,
            qubit_labels=qubit_labels,
            moment_labels=moment_labels,
            elements=elements,
            global_phase=global_phase,
            additional_result_types=additional_result_types,
            unassigned_parameters=unassigned,
        )

    @classmethod
    def _compute_column_elements(
        cls,
        col: int,
        circuit_qubits: QubitSet,
        qubit_index: dict[Qubit, int],
        items: list[Instruction | ResultType],
        global_phase: float | None,
        elements: list,
    ) -> None:
        """Populate *elements* with layout primitives for one column.

        This mirrors ``UnicodeCircuitDiagram._create_diagram_column`` but
        emits dataclass primitives instead of characters.
        """
        symbols: dict[Qubit, str | None] = {q: None for q in circuit_qubits}
        connections: dict[Qubit, str] = dict.fromkeys(circuit_qubits, "none")

        # Track per-item qubit ranges for emitting separate Connection elements
        item_qubit_ranges: list[tuple[int, int]] = []

        for item in items:
            (
                target_qubits,
                control_qubits,
                qubits,
                connections,
                ascii_symbols,
                map_control_qubit_states,
            ) = cls._build_parameters(circuit_qubits, item, connections)

            # Record this item's qubit span for connection drawing
            if len(qubits) > 1:
                item_rows = [qubit_index[q] for q in qubits if q in qubit_index]
                item_qubit_ranges.append((min(item_rows), max(item_rows)))

            for qubit in qubits:
                if qubit in target_qubits:
                    item_qubit_index = [
                        index for index, q in enumerate(target_qubits) if q == qubit
                    ][0]
                    power_string = (
                        f"^{power}"
                        if (
                            (power := getattr(item, "power", 1)) != 1
                            and ascii_symbols[item_qubit_index] != "C"
                        )
                        else ""
                    )
                    symbol = (
                        f"{ascii_symbols[item_qubit_index]}{power_string}"
                        if power_string
                        else ascii_symbols[item_qubit_index]
                    )
                    symbols[qubit] = symbol
                elif qubit in control_qubits:
                    symbols[qubit] = "C" if map_control_qubit_states[qubit] else "N"
                else:
                    symbols[qubit] = "JUNCTION"

        # Convert symbols + connections into layout primitives
        for qubit in circuit_qubits:
            row = qubit_index[qubit]
            symbol = symbols[qubit]
            if symbol is None:
                continue  # qubit wire only, no element at this column

            if symbol in {"C", "N"}:
                elements.append(ControlDot(col=col, row=row, filled=(symbol == "C")))
            elif symbol == "SWAP":
                elements.append(SwapMarker(col=col, row=row))
            elif symbol == "JUNCTION":
                elements.append(JunctionDot(col=col, row=row))
            elif symbol == "||":
                # Barrier symbol — we handle barrier lines separately below
                pass
            else:
                elements.append(GateBox(col=col, row=row, label=symbol))

        # Emit connections — one per item so independent gates don't bridge
        for row_start, row_end in item_qubit_ranges:
            elements.append(Connection(col=col, row_start=row_start, row_end=row_end))

        # Emit barrier lines
        for item in items:
            if (
                isinstance(item, Instruction)
                and isinstance(item.operator, CompilerDirective)
                and item.operator.name == "Barrier"
            ):
                if item.target:
                    rows = sorted(qubit_index[q] for q in item.target)
                else:
                    rows = sorted(qubit_index[q] for q in circuit_qubits)
                elements.append(BarrierLine(col=col, row_start=rows[0], row_end=rows[-1]))

    @classmethod
    def _build_parameters(
        cls,
        circuit_qubits: QubitSet,
        item: ResultType | Instruction,
        connections: dict[Qubit, str],
    ) -> tuple:
        map_control_qubit_states: dict = {}

        if isinstance(item, ResultType) and not item.target:
            target_qubits = circuit_qubits
            control_qubits = QubitSet()
            qubits = circuit_qubits
            ascii_symbols = [item.ascii_symbols[0]] * len(qubits)
            cls._update_connections(qubits, connections)
        elif isinstance(item, Instruction) and isinstance(item.operator, CompilerDirective):
            if item.operator.name == "Barrier":
                if not item.target:
                    target_qubits = circuit_qubits
                    qubits = circuit_qubits
                    ascii_symbols = [item.ascii_symbols[0]] * len(circuit_qubits)
                    cls._update_connections(circuit_qubits, connections)
                else:
                    target_qubits = item.target
                    qubits = target_qubits
                    ascii_symbols = [item.ascii_symbols[0]] * len(target_qubits)
                control_qubits = QubitSet()
            else:
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
            # GPhase does not draw on any qubit wire — use None as sentinel
            ascii_symbols = [None] * len(circuit_qubits)
        else:
            if isinstance(item.target, list):
                target_qubits = reduce(QubitSet.union, map(QubitSet, item.target), QubitSet())
            else:
                target_qubits = item.target
            control_qubits = getattr(item, "control", QubitSet())
            control_state = getattr(item, "control_state", "1" * len(control_qubits))
            map_control_qubit_states = dict(zip(control_qubits, control_state, strict=True))

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
