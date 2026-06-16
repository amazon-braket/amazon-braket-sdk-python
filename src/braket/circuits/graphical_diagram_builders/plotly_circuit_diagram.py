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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NamedTuple

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

if TYPE_CHECKING:
    import plotly.graph_objects as go


class _VerbatimTraceGroup(NamedTuple):
    start: int
    end: int
    collapsed_indices: list[int]
    expanded_indices: list[int]


@dataclass
class _TraceParts:
    gate_x: list[float | None] = field(default_factory=list)
    gate_y: list[float | None] = field(default_factory=list)
    gate_text_x: list[float] = field(default_factory=list)
    gate_text_y: list[float] = field(default_factory=list)
    gate_text: list[str] = field(default_factory=list)
    barrier_x: list[float | None] = field(default_factory=list)
    barrier_y: list[float | None] = field(default_factory=list)
    barrier_text_x: list[float] = field(default_factory=list)
    barrier_text_y: list[float] = field(default_factory=list)
    connection_x: list[float | None] = field(default_factory=list)
    connection_y: list[float | None] = field(default_factory=list)
    hover_x: list[float] = field(default_factory=list)
    hover_y: list[float] = field(default_factory=list)
    hover_text: list[str] = field(default_factory=list)
    filled_control_x: list[float] = field(default_factory=list)
    filled_control_y: list[float] = field(default_factory=list)
    filled_control_hover: list[str] = field(default_factory=list)
    open_control_x: list[float] = field(default_factory=list)
    open_control_y: list[float] = field(default_factory=list)
    open_control_hover: list[str] = field(default_factory=list)
    swap_x: list[float] = field(default_factory=list)
    swap_y: list[float] = field(default_factory=list)
    swap_hover: list[str] = field(default_factory=list)


class PlotlyCircuitDiagram(GraphicalCircuitDiagram):
    """Renders circuit diagrams as interactive Plotly figures.

    Examples:
        >>> from braket.circuits import Circuit
        >>> fig = Circuit().h(0).cnot(0, 1).to_plotly()

    The returned figure includes hover tooltips and, for verbatim boxes, buttons to switch
    individual boxes between collapsed and expanded views.
    """

    COL_WIDTH = 1.4
    COL_GAP = 0.2
    ROW_HEIGHT = 0.8
    WIRE_EXTEND = 0.5

    GATE_BOX_HEIGHT = 0.5
    GATE_BOX_MIN_WIDTH = 0.6
    GATE_BOX_PADDING = 0.3
    GATE_FONT_SIZE = 12
    GATE_FILL_COLOR = "#D4E6F1"
    GATE_EDGE_COLOR = "black"
    GATE_TEXT_COLOR = "black"

    WIRE_COLOR = "#333333"
    WIRE_WIDTH = 1
    CONNECTION_COLOR = "black"
    CONNECTION_WIDTH = 2

    CONTROL_DOT_SIZE = 12
    SWAP_MARKER_SIZE = 13

    BARRIER_COLOR = "#888888"
    BARRIER_FILL_COLOR = "#DDDDDD"
    BARRIER_WIDTH = 0.25
    BARRIER_HEIGHT_FRAC = 0.6

    QUBIT_LABEL_FONT_SIZE = 12
    MOMENT_LABEL_FONT_SIZE = 10
    FOOTER_FONT_SIZE = 10

    @staticmethod
    def build_diagram(
        circuit: cir.Circuit,
        device_metadata: Mapping[str, Any] | None = None,
    ) -> go.Figure:
        """Build a Plotly Figure for *circuit*.

        Args:
            circuit: The circuit to visualise.
            device_metadata: Optional metadata to include in gate hover text. Keys may be
                rendered gate labels (for example, ``"Rx(theta)"``) or source operator names
                (for example, ``"CNot"``); values may be scalars or mappings such as
                ``{"fidelity": 0.997}``.

        Returns:
            A ``plotly.graph_objects.Figure``.

        Raises:
            ImportError: If Plotly is not installed.

        Examples:
            >>> from braket.circuits import Circuit
            >>> fig = Circuit().h(0).cnot(0, 1).to_plotly()
        """
        go = PlotlyCircuitDiagram._get_plotly()

        if not circuit.instructions:
            fig = go.Figure()
            PlotlyCircuitDiagram._add_center_annotation(fig, "(empty circuit)")
            PlotlyCircuitDiagram._configure_empty_figure(fig, width=260, height=140)
            return fig

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            fig = go.Figure()
            PlotlyCircuitDiagram._add_center_annotation(
                fig, f"Global phase: {circuit.global_phase}"
            )
            PlotlyCircuitDiagram._configure_empty_figure(fig, width=340, height=140)
            return fig

        layout = PlotlyCircuitDiagram._compute_layout(circuit)
        return PlotlyCircuitDiagram._render_layout(layout, device_metadata, go)

    @staticmethod
    def _get_plotly() -> Any:
        try:
            import plotly.graph_objects as go  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "Plotly is required for PlotlyCircuitDiagram. Install it with "
                "`pip install amazon-braket-sdk[interactive]` or `pip install plotly`."
            ) from exc
        return go

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
        device_metadata: Mapping[str, Any] | None = None,
        plotly_module: Any | None = None,
    ) -> go.Figure:
        verbatim_ranges = cls._find_verbatim_ranges(layout)
        return cls._render_base_layout(
            layout,
            device_metadata,
            plotly_module=plotly_module,
            verbatim_ranges=verbatim_ranges,
        )

    @classmethod
    def _render_base_layout(
        cls,
        layout: CircuitLayout,
        device_metadata: Mapping[str, Any] | None = None,
        *,
        plotly_module: Any | None = None,
        verbatim_ranges: list[tuple[int, int]] | None = None,
    ) -> go.Figure:
        go = plotly_module or cls._get_plotly()
        fig = go.Figure()
        n_rows = max(layout.num_qubits, 1)

        col_x, col_w = cls._compute_column_x(layout)
        total_width = sum(col_w)
        left_wire = col_x[0] - col_w[0] / 2 - cls.WIRE_EXTEND
        right_wire = total_width + cls.WIRE_EXTEND

        label_y_top = cls.ROW_HEIGHT * 0.8
        label_y_bottom = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.8

        cls._draw_qubit_wires(fig, layout, left_wire, right_wire)
        cls._draw_moment_labels(fig, layout, col_x, label_y_top, label_y_bottom)
        trace_groups = cls._draw_elements(
            fig,
            layout,
            col_x,
            device_metadata,
            plotly_module=go,
            verbatim_ranges=verbatim_ranges or [],
        )

        footer_lines = cls._build_footer_lines(layout)
        if footer_lines:
            cls._draw_footer(fig, footer_lines, left_wire, label_y_bottom)

        cls._configure_axes(fig, left_wire, right_wire, label_y_top, label_y_bottom, footer_lines)
        cls._add_verbatim_toggles(fig, trace_groups, col_x, left_wire, right_wire)
        return fig

    @classmethod
    def _find_verbatim_ranges(cls, layout: CircuitLayout) -> list[tuple[int, int]]:
        starts = {
            elem.col
            for elem in layout.elements
            if isinstance(elem, GateBox) and elem.label == "StartVerbatim"
        }
        ends = {
            elem.col
            for elem in layout.elements
            if isinstance(elem, GateBox) and elem.label == "EndVerbatim"
        }

        ranges: list[tuple[int, int]] = []
        outer_start: int | None = None
        depth = 0
        for col in range(layout.num_moments):
            if col in starts:
                if depth == 0:
                    outer_start = col
                depth += 1
            if col in ends and depth:
                depth -= 1
                if depth == 0 and outer_start is not None:
                    ranges.append((outer_start, col))
                    outer_start = None
        return ranges

    @classmethod
    def _build_collapsed_verbatim_elements(
        cls, layout: CircuitLayout, start: int, end: int, col: int
    ) -> list:
        rows: set[int] = set()
        for elem in layout.elements:
            if start <= elem.col <= end:
                rows.update(cls._element_rows(elem))

        if not rows:
            rows = set(range(layout.num_qubits))

        elements: list = [GateBox(col=col, row=row, label="Verbatim") for row in sorted(rows)]
        if len(rows) > 1:
            elements.append(Connection(col=col, row_start=min(rows), row_end=max(rows)))
        return elements

    @staticmethod
    def _element_rows(elem: object) -> set[int]:
        if isinstance(elem, Connection):
            return set(range(elem.row_start, elem.row_end + 1))
        if isinstance(elem, GateBox | ControlDot | SwapMarker | BarrierMarker):
            return {elem.row}
        return set()

    @staticmethod
    def _is_in_verbatim_range(col: int, verbatim_ranges: list[tuple[int, int]]) -> bool:
        return any(start <= col <= end for start, end in verbatim_ranges)

    @classmethod
    def _draw_qubit_wires(
        cls, fig: go.Figure, layout: CircuitLayout, left_wire: float, right_wire: float
    ) -> None:
        for row_idx, label in enumerate(layout.qubit_labels):
            y = -row_idx * cls.ROW_HEIGHT
            fig.add_shape(
                type="line",
                x0=left_wire,
                x1=right_wire,
                y0=y,
                y1=y,
                line={"color": cls.WIRE_COLOR, "width": cls.WIRE_WIDTH},
                layer="below",
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
        fig: go.Figure,
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
        fig: go.Figure,
        layout: CircuitLayout,
        col_x: list[float],
        device_metadata: Mapping[str, Any] | None = None,
        *,
        plotly_module: Any,
        verbatim_ranges: list[tuple[int, int]],
    ) -> list[_VerbatimTraceGroup]:
        if not verbatim_ranges:
            cls._draw_element_batch(
                fig,
                layout,
                col_x,
                layout.elements,
                device_metadata,
                plotly_module=plotly_module,
                visible=True,
            )
            return []

        always_elements = [
            elem
            for elem in layout.elements
            if not cls._is_in_verbatim_range(elem.col, verbatim_ranges)
        ]
        cls._draw_element_batch(
            fig,
            layout,
            col_x,
            always_elements,
            device_metadata,
            plotly_module=plotly_module,
            visible=True,
        )

        trace_groups: list[_VerbatimTraceGroup] = []
        for start, end in verbatim_ranges:
            expanded_elements = [elem for elem in layout.elements if start <= elem.col <= end]
            expanded_indices = cls._draw_element_batch(
                fig,
                layout,
                col_x,
                expanded_elements,
                device_metadata,
                plotly_module=plotly_module,
                visible=False,
            )

            collapsed_col_x = col_x.copy()
            collapsed_col_x[start] = (col_x[start] + col_x[end]) / 2
            collapsed_elements = cls._build_collapsed_verbatim_elements(
                layout,
                start,
                end,
                start,
            )
            collapsed_indices = cls._draw_element_batch(
                fig,
                layout,
                collapsed_col_x,
                collapsed_elements,
                device_metadata,
                plotly_module=plotly_module,
                visible=True,
            )
            trace_groups.append(
                _VerbatimTraceGroup(
                    start=start,
                    end=end,
                    collapsed_indices=collapsed_indices,
                    expanded_indices=expanded_indices,
                )
            )
        return trace_groups

    @classmethod
    def _draw_element_batch(
        cls,
        fig: go.Figure,
        layout: CircuitLayout,
        col_x: list[float],
        elements: list[object],
        device_metadata: Mapping[str, Any] | None = None,
        *,
        plotly_module: Any,
        visible: bool,
    ) -> list[int]:
        parts = _TraceParts()
        for elem in elements:
            cls._collect_element_trace_parts(parts, elem, layout, col_x, device_metadata)

        return cls._flush_element_traces(
            fig,
            plotly_module,
            visible=visible,
            parts=parts,
        )

    @classmethod
    def _collect_element_trace_parts(
        cls,
        parts: _TraceParts,
        elem: object,
        layout: CircuitLayout,
        col_x: list[float],
        device_metadata: Mapping[str, Any] | None,
    ) -> None:
        if isinstance(elem, GateBox):
            cls._collect_gate_box_trace_parts(parts, elem, layout, col_x, device_metadata)
        elif isinstance(elem, ControlDot):
            cls._collect_control_trace_parts(parts, elem, layout, col_x)
        elif isinstance(elem, SwapMarker):
            x = col_x[elem.col]
            y = -elem.row * cls.ROW_HEIGHT
            parts.swap_x.append(x)
            parts.swap_y.append(y)
            parts.swap_hover.append(f"SWAP<br>Qubit: {layout.qubit_labels[elem.row]}")
        elif isinstance(elem, Connection):
            x = col_x[elem.col]
            y_start = -elem.row_start * cls.ROW_HEIGHT
            y_end = -elem.row_end * cls.ROW_HEIGHT
            parts.connection_x.extend([x, x, None])
            parts.connection_y.extend([y_start, y_end, None])
            parts.hover_x.append(x)
            parts.hover_y.append((y_start + y_end) / 2)
            parts.hover_text.append(
                "Connection"
                f"<br>From: {layout.qubit_labels[elem.row_start]}"
                f"<br>To: {layout.qubit_labels[elem.row_end]}"
            )
        elif isinstance(elem, BarrierMarker):
            x = col_x[elem.col]
            y = -elem.row * cls.ROW_HEIGHT
            cls._append_rect(
                parts.barrier_x,
                parts.barrier_y,
                x,
                y,
                cls.BARRIER_WIDTH,
                cls.ROW_HEIGHT * cls.BARRIER_HEIGHT_FRAC,
            )
            parts.barrier_text_x.append(x)
            parts.barrier_text_y.append(y)
            parts.hover_x.append(x)
            parts.hover_y.append(y)
            parts.hover_text.append(f"Barrier<br>Qubit: {layout.qubit_labels[elem.row]}")

    @classmethod
    def _collect_gate_box_trace_parts(
        cls,
        parts: _TraceParts,
        elem: GateBox,
        layout: CircuitLayout,
        col_x: list[float],
        device_metadata: Mapping[str, Any] | None,
    ) -> None:
        x = col_x[elem.col]
        y = -elem.row * cls.ROW_HEIGHT
        cls._append_rect(
            parts.gate_x,
            parts.gate_y,
            x,
            y,
            cls._gate_box_width(elem.label),
            cls.GATE_BOX_HEIGHT,
        )
        parts.gate_text_x.append(x)
        parts.gate_text_y.append(y)
        parts.gate_text.append(elem.label)
        parts.hover_x.append(x)
        parts.hover_y.append(y)
        parts.hover_text.append(
            cls._gate_hover_text(
                elem.label,
                layout.qubit_labels[elem.row],
                metadata_key=elem.metadata_key,
                parameter_text=elem.parameter_text,
                device_metadata=device_metadata,
            )
        )

    @classmethod
    def _collect_control_trace_parts(
        cls,
        parts: _TraceParts,
        elem: ControlDot,
        layout: CircuitLayout,
        col_x: list[float],
    ) -> None:
        x = col_x[elem.col]
        y = -elem.row * cls.ROW_HEIGHT
        text = (
            f"{'Control' if elem.filled else 'Anti-control'}"
            f"<br>Qubit: {layout.qubit_labels[elem.row]}"
        )
        if elem.filled:
            parts.filled_control_x.append(x)
            parts.filled_control_y.append(y)
            parts.filled_control_hover.append(text)
        else:
            parts.open_control_x.append(x)
            parts.open_control_y.append(y)
            parts.open_control_hover.append(text)

    @staticmethod
    def _append_rect(
        x_values: list[float | None],
        y_values: list[float | None],
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        x0 = x - width / 2
        x1 = x + width / 2
        y0 = y - height / 2
        y1 = y + height / 2
        x_values.extend([x0, x1, x1, x0, x0, None])
        y_values.extend([y0, y0, y1, y1, y0, None])

    @classmethod
    def _flush_element_traces(
        cls,
        fig: go.Figure,
        plotly_module: Any,
        *,
        visible: bool,
        parts: _TraceParts,
    ) -> list[int]:
        trace_indices: list[int] = []
        if parts.connection_x:
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=parts.connection_x,
                        y=parts.connection_y,
                        mode="lines",
                        line={"color": cls.CONNECTION_COLOR, "width": cls.CONNECTION_WIDTH},
                        hoverinfo="skip",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        if parts.gate_x:
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=parts.gate_x,
                        y=parts.gate_y,
                        mode="lines",
                        fill="toself",
                        fillcolor=cls.GATE_FILL_COLOR,
                        line={"color": cls.GATE_EDGE_COLOR, "width": 1.2},
                        hoverinfo="skip",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        if parts.barrier_x:
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=parts.barrier_x,
                        y=parts.barrier_y,
                        mode="lines",
                        fill="toself",
                        fillcolor=cls.BARRIER_FILL_COLOR,
                        line={"color": cls.BARRIER_COLOR, "width": 1},
                        hoverinfo="skip",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        trace_indices.extend(
            cls._add_control_traces(
                fig,
                plotly_module,
                visible=visible,
                parts=parts,
            )
        )
        if parts.swap_x:
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=parts.swap_x,
                        y=parts.swap_y,
                        text=parts.swap_hover,
                        mode="markers",
                        marker={
                            "symbol": "x",
                            "size": cls.SWAP_MARKER_SIZE,
                            "color": cls.CONNECTION_COLOR,
                            "line": {"width": 2},
                        },
                        hovertemplate="%{text}<extra></extra>",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        if parts.gate_text:
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=parts.gate_text_x,
                        y=parts.gate_text_y,
                        text=parts.gate_text,
                        mode="text",
                        textfont={
                            "family": "monospace",
                            "size": cls.GATE_FONT_SIZE,
                            "color": cls.GATE_TEXT_COLOR,
                        },
                        hoverinfo="skip",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        if parts.barrier_text_x:
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=parts.barrier_text_x,
                        y=parts.barrier_text_y,
                        text=["/"] * len(parts.barrier_text_x),
                        mode="text",
                        textfont={"size": cls.GATE_FONT_SIZE, "color": cls.BARRIER_COLOR},
                        hoverinfo="skip",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        if parts.hover_x:
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=parts.hover_x,
                        y=parts.hover_y,
                        text=parts.hover_text,
                        mode="markers",
                        marker={"size": 24, "color": "rgba(0,0,0,0)"},
                        hovertemplate="%{text}<extra></extra>",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        return trace_indices

    @classmethod
    def _add_control_traces(
        cls,
        fig: go.Figure,
        plotly_module: Any,
        *,
        visible: bool,
        parts: _TraceParts,
    ) -> list[int]:
        trace_indices: list[int] = []
        for x_values, y_values, hover_values, fill in (
            (parts.filled_control_x, parts.filled_control_y, parts.filled_control_hover, "black"),
            (parts.open_control_x, parts.open_control_y, parts.open_control_hover, "white"),
        ):
            if not x_values:
                continue
            trace_indices.append(
                cls._add_trace(
                    fig,
                    plotly_module.Scatter(
                        x=x_values,
                        y=y_values,
                        text=hover_values,
                        mode="markers",
                        marker={
                            "symbol": "circle",
                            "size": cls.CONTROL_DOT_SIZE,
                            "color": fill,
                            "line": {"color": "black", "width": 2},
                        },
                        hovertemplate="%{text}<extra></extra>",
                        showlegend=False,
                        visible=visible,
                    ),
                )
            )
        return trace_indices

    @staticmethod
    def _add_trace(fig: go.Figure, trace: Any) -> int:
        fig.add_trace(trace)
        return len(fig.data) - 1

    @classmethod
    def _add_verbatim_toggles(
        cls,
        fig: go.Figure,
        trace_groups: list[_VerbatimTraceGroup],
        col_x: list[float],
        left_wire: float,
        right_wire: float,
    ) -> None:
        if not trace_groups:
            return

        x_min = left_wire - 1.5
        x_max = right_wire + 0.5
        x_span = x_max - x_min
        updatemenus = []
        for index, trace_group in enumerate(trace_groups, start=1):
            trace_indices = trace_group.collapsed_indices + trace_group.expanded_indices
            collapsed_visibility = [True] * len(trace_group.collapsed_indices) + [False] * len(
                trace_group.expanded_indices
            )
            expanded_visibility = [False] * len(trace_group.collapsed_indices) + [True] * len(
                trace_group.expanded_indices
            )
            group_center = (col_x[trace_group.start] + col_x[trace_group.end]) / 2
            updatemenus.append({
                "type": "buttons",
                "direction": "right",
                "showactive": True,
                "active": 0,
                "x": min(max((group_center - x_min) / x_span, 0), 1),
                "xanchor": "center",
                "y": 1.08 + (index - 1) * 0.08,
                "yanchor": "top",
                "buttons": [
                    {
                        "label": f"Collapse verbatim {index}",
                        "method": "restyle",
                        "args": [{"visible": collapsed_visibility}, trace_indices],
                    },
                    {
                        "label": f"Expand verbatim {index}",
                        "method": "restyle",
                        "args": [{"visible": expanded_visibility}, trace_indices],
                    },
                ],
            })
        fig.update_layout(updatemenus=updatemenus)

    @classmethod
    def _gate_hover_text(
        cls,
        label: str,
        qubit_label: str,
        *,
        metadata_key: str | None = None,
        parameter_text: str | None = None,
        device_metadata: Mapping[str, Any] | None = None,
    ) -> str:
        if parameter_text is None:
            parameter_text = cls._parameter_text_from_label(label) or "None"

        return (
            f"Gate: {label}"
            f"<br>Qubit: {qubit_label}"
            f"<br>Parameters: {parameter_text}"
            "<br>Device metadata: "
            f"{cls._device_metadata_text(label, metadata_key, device_metadata)}"
        )

    @classmethod
    def _device_metadata_text(
        cls,
        label: str,
        metadata_key: str | None,
        device_metadata: Mapping[str, Any] | None,
    ) -> str:
        if not device_metadata:
            return "N/A (not attached)"

        label_name, _, _ = label.partition("(")
        for key in (metadata_key, label, label_name):
            if key and key in device_metadata:
                return cls._format_device_metadata(device_metadata[key])
        return "N/A (not attached)"

    @staticmethod
    def _format_device_metadata(metadata: Any) -> str:
        if metadata is None:
            return "N/A (not attached)"
        if isinstance(metadata, Mapping):
            if not metadata:
                return "N/A (not attached)"
            return ", ".join(f"{key}: {value}" for key, value in metadata.items())
        return str(metadata)

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
        cls, fig: go.Figure, footer_lines: list[str], left_wire: float, label_y_bottom: float
    ) -> None:
        footer_y = label_y_bottom - cls.ROW_HEIGHT * 0.7
        for idx, line in enumerate(footer_lines):
            fig.add_annotation(
                x=left_wire,
                y=footer_y - idx * cls.ROW_HEIGHT * 0.5,
                text=line,
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font={"family": "monospace", "size": cls.FOOTER_FONT_SIZE, "color": "#333333"},
            )

    @classmethod
    def _configure_axes(
        cls,
        fig: go.Figure,
        left_wire: float,
        right_wire: float,
        label_y_top: float,
        label_y_bottom: float,
        footer_lines: list[str],
    ) -> None:
        y_top = label_y_top + 0.4
        y_bottom = label_y_bottom - 0.4
        if footer_lines:
            y_bottom -= len(footer_lines) * cls.ROW_HEIGHT * 0.5

        width = max(500, int((right_wire - left_wire + 2) * 95))
        height = max(220, int((y_top - y_bottom + 1) * 95))
        fig.update_layout(
            width=width,
            height=height,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="closest",
            showlegend=False,
        )
        fig.update_xaxes(
            range=[left_wire - 1.5, right_wire + 0.5],
            visible=False,
            scaleanchor="y",
            scaleratio=1,
        )
        fig.update_yaxes(range=[y_bottom, y_top], visible=False)

    @staticmethod
    def _add_center_annotation(fig: go.Figure, text: str) -> None:
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=text,
            showarrow=False,
            font={"size": 14},
        )

    @staticmethod
    def _configure_empty_figure(fig: go.Figure, width: int, height: int) -> None:
        fig.update_layout(
            width=width,
            height=height,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis={"visible": False},
            yaxis={"visible": False},
            showlegend=False,
        )
