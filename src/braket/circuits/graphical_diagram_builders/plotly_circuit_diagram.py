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

from typing import Any

import braket.circuits.circuit as cir
from braket.circuits.graphical_diagram_builders.graphical_circuit_diagram import (
    GraphicalCircuitDiagram,
)
from braket.circuits.graphical_diagram_builders.graphical_diagram_utils import (
    BarrierMarker,
    CircuitLayout,
    Connection,
    ControlDot,
    GateBox,
    SwapMarker,
)
from braket.circuits.moments import MomentType


class PlotlyCircuitDiagram(GraphicalCircuitDiagram):
    """Renders circuit diagrams as interactive Plotly figures.

    The renderer uses the same layout primitives as ``MatplotlibCircuitDiagram``
    and adds hover text for every interactive gate element. Verbatim boxes are
    collapsed by default and can be expanded from the figure controls.

    Examples:
        >>> from braket.circuits import Circuit
        >>> fig = Circuit().h(0).cnot(0, 1).show("interactive")
        >>> fig.show()

    The verbatim expand/collapse controls are derived from layout column ranges,
    so future box-like circuit scopes can reuse the same state-switching path.
    """

    COL_WIDTH = 1.4
    COL_GAP = 0.2
    ROW_HEIGHT = 0.8
    WIRE_EXTEND = 0.5

    GATE_BOX_MIN_WIDTH = 0.6
    GATE_BOX_PADDING = 0.3
    GATE_FILL_COLOR = "#D4E6F1"
    GATE_EDGE_COLOR = "black"
    GATE_TEXT_COLOR = "black"
    WIRE_COLOR = "#333333"
    CONNECTION_COLOR = "black"
    BARRIER_COLOR = "#888888"
    BARRIER_FILL_COLOR = "#DDDDDD"
    COLLAPSED_VERBATIM_COLOR = "#EFE7FF"

    @staticmethod
    def build_diagram(circuit: cir.Circuit) -> Any:
        """Build a Plotly figure for *circuit*.

        Args:
            circuit: The circuit to visualise.

        Returns:
            A ``plotly.graph_objects.Figure``.

        Raises:
            ImportError: If Plotly is not installed.
        """
        go = _plotly_go()
        if not circuit.instructions:
            fig = go.Figure()
            fig.add_annotation(text="(empty circuit)", x=0.5, y=0.5, showarrow=False)
            return PlotlyCircuitDiagram._configure_empty_figure(fig)

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            fig = go.Figure()
            fig.add_annotation(
                text=f"Global phase: {circuit.global_phase}",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return PlotlyCircuitDiagram._configure_empty_figure(fig)

        layout = PlotlyCircuitDiagram._compute_layout(circuit)
        return PlotlyCircuitDiagram._render_layout(layout)

    @classmethod
    def _render_layout(cls, layout: CircuitLayout) -> Any:
        go = _plotly_go()
        fig = go.Figure()

        col_x, col_w = cls._compute_column_x(layout)
        left_wire = col_x[0] - col_w[0] / 2 - cls.WIRE_EXTEND
        right_wire = sum(col_w) + cls.WIRE_EXTEND
        n_rows = max(layout.num_qubits, 1)

        verbatim_ranges = cls._verbatim_ranges(layout)
        visibility: list[tuple[bool, bool]] = []

        def add_trace(trace: Any, *, collapsed: bool = True, expanded: bool = True) -> None:
            trace.visible = collapsed
            fig.add_trace(trace)
            visibility.append((collapsed, expanded))

        cls._add_qubit_wires(fig, layout, left_wire, right_wire, add_trace)
        cls._add_elements(layout, col_x, verbatim_ranges, add_trace)
        cls._add_collapsed_verbatim_boxes(layout, col_x, verbatim_ranges, add_trace)
        cls._add_moment_labels(fig, layout, col_x)
        cls._add_footer(fig, layout, left_wire, n_rows)

        if verbatim_ranges:
            cls._add_verbatim_toggle(fig, visibility)

        cls._configure_axes(fig, left_wire, right_wire, n_rows)
        return fig

    @classmethod
    def _gate_box_width(cls, label: str) -> float:
        char_width = 0.12
        return max(cls.GATE_BOX_MIN_WIDTH, len(label) * char_width + cls.GATE_BOX_PADDING)

    @classmethod
    def _compute_column_x(cls, layout: CircuitLayout) -> tuple[list[float], list[float]]:
        n_cols = max(layout.num_moments, 1)
        widths = [cls.COL_WIDTH] * n_cols
        for elem in layout.elements:
            if isinstance(elem, GateBox):
                widths[elem.col] = max(
                    widths[elem.col], cls._gate_box_width(elem.label) + cls.COL_GAP
                )

        centers: list[float] = []
        cursor = 0.0
        for width in widths:
            centers.append(cursor + width / 2)
            cursor += width
        return centers, widths

    @classmethod
    def _add_qubit_wires(
        cls,
        fig: Any,
        layout: CircuitLayout,
        left_wire: float,
        right_wire: float,
        add_trace: Any,
    ) -> None:
        go = _plotly_go()
        for row_idx, label in enumerate(layout.qubit_labels):
            y = -row_idx * cls.ROW_HEIGHT
            add_trace(
                go.Scatter(
                    x=[left_wire, right_wire],
                    y=[y, y],
                    mode="lines",
                    line={"color": cls.WIRE_COLOR, "width": 1},
                    hoverinfo="skip",
                    showlegend=False,
                    name=f"{label} wire",
                )
            )
            fig.add_annotation(
                x=left_wire - 0.15,
                y=y,
                text=f"{label} :",
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font={"family": "monospace", "size": 12},
            )

    @classmethod
    def _add_elements(
        cls,
        layout: CircuitLayout,
        col_x: list[float],
        verbatim_ranges: list[tuple[int, int]],
        add_trace: Any,
    ) -> None:
        for elem in layout.elements:
            collapsed = not cls._is_col_in_verbatim_range(elem, verbatim_ranges)
            if isinstance(elem, GateBox):
                cls._add_gate_box(layout, elem, col_x[elem.col], add_trace, collapsed)
            elif isinstance(elem, ControlDot):
                cls._add_control_dot(layout, elem, col_x[elem.col], add_trace, collapsed)
            elif isinstance(elem, SwapMarker):
                cls._add_swap_marker(layout, elem, col_x[elem.col], add_trace, collapsed)
            elif isinstance(elem, Connection):
                cls._add_connection(elem, col_x[elem.col], add_trace, collapsed)
            elif isinstance(elem, BarrierMarker):
                cls._add_barrier(layout, elem, col_x[elem.col], add_trace, collapsed)

    @classmethod
    def _add_gate_box(
        cls,
        layout: CircuitLayout,
        elem: GateBox,
        x: float,
        add_trace: Any,
        collapsed: bool,
    ) -> None:
        go = _plotly_go()
        y = -elem.row * cls.ROW_HEIGHT
        marker_size = max(34, min(90, 10 * len(elem.label) + 20))
        add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                marker={
                    "symbol": "square",
                    "size": marker_size,
                    "color": cls.GATE_FILL_COLOR,
                    "line": {"color": cls.GATE_EDGE_COLOR, "width": 1.5},
                },
                text=[elem.label],
                textposition="middle center",
                textfont={"family": "monospace", "color": cls.GATE_TEXT_COLOR, "size": 11},
                hovertemplate=cls._hover_template(
                    elem.label,
                    layout.qubit_labels[elem.row],
                    "gate",
                ),
                showlegend=False,
                name=f"{elem.label} on {layout.qubit_labels[elem.row]}",
            ),
            collapsed=collapsed,
            expanded=True,
        )
        if elem.label in {"StartVerbatim", "EndVerbatim"}:
            add_trace(
                go.Scatter(
                    x=[x],
                    y=[y + cls.ROW_HEIGHT * 0.32],
                    mode="text",
                    text=["verbatim boundary"],
                    textfont={"size": 9, "color": "#555555"},
                    hoverinfo="skip",
                    showlegend=False,
                    name=f"{elem.label} label",
                ),
                collapsed=collapsed,
                expanded=True,
            )

    @classmethod
    def _add_control_dot(
        cls,
        layout: CircuitLayout,
        elem: ControlDot,
        x: float,
        add_trace: Any,
        collapsed: bool,
    ) -> None:
        go = _plotly_go()
        y = -elem.row * cls.ROW_HEIGHT
        add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={
                    "symbol": "circle",
                    "size": 14,
                    "color": "black" if elem.filled else "white",
                    "line": {"color": "black", "width": 2},
                },
                hovertemplate=(
                    f"Control<br>Target qubit: {layout.qubit_labels[elem.row]}"
                    "<br>Device metadata: unavailable<extra></extra>"
                ),
                showlegend=False,
                name=f"control on {layout.qubit_labels[elem.row]}",
            ),
            collapsed=collapsed,
            expanded=True,
        )

    @classmethod
    def _add_swap_marker(
        cls,
        layout: CircuitLayout,
        elem: SwapMarker,
        x: float,
        add_trace: Any,
        collapsed: bool,
    ) -> None:
        go = _plotly_go()
        y = -elem.row * cls.ROW_HEIGHT
        add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={
                    "symbol": "x",
                    "size": 16,
                    "color": cls.CONNECTION_COLOR,
                    "line": {"width": 3},
                },
                hovertemplate=cls._hover_template("SWAP", layout.qubit_labels[elem.row], "gate"),
                showlegend=False,
                name=f"swap on {layout.qubit_labels[elem.row]}",
            ),
            collapsed=collapsed,
            expanded=True,
        )

    @classmethod
    def _add_connection(cls, elem: Connection, x: float, add_trace: Any, collapsed: bool) -> None:
        go = _plotly_go()
        add_trace(
            go.Scatter(
                x=[x, x],
                y=[-elem.row_start * cls.ROW_HEIGHT, -elem.row_end * cls.ROW_HEIGHT],
                mode="lines",
                line={"color": cls.CONNECTION_COLOR, "width": 2},
                hoverinfo="skip",
                showlegend=False,
                name="connection",
            ),
            collapsed=collapsed,
            expanded=True,
        )

    @classmethod
    def _add_barrier(
        cls,
        layout: CircuitLayout,
        elem: BarrierMarker,
        x: float,
        add_trace: Any,
        collapsed: bool,
    ) -> None:
        go = _plotly_go()
        y = -elem.row * cls.ROW_HEIGHT
        add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={
                    "symbol": "square",
                    "size": 24,
                    "color": cls.BARRIER_FILL_COLOR,
                    "line": {"color": cls.BARRIER_COLOR, "width": 1},
                },
                hovertemplate=(
                    f"Barrier<br>Target qubit: {layout.qubit_labels[elem.row]}<extra></extra>"
                ),
                showlegend=False,
                name=f"barrier on {layout.qubit_labels[elem.row]}",
            ),
            collapsed=collapsed,
            expanded=True,
        )

    @classmethod
    def _add_collapsed_verbatim_boxes(
        cls,
        layout: CircuitLayout,
        col_x: list[float],
        verbatim_ranges: list[tuple[int, int]],
        add_trace: Any,
    ) -> None:
        go = _plotly_go()
        for index, (start_col, end_col) in enumerate(verbatim_ranges, start=1):
            rows = cls._rows_in_cols(layout, start_col, end_col)
            if not rows:
                rows = list(range(layout.num_qubits))
            y_center = -(min(rows) + max(rows)) * cls.ROW_HEIGHT / 2
            x_center = (col_x[start_col] + col_x[end_col]) / 2
            marker_size = max(52, int((end_col - start_col + 1) * 22))
            add_trace(
                go.Scatter(
                    x=[x_center],
                    y=[y_center],
                    mode="markers+text",
                    marker={
                        "symbol": "square",
                        "size": marker_size,
                        "color": cls.COLLAPSED_VERBATIM_COLOR,
                        "line": {"color": "#6B46C1", "width": 2},
                    },
                    text=["Verbatim"],
                    textposition="middle center",
                    textfont={"family": "monospace", "color": "#322659", "size": 11},
                    hovertemplate=(
                        "Verbatim box<br>"
                        f"Columns: {start_col}-{end_col}<br>"
                        "Use the figure controls to expand or collapse this box."
                        "<extra></extra>"
                    ),
                    showlegend=False,
                    name=f"collapsed verbatim box {index}",
                ),
                collapsed=True,
                expanded=False,
            )
            add_trace(
                go.Scatter(
                    x=[x_center],
                    y=[y_center - cls.ROW_HEIGHT * 0.38],
                    mode="text",
                    text=["expand from controls"],
                    textfont={"size": 9, "color": "#6B46C1"},
                    hoverinfo="skip",
                    showlegend=False,
                    name=f"collapsed verbatim box {index} label",
                ),
                collapsed=True,
                expanded=False,
            )

    @classmethod
    def _add_moment_labels(cls, fig: Any, layout: CircuitLayout, col_x: list[float]) -> None:
        n_rows = max(layout.num_qubits, 1)
        top_y = cls.ROW_HEIGHT * 0.8
        bottom_y = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.8
        moment_col_ranges: list[tuple[str, int, int]] = []
        for col_idx, label in enumerate(layout.moment_labels):
            if moment_col_ranges and moment_col_ranges[-1][0] == label:
                moment_col_ranges[-1] = (label, moment_col_ranges[-1][1], col_idx)
            else:
                moment_col_ranges.append((label, col_idx, col_idx))

        for label, col_start, col_end in moment_col_ranges:
            x = (col_x[col_start] + col_x[col_end]) / 2
            for y in (top_y, bottom_y):
                fig.add_annotation(
                    x=x,
                    y=y,
                    text=label,
                    showarrow=False,
                    font={"family": "monospace", "size": 10, "color": "#555555"},
                )

    @classmethod
    def _add_footer(cls, fig: Any, layout: CircuitLayout, left_wire: float, n_rows: int) -> None:
        lines = cls._footer_lines(layout)
        bottom_y = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 1.35
        for index, line in enumerate(lines):
            fig.add_annotation(
                x=left_wire,
                y=bottom_y - index * cls.ROW_HEIGHT * 0.45,
                text=line,
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font={"family": "monospace", "size": 10, "color": "#333333"},
            )

    @classmethod
    def _footer_lines(cls, layout: CircuitLayout) -> list[str]:
        lines: list[str] = []
        if layout.global_phase:
            lines.append(f"Global phase: {layout.global_phase}")
        if layout.additional_result_types:
            lines.append(f"Additional result types: {', '.join(layout.additional_result_types)}")
        if layout.unassigned_parameters:
            lines.append(f"Unassigned parameters: {', '.join(layout.unassigned_parameters)}")
        return lines

    @staticmethod
    def _add_verbatim_toggle(fig: Any, visibility: list[tuple[bool, bool]]) -> None:
        collapsed_visibility = [collapsed for collapsed, _ in visibility]
        expanded_visibility = [expanded for _, expanded in visibility]
        fig.update_layout(
            updatemenus=[
                {
                    "type": "buttons",
                    "direction": "right",
                    "x": 0,
                    "y": 1.16,
                    "buttons": [
                        {
                            "label": "Collapse verbatim boxes",
                            "method": "update",
                            "args": [{"visible": collapsed_visibility}],
                        },
                        {
                            "label": "Expand verbatim boxes",
                            "method": "update",
                            "args": [{"visible": expanded_visibility}],
                        },
                    ],
                }
            ]
        )

    @classmethod
    def _configure_axes(cls, fig: Any, left_wire: float, right_wire: float, n_rows: int) -> None:
        top_y = cls.ROW_HEIGHT * 1.3
        bottom_y = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 1.8
        fig.update_xaxes(range=[left_wire - 1.2, right_wire + 0.6], visible=False)
        fig.update_yaxes(
            range=[bottom_y, top_y],
            visible=False,
            scaleanchor="x",
            scaleratio=1,
        )
        fig.update_layout(
            showlegend=False,
            margin={"l": 20, "r": 20, "t": 70, "b": 30},
            template="plotly_white",
            hovermode="closest",
        )

    @staticmethod
    def _configure_empty_figure(fig: Any) -> Any:
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(
            showlegend=False,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            template="plotly_white",
        )
        return fig

    @staticmethod
    def _hover_template(label: str, qubit_label: str, element_type: str) -> str:
        gate_name, parameters = _split_gate_label(label)
        return (
            f"{element_type.title()} name: {gate_name}<br>"
            f"Target qubit: {qubit_label}<br>"
            f"Parameters: {parameters}<br>"
            "Device metadata: unavailable"
            "<extra></extra>"
        )

    @staticmethod
    def _verbatim_ranges(layout: CircuitLayout) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        start_col: int | None = None
        for elem in sorted(
            (e for e in layout.elements if isinstance(e, GateBox)),
            key=lambda gate: (gate.col, gate.row),
        ):
            if elem.label == "StartVerbatim" and start_col is None:
                start_col = elem.col
            elif elem.label == "EndVerbatim" and start_col is not None:
                ranges.append((start_col, elem.col))
                start_col = None
        return ranges

    @staticmethod
    def _is_col_in_verbatim_range(elem: Any, ranges: list[tuple[int, int]]) -> bool:
        col = getattr(elem, "col", None)
        return any(start <= col <= end for start, end in ranges)

    @staticmethod
    def _rows_in_cols(layout: CircuitLayout, start_col: int, end_col: int) -> list[int]:
        rows: set[int] = set()
        for elem in layout.elements:
            col = getattr(elem, "col", None)
            if col is None or not start_col <= col <= end_col:
                continue
            if hasattr(elem, "row"):
                rows.add(elem.row)
            elif isinstance(elem, Connection):
                rows.update(range(elem.row_start, elem.row_end + 1))
        return sorted(rows)


def _plotly_go() -> Any:
    try:
        import plotly.graph_objects as go  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "PlotlyCircuitDiagram requires Plotly. Install it with "
            "`pip install amazon-braket-sdk[interactive]` or `pip install plotly`."
        ) from exc
    return go


def _split_gate_label(label: str) -> tuple[str, str]:
    if "(" not in label or not label.endswith(")"):
        return label, "none"
    gate_name, parameters = label.split("(", 1)
    return gate_name, parameters[:-1] or "none"
