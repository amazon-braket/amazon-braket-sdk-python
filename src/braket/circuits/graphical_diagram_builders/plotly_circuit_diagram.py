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

"""Interactive Plotly-based quantum circuit diagram renderer.

This module provides :class:`PlotlyCircuitDiagram`, a sibling to
:class:`~braket.circuits.graphical_diagram_builders.matplotlib_circuit_diagram.MatplotlibCircuitDiagram`
that renders a :class:`~braket.circuits.circuit.Circuit` as an interactive
``plotly.graph_objects.FigureWidget``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import braket.circuits.circuit as cir
from braket.circuits.compiler_directive import CompilerDirective
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
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType

if TYPE_CHECKING:
    pass

try:
    import plotly.graph_objects as go
    _PLOTLY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PLOTLY_AVAILABLE = False

try:
    from plotly.graph_objects import FigureWidget as _FigureWidget
    # plotly >= 6 makes FigureWidget importable but raises on construction
    # without anywidget. Probe it here so we fall back gracefully.
    _FigureWidget()
    _FIGUREWIDGET_AVAILABLE = True
except Exception:  # pragma: no cover
    _FIGUREWIDGET_AVAILABLE = False


@dataclass
class _VerbatimBlock:
    col_start: int
    col_end: int
    expanded: bool = False

@dataclass
class _RenderState:
    layout: CircuitLayout
    verbatim_blocks: list[_VerbatimBlock] = field(default_factory=list)
    device_metadata: dict[str, str] = field(default_factory=dict)


class PlotlyCircuitDiagram(GraphicalCircuitDiagram):
    """Renders circuit diagrams as interactive Plotly FigureWidgets.

    Note:
        Plotly must be installed.  Use::

            pip install "amazon-braket-sdk[interactive]"
    """
    COL_WIDTH: float = 1.6
    COL_GAP: float = 0.2
    ROW_HEIGHT: float = 1.0
    WIRE_EXTEND: float = 0.6

    GATE_BOX_HEIGHT: float = 0.55
    GATE_BOX_MIN_WIDTH: float = 0.7
    GATE_BOX_PADDING: float = 0.35
    GATE_FONT_SIZE: int = 13

    FOOTER_COLOR: str = "#555555"
    @classmethod
    def _gate_box_width(cls, label: str) -> float:
        char_width = cls.GATE_FONT_SIZE * 0.011
        return max(cls.GATE_BOX_MIN_WIDTH, len(label) * char_width + cls.GATE_BOX_PADDING)

    @classmethod
    def _compute_column_x(
        cls, layout: CircuitLayout, hidden_cols: set[int]
    ) -> tuple[list[float], list[float]]:
        """Return ``(centers, widths)`` for each column, skipping hidden ones."""
        n_cols = max(layout.num_moments, 1)
        widths = [cls.COL_WIDTH] * n_cols
        for elem in layout.elements:
            if isinstance(elem, GateBox):
                widths[elem.col] = max(
                    widths[elem.col], cls._gate_box_width(elem.label) + cls.COL_GAP
                )
        centers: list[float] = []
        cursor = 0.0
        for col_idx, w in enumerate(widths):
            if col_idx in hidden_cols:
                centers.append(None)  # placeholder; not rendered
            else:
                centers.append(cursor + w / 2)
                cursor += w
        return centers, widths

    @staticmethod
    def build_diagram(
        circuit: cir.Circuit,
        device_metadata: dict[str, str] | None = None,
    ) -> Any:
        """Build an interactive Plotly Figure for *circuit*."""
        if not _PLOTLY_AVAILABLE:
            raise ImportError(
                "Plotly is required for interactive visualization. "
                "Install it with: pip install 'amazon-braket-sdk[interactive]'"
            )

        FigCls = _FigureWidget if _FIGUREWIDGET_AVAILABLE else go.Figure

        if not circuit.instructions:
            fig = FigCls()
            fig.add_annotation(
                text="(empty circuit)",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font={"size": 16, "color": "#555555"},
            )
            fig.update_layout(
                xaxis={"visible": False}, yaxis={"visible": False},
                plot_bgcolor="white", paper_bgcolor="white",
                width=300, height=150,
            )
            return fig

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            fig = FigCls()
            fig.add_annotation(
                text=f"Global phase: {circuit.global_phase}",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font={"size": 14, "color": "#555555"},
            )
            fig.update_layout(
                xaxis={"visible": False}, yaxis={"visible": False},
                plot_bgcolor="white", paper_bgcolor="white",
                width=400, height=150,
            )
            return fig

        layout = PlotlyCircuitDiagram._compute_layout(circuit)
        verbatim_blocks = PlotlyCircuitDiagram._identify_blocks(circuit, layout)
        state = _RenderState(
            layout=layout,
            verbatim_blocks=verbatim_blocks,
            device_metadata=device_metadata or {},
        )
        return PlotlyCircuitDiagram._build_figure(state)

    @staticmethod
    def _identify_blocks(
        circuit: cir.Circuit, layout: CircuitLayout  # noqa: ARG004
    ) -> list[_VerbatimBlock]:
        blocks: list[_VerbatimBlock] = []
        open_start: int | None = None
        col = 0

        from braket.circuits.graphical_diagram_builders.graphical_diagram_utils import (
            _group_items,
        )
        circuit_qubits = circuit.qubits
        circuit_qubits.sort()

        time_slices = circuit.moments.time_slices()
        for _time, instructions in time_slices.items():
            from braket.circuits.graphical_diagram_builders.graphical_diagram_utils import (
                _has_global_phase,
            )
            groupings = _group_items(circuit_qubits, instructions)
            for grouping in groupings:
                for item in grouping[1]:
                    if isinstance(item, Instruction) and isinstance(
                        item.operator, CompilerDirective
                    ):
                        name = item.operator.name
                        if name == "StartVerbatimBox":
                            open_start = col
                        elif name == "EndVerbatimBox" and open_start is not None:
                            blocks.append(_VerbatimBlock(col_start=open_start, col_end=col))
                            open_start = None
                col += 1

        return blocks

    @classmethod
    def _build_figure(cls, state: _RenderState) -> Any:
        layout = state.layout
        n_rows = max(layout.num_qubits, 1)

        hidden_cols: set[int] = set()
        for block in state.verbatim_blocks:
            if not block.expanded:
                # hide all interior columns (keep start+end as sentinel)
                for c in range(block.col_start + 1, block.col_end):
                    hidden_cols.add(c)

        col_x, col_w = cls._compute_column_x(layout, hidden_cols)

        visible_xs = [x for x in col_x if x is not None]
        total_width = sum(w for idx, w in enumerate(col_w) if idx not in hidden_cols)

        left_wire = (visible_xs[0] if visible_xs else 0) - col_w[0] / 2 - cls.WIRE_EXTEND
        right_wire = left_wire + total_width + cls.WIRE_EXTEND * 2

        fig_width = max(480, int((right_wire - left_wire + 3) * 80))
        fig_height = max(200, int(n_rows * cls.ROW_HEIGHT * 80 + 160))

        shapes: list[dict] = []
        traces: list[Any] = []

        cls._add_qubit_wires(shapes, traces, layout, left_wire, right_wire)
        cls._add_elements(
            shapes, traces, layout, col_x, col_w, hidden_cols, state
        )
        cls._add_verbatim_blocks(shapes, traces, layout, col_x, col_w, state)

        footer_text = cls._build_footer_text(layout)

        FigCls = _FigureWidget if _FIGUREWIDGET_AVAILABLE else go.Figure
        fig = FigCls(data=traces)
        fig.update_layout(
            shapes=shapes,
            xaxis={
                "range": [left_wire - 1.0, right_wire + 0.5],
                "visible": False,
                "fixedrange": False,
            },
            yaxis={
                "range": [-(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.9,
                           cls.ROW_HEIGHT * 0.9],
                "visible": False,
                "fixedrange": False,
                "scaleanchor": "x",
                "scaleratio": 1,
            },
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
            margin={"l": 60, "r": 30, "t": 50, "b": 30 + (30 * len(footer_text.splitlines()))},
            width=fig_width,
            height=fig_height,
            hovermode="closest",
            hoverlabel={"bgcolor": "#FDFEFE", "font_size": 12, "namelength": -1},
            title={
                "text": "Quantum Circuit" + (f"<br><sup>{footer_text}</sup>" if footer_text else ""),
                "x": 0.5,
                "font": {"size": 15, "color": "#2C3E50"},
            },
        )

        if _FIGUREWIDGET_AVAILABLE and isinstance(fig, _FigureWidget):
            for trace_idx, trace in enumerate(fig.data):
                if getattr(trace, "name", "").startswith("__verbatim__"):
                    block_idx = int(trace.name.split("__")[2])
                    # Closure that captures block_idx and state
                    def _make_callback(bidx: int, s: _RenderState):
                        def _on_click(trace, points, selector):  # noqa: ANN001
                            if not points.point_inds:
                                return
                            s.verbatim_blocks[bidx].expanded = not s.verbatim_blocks[bidx].expanded
                            new_fig = cls._build_figure(s)
                            with fig.batch_update():
                                fig.layout.shapes = new_fig.layout.shapes
                                fig.data = new_fig.data
                                fig.layout.xaxis = new_fig.layout.xaxis
                                fig.layout.yaxis = new_fig.layout.yaxis
                        return _on_click
                    trace.on_click(_make_callback(block_idx, state))

        return fig

    @classmethod
    def _add_qubit_wires(
        cls,
        shapes: list[dict],
        traces: list,
        layout: CircuitLayout,
        left_wire: float,
        right_wire: float,
    ) -> None:
        for row_idx, label in enumerate(layout.qubit_labels):
            y = -row_idx * cls.ROW_HEIGHT
            shapes.append({
                "type": "line",
                "x0": left_wire, "y0": y, "x1": right_wire, "y1": y,
                "line": {"color": cls.WIRE_COLOR, "width": 1.5},
                "layer": "below",
            })
            traces.append(go.Scatter(
                x=[left_wire - 0.1],
                y=[y],
                mode="text",
                text=[f"<b>{label} :</b>"],
                textposition="middle left",
                textfont={"size": 12, "family": "monospace", "color": "#2C3E50"},
                hoverinfo="skip",
                showlegend=False,
            ))

    @classmethod
    def _add_elements(
        cls,
        shapes: list[dict],
        traces: list,
        layout: CircuitLayout,
        col_x: list[float],
        col_w: list[float],
        hidden_cols: set[int],
        state: _RenderState,
    ) -> None:
        for elem in layout.elements:
            col = elem.col
            if col in hidden_cols or col_x[col] is None:
                continue
            x = col_x[col]

            if isinstance(elem, GateBox):
                cls._add_gate_box(shapes, traces, elem, x, state.device_metadata)
            elif isinstance(elem, ControlDot):
                cls._add_control_dot(shapes, traces, elem, x)
            elif isinstance(elem, SwapMarker):
                cls._add_swap_marker(traces, elem, x)
            elif isinstance(elem, Connection):
                cls._add_connection(shapes, elem, x)
            elif isinstance(elem, BarrierMarker):
                cls._add_barrier(shapes, elem, x)

    @classmethod
    def _add_gate_box(
        cls,
        shapes: list[dict],
        traces: list,
        elem: GateBox,
        x: float,
        device_metadata: dict[str, str],
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        bw = cls._gate_box_width(elem.label)
        bh = cls.GATE_BOX_HEIGHT

        shapes.append({
            "type": "rect",
            "x0": x - bw / 2, "y0": y - bh / 2,
            "x1": x + bw / 2, "y1": y + bh / 2,
            "fillcolor": cls.GATE_FILL_COLOR,
            "line": {"color": cls.GATE_LINE_COLOR, "width": 1.5},
            "layer": "above",
        })

        tooltip_lines = [
            f"<b>Gate:</b> {elem.label}",
            f"<b>Qubit row:</b> {elem.row}",
        ]
        extra = device_metadata.get(elem.label)
        if extra:
            tooltip_lines.append(f"<b>Device metadata:</b> {extra}")
        else:
            tooltip_lines.append("<i>Device metadata: N/A</i>")

        hovertext = "<br>".join(tooltip_lines)

        traces.append(go.Scatter(
            x=[x],
            y=[y],
            mode="text",
            text=[elem.label],
            textposition="middle center",
            textfont={"size": cls.GATE_FONT_SIZE, "family": "monospace", "color": "#1A2951"},
            hoverinfo="text",
            hovertext=hovertext,
            showlegend=False,
        ))

    @classmethod
    def _add_control_dot(
        cls,
        shapes: list[dict],
        traces: list,
        elem: ControlDot,
        x: float,
    ) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        fill = cls.CONTROL_DOT_COLOR if elem.filled else "white"
        shapes.append({
            "type": "circle",
            "x0": x - 0.12, "y0": y - 0.12,
            "x1": x + 0.12, "y1": y + 0.12,
            "fillcolor": fill,
            "line": {"color": cls.CONTROL_DOT_COLOR, "width": 1.5},
            "layer": "above",
        })
        label = "Control" if elem.filled else "Anti-control"
        traces.append(go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker={"size": 1, "opacity": 0},
            hoverinfo="text",
            hovertext=f"<b>{label}</b><br><b>Qubit row:</b> {elem.row}",
            showlegend=False,
        ))

    @classmethod
    def _add_swap_marker(cls, traces: list, elem: SwapMarker, x: float) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        traces.append(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker={"symbol": "x", "size": 14, "color": cls.SWAP_COLOR, "line": {"width": 2}},
            text=[""],
            hoverinfo="text",
            hovertext=f"<b>SWAP</b><br><b>Qubit row:</b> {elem.row}",
            showlegend=False,
        ))

    @classmethod
    def _add_connection(cls, shapes: list[dict], elem: Connection, x: float) -> None:
        y_start = -elem.row_start * cls.ROW_HEIGHT
        y_end = -elem.row_end * cls.ROW_HEIGHT
        shapes.append({
            "type": "line",
            "x0": x, "y0": y_start, "x1": x, "y1": y_end,
            "line": {"color": cls.CONNECTION_COLOR, "width": 1.8},
            "layer": "above",
        })

    @classmethod
    def _add_barrier(cls, shapes: list[dict], elem: BarrierMarker, x: float) -> None:
        y = -elem.row * cls.ROW_HEIGHT
        hw = 0.18
        hh = cls.ROW_HEIGHT * 0.35
        shapes.append({
            "type": "rect",
            "x0": x - hw, "y0": y - hh,
            "x1": x + hw, "y1": y + hh,
            "fillcolor": cls.BARRIER_FILL_COLOR,
            "line": {"color": cls.BARRIER_LINE_COLOR, "width": 1.0, "dash": "dot"},
            "layer": "above",
        })

    @classmethod
    def _add_verbatim_blocks(
        cls,
        shapes: list[dict],
        traces: list,
        layout: CircuitLayout,
        col_x: list[float],
        col_w: list[float],
        state: _RenderState,
    ) -> None:
        n_rows = max(layout.num_qubits, 1)
        top_y = cls.ROW_HEIGHT * 0.35
        bot_y = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.35

        for block_idx, block in enumerate(state.verbatim_blocks):
            cs = block.col_start
            ce = block.col_end

            # Guard: columns must be valid and have computed x positions
            if cs >= len(col_x) or ce >= len(col_x):
                continue
            if col_x[cs] is None or col_x[ce] is None:
                continue

            x_left = col_x[cs] - col_w[cs] / 2
            x_right = col_x[ce] + col_w[ce] / 2
            fill = cls.VERBATIM_EXPANDED_FILL if block.expanded else cls.VERBATIM_FILL_COLOR
            line_color = cls.VERBATIM_EXPANDED_LINE if block.expanded else cls.VERBATIM_LINE_COLOR

            shapes.append({
                "type": "rect",
                "x0": x_left, "y0": bot_y,
                "x1": x_right, "y1": top_y,
                "fillcolor": fill,
                "opacity": 0.35,
                "line": {"color": line_color, "width": 2.0, "dash": "dash"},
                "layer": "below",
            })

            cx = (x_left + x_right) / 2
            state_label = "▼ verbatim (expanded — click to collapse)" if block.expanded else "▶ verbatim (click to expand)"
            traces.append(go.Scatter(
                x=[cx],
                y=[top_y + 0.18],
                mode="text",
                text=[state_label],
                textposition="bottom center",
                textfont={"size": 10, "color": line_color, "family": "monospace"},
                hoverinfo="text",
                hovertext="<b>Verbatim box</b><br>Click to toggle expand/collapse",
                name=f"__verbatim__{block_idx}__",
                showlegend=False,
            ))

    @classmethod
    def _build_footer_text(cls, layout: CircuitLayout) -> str:
        lines: list[str] = []
        if layout.global_phase:
            lines.append(f"Global phase: {layout.global_phase}")
        if layout.additional_result_types:
            lines.append(f"Additional result types: {', '.join(layout.additional_result_types)}")
        if layout.unassigned_parameters:
            lines.append(f"Unassigned parameters: {', '.join(layout.unassigned_parameters)}")
        return "<br>".join(lines)

    @classmethod
    def _render_layout(cls, layout: CircuitLayout) -> Any:
        state = _RenderState(layout=layout)
        return cls._build_figure(state)
