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

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

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

try:
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover - exercised when optional extra is absent
    go = None


@dataclass(frozen=True)
class _VerbatimBlock:
    start_col: int
    end_col: int
    row_start: int
    row_end: int


class PlotlyCircuitDiagram(GraphicalCircuitDiagram):
    """Renders circuit diagrams as interactive Plotly figures.

    Example:
        >>> from braket.circuits import Circuit
        >>> fig = Circuit().h(0).cnot(0, 1).show("interactive")

    Verbatim boxes are drawn as collapsed blocks by default. The generated
    figure includes an expand/collapse control that toggles between the
    summary block and the inline instructions. The same mechanism can be
    extended to future circuit sub-structures by identifying their column
    ranges and adding corresponding collapsed overlay traces.
    """

    COL_WIDTH = 1.4
    COL_GAP = 0.2
    ROW_HEIGHT = 0.8
    WIRE_EXTEND = 0.5

    GATE_BOX_HEIGHT = 0.5
    GATE_BOX_MIN_WIDTH = 0.6
    GATE_BOX_PADDING = 0.3
    GATE_FONT_SIZE = 10
    GATE_FILL_COLOR = "#D4E6F1"
    GATE_EDGE_COLOR = "black"
    GATE_TEXT_COLOR = "black"

    WIRE_COLOR = "#333333"
    WIRE_LW = 1.0

    CONTROL_DOT_SIZE = 10
    CONTROL_DOT_COLOR = "black"

    CONNECTION_LW = 2
    CONNECTION_COLOR = "black"
    BARRIER_COLOR = "#888888"
    BARRIER_FILL_COLOR = "#DDDDDD"
    BARRIER_WIDTH = 0.25
    BARRIER_HEIGHT_FRAC = 0.6

    QUBIT_LABEL_FONT_SIZE = 12
    MOMENT_LABEL_FONT_SIZE = 10
    FOOTER_FONT_SIZE = 10

    SWAP_MARKER_SIZE = 12

    VERBATIM_FILL_COLOR = "#FFF2CC"
    VERBATIM_EDGE_COLOR = "#B7950B"
    VERBATIM_LABEL = "Verbatim"

    _ALWAYS: ClassVar[str] = "always"
    _COLLAPSED_ONLY: ClassVar[str] = "collapsed"
    _EXPANDED_ONLY: ClassVar[str] = "expanded"

    @classmethod
    def build_diagram(
        cls,
        circuit: cir.Circuit,
        *,
        device_metadata: Mapping[str, Any] | None = None,
    ) -> Any:
        """Build a Plotly figure for *circuit*.

        Args:
            circuit: The circuit to visualize.
            device_metadata: Optional metadata keyed by gate label, gate name, or
                ``"{gate_name}:{comma_separated_qubit_labels}"``. Matching values
                are included in hover text and can hold device-specific data such
                as fidelity or error rate.

        Returns:
            A ``plotly.graph_objects.Figure`` that renders inline in Jupyter.

        Raises:
            ImportError: If Plotly is not installed.
        """
        cls._ensure_plotly_available()

        if not circuit.instructions:
            return cls._build_message_figure("(empty circuit)")

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            return cls._build_message_figure(f"Global phase: {circuit.global_phase}")

        layout = cls._compute_layout(circuit)
        return cls._render_layout(layout, device_metadata=device_metadata)

    @classmethod
    def _ensure_plotly_available(cls) -> None:
        if go is None:
            msg = (
                "Plotly is required for interactive circuit diagrams. Install it with "
                "`pip install amazon-braket-sdk[interactive]`."
            )
            raise ImportError(msg)

    @classmethod
    def _build_message_figure(cls, message: str) -> Any:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=message,
            showarrow=False,
            font={"size": 14},
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(
            height=160,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            showlegend=False,
            template="plotly_white",
        )
        return fig

    @classmethod
    def _gate_box_width(cls, label: str) -> float:
        char_width = cls.GATE_FONT_SIZE * 0.012
        text_width = len(label) * char_width
        return max(cls.GATE_BOX_MIN_WIDTH, text_width + cls.GATE_BOX_PADDING)

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
    def _render_layout(
        cls,
        layout: CircuitLayout,
        *,
        device_metadata: Mapping[str, Any] | None = None,
    ) -> Any:
        n_rows = max(layout.num_qubits, 1)
        col_x, col_w = cls._compute_column_x(layout)
        total_width = sum(col_w)
        right_edge = total_width

        left_wire = col_x[0] - col_w[0] / 2 - cls.WIRE_EXTEND
        right_wire = right_edge + cls.WIRE_EXTEND
        label_y_top = cls.ROW_HEIGHT * 0.8
        label_y_bottom = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.8

        fig = go.Figure()
        trace_kinds: list[str] = []

        verbatim_blocks = cls._find_verbatim_blocks(layout)
        collapsed_cols = {
            col for block in verbatim_blocks for col in range(block.start_col, block.end_col + 1)
        }

        cls._draw_qubit_wires(fig, trace_kinds, layout, left_wire, right_wire)
        cls._draw_elements(fig, trace_kinds, layout, col_x, collapsed_cols, device_metadata)
        cls._draw_verbatim_blocks(fig, trace_kinds, layout, col_x, col_w, verbatim_blocks)
        cls._draw_moment_labels(fig, layout, col_x, label_y_top, label_y_bottom)

        footer_lines = cls._build_footer_lines(layout)
        if footer_lines:
            cls._draw_footer(fig, footer_lines, left_wire, label_y_bottom)

        cls._configure_figure(
            fig,
            left_wire,
            right_wire,
            label_y_top,
            label_y_bottom,
            footer_lines,
            total_width,
            n_rows,
        )
        if verbatim_blocks:
            cls._add_verbatim_toggle(fig, trace_kinds)
        return fig

    @classmethod
    def _draw_qubit_wires(
        cls,
        fig: Any,
        trace_kinds: list[str],
        layout: CircuitLayout,
        left_wire: float,
        right_wire: float,
    ) -> None:
        for row_idx, label in enumerate(layout.qubit_labels):
            y = -row_idx * cls.ROW_HEIGHT
            cls._add_trace(
                fig,
                trace_kinds,
                go.Scatter(
                    x=[left_wire, right_wire],
                    y=[y, y],
                    mode="lines",
                    line={"color": cls.WIRE_COLOR, "width": cls.WIRE_LW},
                    hoverinfo="skip",
                    showlegend=False,
                ),
            )
            fig.add_annotation(
                x=left_wire - 0.15,
                y=y,
                text=f"{label} :",
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font={"family": "monospace", "size": cls.QUBIT_LABEL_FONT_SIZE},
            )

    @classmethod
    def _draw_moment_labels(
        cls,
        fig: Any,
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
                fig.add_annotation(
                    x=cx,
                    y=y_pos,
                    text=label,
                    showarrow=False,
                    xanchor="center",
                    yanchor="middle",
                    font={
                        "family": "monospace",
                        "size": cls.MOMENT_LABEL_FONT_SIZE,
                        "color": "#555555",
                    },
                )

    @classmethod
    def _draw_elements(
        cls,
        fig: Any,
        trace_kinds: list[str],
        layout: CircuitLayout,
        col_x: list[float],
        collapsed_cols: set[int],
        device_metadata: Mapping[str, Any] | None,
    ) -> None:
        gate_targets = cls._gate_targets_by_col_and_label(layout)
        for elem in layout.elements:
            kind = cls._EXPANDED_ONLY if cls._element_col(elem) in collapsed_cols else cls._ALWAYS
            if isinstance(elem, GateBox):
                target_qubits = gate_targets[elem.col, elem.label]
                cls._draw_gate_box(
                    fig,
                    trace_kinds,
                    elem,
                    col_x[elem.col],
                    target_qubits,
                    device_metadata,
                    kind,
                )
            elif isinstance(elem, ControlDot):
                cls._draw_control_dot(fig, trace_kinds, elem, col_x[elem.col], layout, kind)
            elif isinstance(elem, SwapMarker):
                cls._draw_swap_marker(fig, trace_kinds, elem, col_x[elem.col], layout, kind)
            elif isinstance(elem, Connection):
                cls._draw_connection(fig, trace_kinds, elem, col_x[elem.col], kind)
            elif isinstance(elem, BarrierMarker):
                cls._draw_barrier(fig, trace_kinds, elem, col_x[elem.col], layout, kind)

    @staticmethod
    def _element_col(elem: object) -> int | None:
        return getattr(elem, "col", None)

    @classmethod
    def _gate_targets_by_col_and_label(
        cls, layout: CircuitLayout
    ) -> dict[tuple[int, str], list[str]]:
        targets: dict[tuple[int, str], list[str]] = {}
        for elem in layout.elements:
            if isinstance(elem, GateBox):
                key = (elem.col, elem.label)
                targets.setdefault(key, []).append(layout.qubit_labels[elem.row])
        return targets

    @classmethod
    def _draw_gate_box(
        cls,
        fig: Any,
        trace_kinds: list[str],
        elem: GateBox,
        x: float,
        target_qubits: list[str],
        device_metadata: Mapping[str, Any] | None,
        kind: str,
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        box_width = cls._gate_box_width(elem.label)
        x0 = x - box_width / 2
        x1 = x + box_width / 2
        y0 = y - cls.GATE_BOX_HEIGHT / 2
        y1 = y + cls.GATE_BOX_HEIGHT / 2

        cls._add_rectangle_trace(
            fig,
            trace_kinds,
            x0,
            x1,
            y0,
            y1,
            cls.GATE_FILL_COLOR,
            cls.GATE_EDGE_COLOR,
            kind,
        )
        cls._add_trace(
            fig,
            trace_kinds,
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                marker={"size": max(18, len(elem.label) * 7), "opacity": 0},
                text=[elem.label],
                textfont={
                    "family": "monospace",
                    "size": cls.GATE_FONT_SIZE,
                    "color": cls.GATE_TEXT_COLOR,
                },
                textposition="middle center",
                hovertemplate=cls._gate_hover_template(
                    elem.label,
                    target_qubits,
                    device_metadata,
                ),
                showlegend=False,
            ),
            kind,
        )

    @classmethod
    def _draw_control_dot(
        cls,
        fig: Any,
        trace_kinds: list[str],
        elem: ControlDot,
        x: float,
        layout: CircuitLayout,
        kind: str,
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        cls._add_trace(
            fig,
            trace_kinds,
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={
                    "size": cls.CONTROL_DOT_SIZE,
                    "color": cls.CONTROL_DOT_COLOR if elem.filled else "white",
                    "line": {"color": cls.CONTROL_DOT_COLOR, "width": 2},
                    "symbol": "circle",
                },
                hovertemplate=(
                    f"Control qubit: {layout.qubit_labels[elem.row]}<br>"
                    f"State: {'1' if elem.filled else '0'}<extra></extra>"
                ),
                showlegend=False,
            ),
            kind,
        )

    @classmethod
    def _draw_swap_marker(
        cls,
        fig: Any,
        trace_kinds: list[str],
        elem: SwapMarker,
        x: float,
        layout: CircuitLayout,
        kind: str,
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        cls._add_trace(
            fig,
            trace_kinds,
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={
                    "size": cls.SWAP_MARKER_SIZE,
                    "color": cls.CONNECTION_COLOR,
                    "symbol": "x",
                    "line": {"width": 2},
                },
                hovertemplate=(
                    f"Gate name: SWAP<br>"
                    f"Target qubit(s): {layout.qubit_labels[elem.row]}<br>"
                    "Gate parameters: None<br>"
                    "Device metadata: Not provided<extra></extra>"
                ),
                showlegend=False,
            ),
            kind,
        )

    @classmethod
    def _draw_connection(
        cls,
        fig: Any,
        trace_kinds: list[str],
        elem: Connection,
        x: float,
        kind: str,
    ) -> None:
        y_start = -elem.row_start * cls.ROW_HEIGHT
        y_end = -elem.row_end * cls.ROW_HEIGHT
        cls._add_trace(
            fig,
            trace_kinds,
            go.Scatter(
                x=[x, x],
                y=[y_start, y_end],
                mode="lines",
                line={"color": cls.CONNECTION_COLOR, "width": cls.CONNECTION_LW},
                hoverinfo="skip",
                showlegend=False,
            ),
            kind,
        )

    @classmethod
    def _draw_barrier(
        cls,
        fig: Any,
        trace_kinds: list[str],
        elem: BarrierMarker,
        x: float,
        layout: CircuitLayout,
        kind: str,
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        half_h = cls.ROW_HEIGHT * cls.BARRIER_HEIGHT_FRAC / 2
        half_w = cls.BARRIER_WIDTH / 2
        cls._add_rectangle_trace(
            fig,
            trace_kinds,
            x - half_w,
            x + half_w,
            y - half_h,
            y + half_h,
            cls.BARRIER_FILL_COLOR,
            cls.BARRIER_COLOR,
            kind,
            hovertemplate=(
                f"Barrier<br>Target qubit(s): {layout.qubit_labels[elem.row]}<extra></extra>"
            ),
        )

    @classmethod
    def _draw_verbatim_blocks(
        cls,
        fig: Any,
        trace_kinds: list[str],
        layout: CircuitLayout,
        col_x: list[float],
        col_w: list[float],
        verbatim_blocks: list[_VerbatimBlock],
    ) -> None:
        for block in verbatim_blocks:
            x0 = col_x[block.start_col] - col_w[block.start_col] / 2 + cls.COL_GAP / 2
            x1 = col_x[block.end_col] + col_w[block.end_col] / 2 - cls.COL_GAP / 2
            y_top = -block.row_start * cls.ROW_HEIGHT + cls.ROW_HEIGHT * 0.4
            y_bottom = -block.row_end * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.4
            x_center = (x0 + x1) / 2
            y_center = (y_top + y_bottom) / 2
            block_qubits = ", ".join(layout.qubit_labels[block.row_start : block.row_end + 1])
            column_count = block.end_col - block.start_col + 1
            hovertemplate = (
                f"Verbatim block<br>Target qubit(s): {block_qubits}<br>"
                f"Collapsed columns: {column_count}<br>"
                "Use the expand/collapse control to reveal or hide inline gates."
                "<extra></extra>"
            )
            cls._add_rectangle_trace(
                fig,
                trace_kinds,
                x0,
                x1,
                y_bottom,
                y_top,
                cls.VERBATIM_FILL_COLOR,
                cls.VERBATIM_EDGE_COLOR,
                cls._COLLAPSED_ONLY,
                hovertemplate=hovertemplate,
                line_dash="dash",
            )
            cls._add_trace(
                fig,
                trace_kinds,
                go.Scatter(
                    x=[x_center],
                    y=[y_center],
                    mode="markers+text",
                    marker={"size": max(28, len(cls.VERBATIM_LABEL) * 8), "opacity": 0},
                    text=[cls.VERBATIM_LABEL],
                    textfont={
                        "family": "monospace",
                        "size": cls.GATE_FONT_SIZE,
                        "color": cls.GATE_TEXT_COLOR,
                    },
                    textposition="middle center",
                    hovertemplate=hovertemplate,
                    showlegend=False,
                ),
                cls._COLLAPSED_ONLY,
            )

    @classmethod
    def _find_verbatim_blocks(cls, layout: CircuitLayout) -> list[_VerbatimBlock]:
        start_cols = sorted({
            elem.col
            for elem in layout.elements
            if isinstance(elem, GateBox) and elem.label == "StartVerbatim"
        })
        end_cols = sorted({
            elem.col
            for elem in layout.elements
            if isinstance(elem, GateBox) and elem.label == "EndVerbatim"
        })

        blocks: list[_VerbatimBlock] = []
        remaining_end_cols = end_cols.copy()
        for start_col in start_cols:
            matching_end = next((col for col in remaining_end_cols if col > start_col), None)
            if matching_end is None:
                continue
            remaining_end_cols.remove(matching_end)
            rows = cls._rows_in_column_range(layout, start_col, matching_end)
            if rows:
                blocks.append(
                    _VerbatimBlock(
                        start_col=start_col,
                        end_col=matching_end,
                        row_start=min(rows),
                        row_end=max(rows),
                    )
                )
        return blocks

    @staticmethod
    def _rows_in_column_range(layout: CircuitLayout, start_col: int, end_col: int) -> set[int]:
        rows: set[int] = set()
        for elem in layout.elements:
            elem_col = getattr(elem, "col", None)
            if elem_col is not None and start_col <= elem_col <= end_col:
                elem_row = getattr(elem, "row", None)
                if elem_row is not None:
                    rows.add(elem_row)
            if isinstance(elem, Connection) and start_col <= elem.col <= end_col:
                rows.update(range(elem.row_start, elem.row_end + 1))
        return rows

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
        cls,
        fig: Any,
        footer_lines: list[str],
        left_wire: float,
        label_y_bottom: float,
    ) -> None:
        footer_y = label_y_bottom - cls.ROW_HEIGHT * 0.7
        for i, line in enumerate(footer_lines):
            fig.add_annotation(
                x=left_wire,
                y=footer_y - i * cls.ROW_HEIGHT * 0.5,
                text=line,
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font={"family": "monospace", "size": cls.FOOTER_FONT_SIZE, "color": "#333333"},
            )

    @classmethod
    def _configure_figure(
        cls,
        fig: Any,
        left_wire: float,
        right_wire: float,
        label_y_top: float,
        label_y_bottom: float,
        footer_lines: list[str],
        total_width: float,
        n_rows: int,
    ) -> None:
        y_top = label_y_top + 0.4
        y_bottom = label_y_bottom - 0.4
        if footer_lines:
            y_bottom -= len(footer_lines) * cls.ROW_HEIGHT * 0.5

        fig_width = max(520, int((cls.WIRE_EXTEND * 2 + total_width + 1.5) * 110))
        fig_height = max(260, int((n_rows * cls.ROW_HEIGHT + 1.7) * 120))
        fig.update_xaxes(visible=False, range=[left_wire - 1.5, right_wire + 0.5])
        fig.update_yaxes(
            visible=False,
            range=[y_bottom, y_top],
            scaleanchor="x",
            scaleratio=1,
        )
        fig.update_layout(
            width=fig_width,
            height=fig_height,
            hovermode="closest",
            margin={"l": 20, "r": 20, "t": 55, "b": 20},
            showlegend=False,
            template="plotly_white",
        )

    @classmethod
    def _add_verbatim_toggle(cls, fig: Any, trace_kinds: list[str]) -> None:
        collapsed_mask = [kind != cls._EXPANDED_ONLY for kind in trace_kinds]
        expanded_mask = [kind != cls._COLLAPSED_ONLY for kind in trace_kinds]
        fig.update_layout(
            updatemenus=[
                {
                    "type": "buttons",
                    "direction": "right",
                    "x": 0,
                    "xanchor": "left",
                    "y": 1.08,
                    "yanchor": "bottom",
                    "buttons": [
                        {
                            "label": "Collapse verbatim boxes",
                            "method": "update",
                            "args": [{"visible": collapsed_mask}],
                        },
                        {
                            "label": "Expand verbatim boxes",
                            "method": "update",
                            "args": [{"visible": expanded_mask}],
                        },
                    ],
                }
            ]
        )

    @classmethod
    def _add_rectangle_trace(
        cls,
        fig: Any,
        trace_kinds: list[str],
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        fill_color: str,
        edge_color: str,
        kind: str,
        *,
        hovertemplate: str | None = None,
        line_dash: str | None = None,
    ) -> None:
        cls._add_trace(
            fig,
            trace_kinds,
            go.Scatter(
                x=[x0, x1, x1, x0, x0],
                y=[y0, y0, y1, y1, y0],
                mode="lines",
                fill="toself",
                fillcolor=fill_color,
                line={"color": edge_color, "width": 1.2, "dash": line_dash},
                hoverinfo="skip" if hovertemplate is None else None,
                hovertemplate=hovertemplate,
                showlegend=False,
            ),
            kind,
        )

    @classmethod
    def _add_trace(
        cls,
        fig: Any,
        trace_kinds: list[str],
        trace: Any,
        kind: str = _ALWAYS,
    ) -> None:
        trace.visible = kind != cls._EXPANDED_ONLY
        fig.add_trace(trace)
        trace_kinds.append(kind)

    @classmethod
    def _gate_hover_template(
        cls,
        label: str,
        target_qubits: list[str],
        device_metadata: Mapping[str, Any] | None,
    ) -> str:
        gate_name, parameters = cls._parse_gate_label(label)
        metadata = cls._device_metadata_text(label, gate_name, target_qubits, device_metadata)
        return (
            f"Gate name: {gate_name}<br>"
            f"Target qubit(s): {', '.join(target_qubits)}<br>"
            f"Gate parameters: {parameters}<br>"
            f"Device metadata: {metadata}<extra></extra>"
        )

    @staticmethod
    def _parse_gate_label(label: str) -> tuple[str, str]:
        power = None
        gate_label = label
        if "^" in gate_label:
            gate_label, power = gate_label.split("^", maxsplit=1)

        parameters = "None"
        gate_name = gate_label
        if "(" in gate_label and gate_label.endswith(")"):
            gate_name, parameter_text = gate_label[:-1].split("(", maxsplit=1)
            parameters = parameter_text or "None"
        if power is not None:
            parameters = (
                f"{parameters}; power={power}" if parameters != "None" else f"power={power}"
            )
        return gate_name, parameters

    @staticmethod
    def _device_metadata_text(
        label: str,
        gate_name: str,
        target_qubits: list[str],
        device_metadata: Mapping[str, Any] | None,
    ) -> str:
        if not device_metadata:
            return "Not provided"

        qubit_key = ",".join(target_qubits)
        for key in (
            f"{gate_name}:{qubit_key}",
            f"{label}:{qubit_key}",
            gate_name,
            label,
        ):
            if key in device_metadata:
                return str(device_metadata[key])
        return "Not provided"
