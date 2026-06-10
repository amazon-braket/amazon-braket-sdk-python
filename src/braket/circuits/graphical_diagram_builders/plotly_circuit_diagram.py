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
from typing import TYPE_CHECKING, Any

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


class PlotlyCircuitDiagram(GraphicalCircuitDiagram):
    """Renders circuit diagrams as interactive Plotly figures.

    Examples:
        >>> from braket.circuits import Circuit
        >>> fig = Circuit().h(0).cnot(0, 1).show("interactive")

    The returned figure includes hover tooltips and, for verbatim boxes, buttons to switch
    between collapsed and expanded views.

    The collapse path is intentionally range-based: the renderer detects nestable column
    ranges, draws a synthetic collapsed layout, and keeps the expanded layout behind the same
    toggle. Future ``box`` or ``scope`` circuit structures can reuse this path by contributing
    their own ranges and collapsed labels once the SDK exposes them in the layout.
    The current verbatim control is one global ``updatemenus`` toggle for the figure.
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
            >>> fig = Circuit().h(0).cnot(0, 1).show("interactive")
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
        return PlotlyCircuitDiagram._render_layout(layout, device_metadata)

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
    ) -> go.Figure:
        verbatim_ranges = cls._find_verbatim_ranges(layout)
        if verbatim_ranges:
            collapsed_layout = cls._collapse_verbatim_layout(layout, verbatim_ranges)
            collapsed_fig = cls._render_base_layout(collapsed_layout, device_metadata)
            expanded_fig = cls._render_base_layout(layout, device_metadata)
            return cls._add_verbatim_toggle(collapsed_fig, expanded_fig)
        return cls._render_base_layout(layout, device_metadata)

    @classmethod
    def _render_base_layout(
        cls,
        layout: CircuitLayout,
        device_metadata: Mapping[str, Any] | None = None,
    ) -> go.Figure:
        go = cls._get_plotly()
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
        cls._draw_elements(fig, layout, col_x, device_metadata)

        footer_lines = cls._build_footer_lines(layout)
        if footer_lines:
            cls._draw_footer(fig, footer_lines, left_wire, label_y_bottom)

        cls._configure_axes(fig, left_wire, right_wire, label_y_top, label_y_bottom, footer_lines)
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
    def _collapse_verbatim_layout(
        cls, layout: CircuitLayout, verbatim_ranges: list[tuple[int, int]]
    ) -> CircuitLayout:
        col_map: dict[int, int] = {}
        collapsed_elements: list = []
        collapsed_moment_labels: list[str] = []
        new_col = 0
        col = 0
        while col < layout.num_moments:
            verbatim_range = next(
                ((start, end) for start, end in verbatim_ranges if start == col),
                None,
            )
            if verbatim_range:
                start, end = verbatim_range
                for source_col in range(start, end + 1):
                    col_map[source_col] = new_col
                collapsed_moment_labels.append("Verbatim")
                collapsed_elements.extend(
                    cls._build_collapsed_verbatim_elements(layout, start, end, new_col)
                )
                new_col += 1
                col = end + 1
            else:
                col_map[col] = new_col
                collapsed_moment_labels.append(layout.moment_labels[col])
                new_col += 1
                col += 1

        for elem in layout.elements:
            if cls._is_in_verbatim_range(elem.col, verbatim_ranges):
                continue
            collapsed_elements.append(cls._clone_element_with_col(elem, col_map[elem.col]))

        return CircuitLayout(
            num_qubits=layout.num_qubits,
            num_moments=new_col,
            qubit_labels=layout.qubit_labels,
            moment_labels=collapsed_moment_labels,
            elements=collapsed_elements,
            global_phase=layout.global_phase,
            additional_result_types=layout.additional_result_types,
            unassigned_parameters=layout.unassigned_parameters,
        )

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

    @staticmethod
    def _clone_element_with_col(elem: object, col: int) -> object:
        if isinstance(elem, GateBox):
            return GateBox(
                col=col,
                row=elem.row,
                label=elem.label,
                metadata_key=elem.metadata_key,
                parameter_text=elem.parameter_text,
            )
        if isinstance(elem, ControlDot):
            return ControlDot(col=col, row=elem.row, filled=elem.filled)
        if isinstance(elem, SwapMarker):
            return SwapMarker(col=col, row=elem.row)
        if isinstance(elem, Connection):
            return Connection(col=col, row_start=elem.row_start, row_end=elem.row_end)
        if isinstance(elem, BarrierMarker):
            return BarrierMarker(col=col, row=elem.row)
        return elem

    @classmethod
    def _add_verbatim_toggle(cls, collapsed_fig: go.Figure, expanded_fig: go.Figure) -> go.Figure:
        collapsed_trace_count = len(collapsed_fig.data)
        expanded_trace_count = len(expanded_fig.data)

        for trace in expanded_fig.data:
            trace.visible = False
            collapsed_fig.add_trace(trace)

        collapsed_shapes = cls._visible_layout_items(collapsed_fig.layout.shapes, visible=True)
        expanded_shapes = cls._visible_layout_items(expanded_fig.layout.shapes, visible=False)
        collapsed_annotations = cls._visible_layout_items(
            collapsed_fig.layout.annotations, visible=True
        )
        expanded_annotations = cls._visible_layout_items(
            expanded_fig.layout.annotations, visible=False
        )
        collapsed_fig.update_layout(
            shapes=collapsed_shapes + expanded_shapes,
            annotations=collapsed_annotations + expanded_annotations,
            updatemenus=[
                {
                    "type": "buttons",
                    "direction": "right",
                    "x": 1,
                    "xanchor": "right",
                    "y": 1.08,
                    "yanchor": "top",
                    "buttons": [
                        {
                            "label": "Collapse verbatim",
                            "method": "update",
                            "args": [
                                {
                                    "visible": [True] * collapsed_trace_count
                                    + [False] * expanded_trace_count
                                },
                                cls._verbatim_layout_update(
                                    collapsed_fig,
                                    expanded_fig,
                                    collapsed_shapes,
                                    expanded_shapes,
                                    collapsed_annotations,
                                    expanded_annotations,
                                    expand=False,
                                ),
                            ],
                        },
                        {
                            "label": "Expand verbatim",
                            "method": "update",
                            "args": [
                                {
                                    "visible": [False] * collapsed_trace_count
                                    + [True] * expanded_trace_count
                                },
                                cls._verbatim_layout_update(
                                    collapsed_fig,
                                    expanded_fig,
                                    collapsed_shapes,
                                    expanded_shapes,
                                    collapsed_annotations,
                                    expanded_annotations,
                                    expand=True,
                                ),
                            ],
                        },
                    ],
                }
            ],
        )
        return collapsed_fig

    @staticmethod
    def _visible_layout_items(items: tuple, visible: bool) -> list[dict]:
        visible_items = []
        for item in items:
            item_dict = item.to_plotly_json()
            item_dict["visible"] = visible
            visible_items.append(item_dict)
        return visible_items

    @staticmethod
    def _verbatim_layout_update(
        collapsed_fig: go.Figure,
        expanded_fig: go.Figure,
        collapsed_shapes: list[dict],
        expanded_shapes: list[dict],
        collapsed_annotations: list[dict],
        expanded_annotations: list[dict],
        *,
        expand: bool,
    ) -> dict:
        active_fig = expanded_fig if expand else collapsed_fig
        return {
            "shapes": [{**shape, "visible": not expand} for shape in collapsed_shapes]
            + [{**shape, "visible": expand} for shape in expanded_shapes],
            "annotations": [
                {**annotation, "visible": not expand} for annotation in collapsed_annotations
            ]
            + [{**annotation, "visible": expand} for annotation in expanded_annotations],
            "xaxis": active_fig.layout.xaxis.to_plotly_json(),
            "yaxis": active_fig.layout.yaxis.to_plotly_json(),
            "width": active_fig.layout.width,
            "height": active_fig.layout.height,
        }

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
    ) -> None:
        for elem in layout.elements:
            if isinstance(elem, GateBox):
                cls._draw_gate_box(fig, elem, col_x[elem.col], layout, device_metadata)
            elif isinstance(elem, ControlDot):
                cls._draw_control_dot(fig, elem, col_x[elem.col], layout)
            elif isinstance(elem, SwapMarker):
                cls._draw_swap_marker(fig, elem, col_x[elem.col], layout)
            elif isinstance(elem, Connection):
                cls._draw_connection(fig, elem, col_x[elem.col], layout)
            elif isinstance(elem, BarrierMarker):
                cls._draw_barrier(fig, elem, col_x[elem.col], layout)

    @classmethod
    def _draw_gate_box(
        cls,
        fig: go.Figure,
        elem: GateBox,
        x: float,
        layout: CircuitLayout,
        device_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        box_width = cls._gate_box_width(elem.label)
        fig.add_shape(
            type="rect",
            x0=x - box_width / 2,
            x1=x + box_width / 2,
            y0=y - cls.GATE_BOX_HEIGHT / 2,
            y1=y + cls.GATE_BOX_HEIGHT / 2,
            fillcolor=cls.GATE_FILL_COLOR,
            line={"color": cls.GATE_EDGE_COLOR, "width": 1.2},
            layer="above",
        )
        fig.add_annotation(
            x=x,
            y=y,
            text=elem.label,
            showarrow=False,
            xanchor="center",
            yanchor="middle",
            font={
                "family": "monospace",
                "size": cls.GATE_FONT_SIZE,
                "color": cls.GATE_TEXT_COLOR,
            },
        )
        cls._add_hover_marker(
            fig,
            x,
            y,
            cls._gate_hover_text(
                elem.label,
                layout.qubit_labels[elem.row],
                metadata_key=elem.metadata_key,
                parameter_text=elem.parameter_text,
                device_metadata=device_metadata,
            ),
        )

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
    def _draw_control_dot(
        cls, fig: go.Figure, elem: ControlDot, x: float, layout: CircuitLayout
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        fill = "black" if elem.filled else "white"
        fig.add_trace(
            cls._get_plotly().Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={
                    "symbol": "circle",
                    "size": cls.CONTROL_DOT_SIZE,
                    "color": fill,
                    "line": {"color": "black", "width": 2},
                },
                hovertemplate=(
                    f"{'Control' if elem.filled else 'Anti-control'}"
                    f"<br>Qubit: {layout.qubit_labels[elem.row]}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    @classmethod
    def _draw_swap_marker(
        cls, fig: go.Figure, elem: SwapMarker, x: float, layout: CircuitLayout
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        fig.add_trace(
            cls._get_plotly().Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={
                    "symbol": "x",
                    "size": cls.SWAP_MARKER_SIZE,
                    "color": cls.CONNECTION_COLOR,
                    "line": {"width": 2},
                },
                hovertemplate=f"SWAP<br>Qubit: {layout.qubit_labels[elem.row]}<extra></extra>",
                showlegend=False,
            )
        )

    @classmethod
    def _draw_connection(
        cls, fig: go.Figure, elem: Connection, x: float, layout: CircuitLayout
    ) -> None:
        y_start = -elem.row_start * cls.ROW_HEIGHT
        y_end = -elem.row_end * cls.ROW_HEIGHT
        fig.add_shape(
            type="line",
            x0=x,
            x1=x,
            y0=y_start,
            y1=y_end,
            line={"color": cls.CONNECTION_COLOR, "width": cls.CONNECTION_WIDTH},
        )
        cls._add_hover_marker(
            fig,
            x,
            (y_start + y_end) / 2,
            (
                "Connection"
                f"<br>From: {layout.qubit_labels[elem.row_start]}"
                f"<br>To: {layout.qubit_labels[elem.row_end]}"
            ),
        )

    @classmethod
    def _draw_barrier(
        cls, fig: go.Figure, elem: BarrierMarker, x: float, layout: CircuitLayout
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        half_h = cls.ROW_HEIGHT * cls.BARRIER_HEIGHT_FRAC / 2
        half_w = cls.BARRIER_WIDTH / 2
        fig.add_shape(
            type="rect",
            x0=x - half_w,
            x1=x + half_w,
            y0=y - half_h,
            y1=y + half_h,
            fillcolor=cls.BARRIER_FILL_COLOR,
            line={"color": cls.BARRIER_COLOR, "width": 1},
        )
        fig.add_annotation(
            x=x,
            y=y,
            text="/",
            showarrow=False,
            xanchor="center",
            yanchor="middle",
            font={"size": cls.GATE_FONT_SIZE, "color": cls.BARRIER_COLOR},
        )
        cls._add_hover_marker(fig, x, y, f"Barrier<br>Qubit: {layout.qubit_labels[elem.row]}")

    @classmethod
    def _add_hover_marker(cls, fig: go.Figure, x: float, y: float, text: str) -> None:
        fig.add_trace(
            cls._get_plotly().Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker={"size": 24, "color": "rgba(0,0,0,0)"},
                hovertemplate=f"{text}<extra></extra>",
                showlegend=False,
            )
        )

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
