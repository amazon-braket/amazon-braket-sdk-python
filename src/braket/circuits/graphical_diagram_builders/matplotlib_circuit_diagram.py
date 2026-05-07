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

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

import braket.circuits.circuit as cir
from braket.circuits.graphical_diagram_builders.graphical_circuit_diagram import (
    GraphicalCircuitDiagram,
)
from braket.circuits.graphical_diagram_builders.graphical_diagram_utils import (
    BarrierLine,
    CircuitLayout,
    Connection,
    ControlDot,
    GateBox,
    JunctionDot,
    SwapMarker,
)
from braket.circuits.moments import MomentType


class MatplotlibCircuitDiagram(GraphicalCircuitDiagram):
    """Renders circuit diagrams as matplotlib Figures.

    The visual style mirrors the Unicode text diagram:
    - Gates are drawn as labelled boxes
    - Control qubits are filled/open circles
    - Multi-qubit connections are vertical lines
    - SWAP gates are drawn as ``x`` markers
    - Barriers are dashed vertical lines
    """

    # Layout parameters
    COL_WIDTH = 1.4  # default/minimum column width, used as a lower bound
    COL_GAP = 0.2  # horizontal gap between adjacent column boxes
    ROW_HEIGHT = 0.8
    WIRE_EXTEND = 0.5  # extra wire length before first / after last column

    # Gate box style
    GATE_BOX_HEIGHT = 0.5
    GATE_BOX_MIN_WIDTH = 0.6
    GATE_BOX_PADDING = 0.3  # horizontal padding inside the box around the label
    GATE_FONT_SIZE = 10
    GATE_FILL_COLOR = "#D4E6F1"
    GATE_EDGE_COLOR = "black"
    GATE_TEXT_COLOR = "black"

    # Wire style
    WIRE_COLOR = "#333333"
    WIRE_LW = 1.0

    # Control dot style
    CONTROL_DOT_RADIUS = 0.08
    CONTROL_DOT_COLOR = "black"

    # Connection / barrier style
    CONNECTION_LW = 1.5
    CONNECTION_COLOR = "black"
    BARRIER_COLOR = "#888888"
    BARRIER_LW = 1.5

    # Label style
    QUBIT_LABEL_FONT_SIZE = 11
    MOMENT_LABEL_FONT_SIZE = 9
    FOOTER_FONT_SIZE = 9

    # Marker sizes
    SWAP_MARKER_SIZE = 8
    JUNCTION_DOT_SIZE = 4

    @staticmethod
    def build_diagram(circuit: cir.Circuit) -> Figure:
        """Build a matplotlib Figure for *circuit*.

        Args:
            circuit: The circuit to visualise.

        Returns:
            A ``matplotlib.figure.Figure``.
        """
        if not circuit.instructions:
            fig, ax = plt.subplots(figsize=(2, 1))
            ax.text(0.5, 0.5, "(empty circuit)", ha="center", va="center", fontsize=12)
            ax.axis("off")
            return fig

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            fig, ax = plt.subplots(figsize=(3, 1))
            ax.text(
                0.5,
                0.5,
                f"Global phase: {circuit.global_phase}",
                ha="center",
                va="center",
                fontsize=12,
            )
            ax.axis("off")
            return fig

        layout = MatplotlibCircuitDiagram._compute_layout(circuit)
        return MatplotlibCircuitDiagram._render_layout(layout)

    @classmethod
    def _gate_box_width(cls, label: str) -> float:
        """Return the width of a gate box rendered with *label*."""
        char_width = cls.GATE_FONT_SIZE * 0.012
        text_width = len(label) * char_width
        return max(cls.GATE_BOX_MIN_WIDTH, text_width + cls.GATE_BOX_PADDING)

    @classmethod
    def _compute_column_x(cls, layout: CircuitLayout) -> tuple[list[float], list[float]]:
        """Compute the x center and width of each column based on box sizes.

        Columns are sized to fit the widest gate box they contain, plus a
        fixed gap. Columns with no boxes fall back to the default width.

        Returns:
            Tuple of ``(centers, widths)`` lists of length ``num_moments``.
        """
        n_cols = max(layout.num_moments, 1)
        widths = [cls.COL_WIDTH] * n_cols
        for elem in layout.elements:
            if isinstance(elem, GateBox):
                widths[elem.col] = max(
                    widths[elem.col], cls._gate_box_width(elem.label) + cls.COL_GAP
                )
        centers: list[float] = []
        cursor = 0.0
        for w in widths:
            centers.append(cursor + w / 2)
            cursor += w
        return centers, widths

    @classmethod
    def _render_layout(cls, layout: CircuitLayout) -> Figure:
        n_rows = max(layout.num_qubits, 1)

        col_x, col_w = cls._compute_column_x(layout)
        total_width = sum(col_w)
        right_edge = total_width

        fig_width = max(4, cls.WIRE_EXTEND * 2 + total_width + 1.5)
        fig_height = max(2, n_rows * cls.ROW_HEIGHT + 1.5)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        left_wire = col_x[0] - col_w[0] / 2 - cls.WIRE_EXTEND
        right_wire = right_edge + cls.WIRE_EXTEND

        cls._draw_qubit_wires(ax, layout, left_wire, right_wire)

        label_y_top = cls.ROW_HEIGHT * 0.8
        label_y_bottom = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.8
        cls._draw_moment_labels(ax, layout, col_x, label_y_top, label_y_bottom)

        cls._draw_elements(ax, layout, col_x)

        footer_lines = cls._build_footer_lines(layout)
        if footer_lines:
            cls._draw_footer(ax, footer_lines, left_wire, label_y_bottom)

        cls._configure_axes(ax, left_wire, right_wire, label_y_top, label_y_bottom, footer_lines)
        fig.tight_layout()
        return fig

    @classmethod
    def _draw_qubit_wires(
        cls, ax: Axes, layout: CircuitLayout, left_wire: float, right_wire: float
    ) -> None:
        for row_idx, label in enumerate(layout.qubit_labels):
            y = -row_idx * cls.ROW_HEIGHT
            ax.plot(
                [left_wire, right_wire],
                [y, y],
                color=cls.WIRE_COLOR,
                lw=cls.WIRE_LW,
                zorder=1,
            )
            ax.text(
                left_wire - 0.15,
                y,
                f"{label} :",
                ha="right",
                va="center",
                fontsize=cls.QUBIT_LABEL_FONT_SIZE,
                fontfamily="monospace",
            )

    @classmethod
    def _draw_moment_labels(
        cls,
        ax: Axes,
        layout: CircuitLayout,
        col_x: list[float],
        label_y_top: float,
        label_y_bottom: float,
    ) -> None:
        moment_col_ranges: list[tuple[str, int, int]] = []
        for col_idx, label in enumerate(layout.moment_labels):
            if moment_col_ranges and moment_col_ranges[-1][0] == label:
                moment_col_ranges[-1] = (label, moment_col_ranges[-1][1], col_idx)
            else:
                moment_col_ranges.append((label, col_idx, col_idx))

        for label, col_start, col_end in moment_col_ranges:
            cx = (col_x[col_start] + col_x[col_end]) / 2
            for y_pos in (label_y_top, label_y_bottom):
                ax.text(
                    cx,
                    y_pos,
                    label,
                    ha="center",
                    va="center",
                    fontsize=cls.MOMENT_LABEL_FONT_SIZE,
                    fontfamily="monospace",
                    color="#555555",
                )

    @classmethod
    def _draw_elements(cls, ax: Axes, layout: CircuitLayout, col_x: list[float]) -> None:
        for elem in layout.elements:
            if isinstance(elem, GateBox):
                cls._draw_gate_box(ax, elem, col_x[elem.col])
            elif isinstance(elem, ControlDot):
                cls._draw_control_dot(ax, elem, col_x[elem.col])
            elif isinstance(elem, SwapMarker):
                cls._draw_swap_marker(ax, elem, col_x[elem.col])
            elif isinstance(elem, Connection):
                cls._draw_connection(ax, elem, col_x[elem.col])
            elif isinstance(elem, BarrierLine):
                cls._draw_barrier(ax, elem, col_x[elem.col])
            elif isinstance(elem, JunctionDot):
                cls._draw_junction_dot(ax, elem, col_x[elem.col])

    @classmethod
    def _build_footer_lines(cls, layout: CircuitLayout) -> list[str]:
        footer_lines: list[str] = []
        if layout.global_phase:
            footer_lines.append(f"Global phase: {layout.global_phase}")
        if layout.additional_result_types:
            footer_lines.append(
                f"Additional result types: {', '.join(layout.additional_result_types)}"
            )
        if layout.unassigned_parameters:
            footer_lines.append(f"Unassigned parameters: {', '.join(layout.unassigned_parameters)}")
        return footer_lines

    @classmethod
    def _draw_footer(
        cls, ax: Axes, footer_lines: list[str], left_wire: float, label_y_bottom: float
    ) -> None:
        footer_y = label_y_bottom - cls.ROW_HEIGHT * 0.7
        for i, line in enumerate(footer_lines):
            ax.text(
                left_wire,
                footer_y - i * cls.ROW_HEIGHT * 0.5,
                line,
                ha="left",
                va="top",
                fontsize=cls.FOOTER_FONT_SIZE,
                fontfamily="monospace",
                color="#333333",
            )

    @classmethod
    def _configure_axes(
        cls,
        ax: Axes,
        left_wire: float,
        right_wire: float,
        label_y_top: float,
        label_y_bottom: float,
        footer_lines: list[str],
    ) -> None:
        ax.set_xlim(left_wire - 1.5, right_wire + 0.5)
        y_top = label_y_top + 0.4
        y_bottom = label_y_bottom - 0.4
        if footer_lines:
            y_bottom -= len(footer_lines) * cls.ROW_HEIGHT * 0.5
        ax.set_ylim(y_bottom, y_top)
        ax.set_aspect("equal")
        ax.axis("off")

    @classmethod
    def _draw_gate_box(cls, ax: Axes, elem: GateBox, x: float) -> None:
        y = -elem.row * cls.ROW_HEIGHT

        box_width = cls._gate_box_width(elem.label)

        rect = mpatches.FancyBboxPatch(
            (x - box_width / 2, y - cls.GATE_BOX_HEIGHT / 2),
            box_width,
            cls.GATE_BOX_HEIGHT,
            boxstyle=mpatches.BoxStyle.Round(pad=0.05),
            facecolor=cls.GATE_FILL_COLOR,
            edgecolor=cls.GATE_EDGE_COLOR,
            linewidth=1.2,
            zorder=3,
        )
        ax.add_patch(rect)
        ax.text(
            x,
            y,
            elem.label,
            ha="center",
            va="center",
            fontsize=cls.GATE_FONT_SIZE,
            fontfamily="monospace",
            color=cls.GATE_TEXT_COLOR,
            zorder=4,
        )

    @classmethod
    def _draw_control_dot(cls, ax: Axes, elem: ControlDot, x: float) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        if elem.filled:
            circle = plt.Circle(
                (x, y),
                cls.CONTROL_DOT_RADIUS,
                color=cls.CONTROL_DOT_COLOR,
                zorder=4,
            )
        else:
            circle = plt.Circle(
                (x, y),
                cls.CONTROL_DOT_RADIUS,
                facecolor="white",
                edgecolor=cls.CONTROL_DOT_COLOR,
                linewidth=1.5,
                zorder=4,
            )
        ax.add_patch(circle)

    @classmethod
    def _draw_swap_marker(cls, ax: Axes, elem: SwapMarker, x: float) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        ax.plot(
            x,
            y,
            "x",
            markersize=cls.SWAP_MARKER_SIZE,
            color=cls.CONNECTION_COLOR,
            markeredgewidth=2,
            zorder=4,
        )

    @classmethod
    def _draw_connection(cls, ax: Axes, elem: Connection, x: float) -> None:
        y_start = -elem.row_start * cls.ROW_HEIGHT
        y_end = -elem.row_end * cls.ROW_HEIGHT
        ax.plot(
            [x, x],
            [y_start, y_end],
            color=cls.CONNECTION_COLOR,
            lw=cls.CONNECTION_LW,
            zorder=2,
        )

    @classmethod
    def _draw_barrier(cls, ax: Axes, elem: BarrierLine, x: float) -> None:
        y_start = -elem.row_start * cls.ROW_HEIGHT
        y_end = -elem.row_end * cls.ROW_HEIGHT
        ax.plot(
            [x, x],
            [y_start - cls.ROW_HEIGHT * 0.3, y_end + cls.ROW_HEIGHT * 0.3],
            color=cls.BARRIER_COLOR,
            lw=cls.BARRIER_LW,
            linestyle="--",
            zorder=2,
        )

    @classmethod
    def _draw_junction_dot(cls, ax: Axes, elem: JunctionDot, x: float) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        ax.plot(
            x,
            y,
            "o",
            markersize=cls.JUNCTION_DOT_SIZE,
            color=cls.CONNECTION_COLOR,
            zorder=3,
        )
