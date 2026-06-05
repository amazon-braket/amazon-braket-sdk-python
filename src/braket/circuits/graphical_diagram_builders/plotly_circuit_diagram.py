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

from dataclasses import dataclass

try:
    import plotly.graph_objects as go
except ImportError:
    raise ImportError(
        "plotly is required for interactive visualization. "
        "Install it with: pip install amazon-braket-sdk[interactive]"
    )

import braket.circuits.circuit as cir
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
from braket.circuits.graphical_diagram_builders \
    .graphical_circuit_diagram import GraphicalCircuitDiagram
from braket.circuits.graphical_diagram_builders \
    .graphical_diagram_utils import (
        BarrierMarker,
        CircuitLayout,
        Connection,
        ControlDot,
        GateBox,
        SwapMarker,
    )
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType


@dataclass
class TooltipData:
    gate_name: str = ""
    target_qubits: str = ""
    parameters: str = ""


@dataclass
class VerbatimRange:
    col_start: int
    col_end: int
    row_top: int
    row_bottom: int
    gate_count: int


class PlotlyCircuitDiagram(GraphicalCircuitDiagram):
    """Interactive Plotly circuit diagram renderer.

    Subclasses :class:`GraphicalCircuitDiagram` and renders the computed
    :class:`CircuitLayout` as an interactive ``plotly.graph_objects.Figure``.

    Features compared to the static Matplotlib renderer:

    *   **Hover tooltips** – gates display name, target qubits, and
        parameters on hover.
    *   **Expandable / collapsible verbatim boxes** – a verbatim box
        can be toggled between a single collapsed block and the expanded
        inline gates via a Plotly ``updatemenu`` button.
    *   **Zoom, pan, and dynamic filtering** – standard Plotly figure
        controls are available.

    The visual style intentionally mirrors the Matplotlib renderer's
    coordinate system and colour palette so that users get a consistent
    experience regardless of which backend they choose.
    """

    ROW_HEIGHT = 0.8
    COL_WIDTH = 1.4
    COL_GAP = 0.2
    WIRE_EXTEND = 0.5

    GATE_BOX_HEIGHT = 0.5
    GATE_BOX_MIN_WIDTH = 0.6
    GATE_BOX_PADDING = 0.35
    GATE_FONT_SIZE = 11

    GATE_FILL = "#D4E6F1"
    GATE_EDGE = "black"
    GATE_TEXT = "black"

    WIRE_COLOR = "#333333"
    WIRE_LW = 2

    CONTROL_DOT_RADIUS = 8
    CONTROL_DOT_FILL = "black"
    CONTROL_OPEN_EDGE = "black"

    CONNECTION_LW = 2
    CONNECTION_COLOR = "black"

    BARRIER_FILL = "#DDDDDD"
    BARRIER_EDGE = "#888888"
    BARRIER_LW = 1
    BARRIER_WIDTH = 0.25
    BARRIER_HEIGHT_FRAC = 0.6

    QUBIT_FONT_SIZE = 12
    MOMENT_FONT_SIZE = 10
    FOOTER_FONT_SIZE = 10

    SWAP_SIZE = 10

    VB_FILL = "#FFF3CD"
    VB_EDGE = "#856404"
    VB_FONT_SIZE = 11

    @staticmethod
    def build_diagram(circuit: cir.Circuit) -> go.Figure:
        """Build an interactive Plotly figure for *circuit*.

        Args:
            circuit: The circuit to visualise.

        Returns:
            A ``plotly.graph_objects.Figure``.
        """
        if not circuit.instructions:
            return PlotlyCircuitDiagram._empty_figure("(empty circuit)")

        if all(
            m.moment_type == MomentType.GLOBAL_PHASE
            for m in circuit._moments
        ):
            return PlotlyCircuitDiagram._empty_figure(
                f"Global phase: {circuit.global_phase}"
            )

        layout = PlotlyCircuitDiagram._compute_layout(circuit)
        verbatim_ranges = PlotlyCircuitDiagram._detect_verbatim(
            circuit, layout)
        tooltips = PlotlyCircuitDiagram._build_tooltips(circuit, layout)
        return PlotlyCircuitDiagram._render_layout(
            circuit, layout, verbatim_ranges, tooltips)

    # ------------------------------------------------------------------
    # Empty-circuit helper
    # ------------------------------------------------------------------

    @classmethod
    def _empty_figure(cls, text: str) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5, text=text,
            xref="paper", yref="paper", showarrow=False,
            font={"size": 13},
        )
        fig.update_layout(
            xaxis={"visible": False, "range": [0, 1]},
            yaxis={"visible": False, "range": [0, 1]},
            width=400, height=160,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            template="none",
        )
        return fig

    # ------------------------------------------------------------------
    # Verbatim-region detection
    # ------------------------------------------------------------------

    @classmethod
    def _detect_verbatim(
        cls, circuit: cir.Circuit, layout: CircuitLayout
    ) -> list[VerbatimRange]:
        instrs = circuit.instructions
        if not instrs:
            return []

        # Build a map from instruction index to approximate column so we
        # can translate instruction positions into layout columns.
        col_of_instr: dict[int, int] = {}
        col = 0
        for idx, instr in enumerate(instrs):
            if (
                isinstance(instr, Instruction)
                and isinstance(instr.operator, Gate)
                and instr.operator.name == "GPhase"
            ):
                continue
            col_of_instr[idx] = col
            col += 1

        ranges: list[VerbatimRange] = []
        i = 0
        while i < len(instrs):
            instr = instrs[i]
            if (
                isinstance(instr, Instruction)
                and isinstance(instr.operator, CompilerDirective)
                and instr.operator.name == "StartVerbatimBox"
            ):
                start_col = col_of_instr.get(i, 0)
                gate_count = 0
                first_gate_row = 2**31
                last_gate_row = -1
                has_inner = False
                i += 1
                while i < len(instrs):
                    inner = instrs[i]
                    if (
                        isinstance(inner, Instruction)
                        and isinstance(inner.operator, CompilerDirective)
                        and inner.operator.name == "EndVerbatimBox"
                    ):
                        end_col = col_of_instr.get(i, layout.num_moments - 1)
                        qubits = sorted(circuit.qubits)
                        if not has_inner:
                            # Empty verbatim box: use the circuit's full qubit
                            # span
                            row_top = 0
                            row_bottom = max(len(qubits) - 1, 0)
                        else:
                            row_top = max(first_gate_row, 0)
                            row_bottom = max(last_gate_row, first_gate_row)
                        ranges.append(VerbatimRange(
                            col_start=start_col,
                            col_end=end_col,
                            row_top=row_top,
                            row_bottom=row_bottom,
                            gate_count=gate_count,
                        ))
                        i += 1
                        break
                    if isinstance(
                            inner, Instruction) and isinstance(
                            inner.operator, Gate):
                        gate_count += 1
                        has_inner = True
                        qubits = sorted(circuit.qubits)
                        for q in inner.target:
                            if q in qubits:
                                r = qubits.index(q)
                                first_gate_row = min(first_gate_row, r)
                                last_gate_row = max(last_gate_row, r)
                    i += 1
                else:
                    break
            else:
                i += 1
        return ranges

    # ------------------------------------------------------------------
    # Tooltip data
    # ------------------------------------------------------------------

    @classmethod
    def _build_tooltips(
        cls, circuit: cir.Circuit, layout: CircuitLayout
    ) -> dict[tuple[int, int], TooltipData]:
        """Return {(col, row): TooltipData} for every gate in *circuit*."""
        mapping: dict[tuple[int, int], TooltipData] = {}
        qubits = sorted(circuit.qubits)
        qi = {q: i for i, q in enumerate(qubits)}

        col = 0
        for _time, items in circuit.moments.time_slices().items():
            for item in items:
                if not isinstance(item, Instruction):
                    continue
                op = item.operator
                if not isinstance(op, Gate):
                    continue
                rows = [qi.get(q, -1) for q in item.target if q in qi]
                if not rows:
                    continue
                params = list(getattr(op, "parameters", ()))
                mapping[(col, rows[-1])] = TooltipData(
                    gate_name=op.name,
                    target_qubits=", ".join(
                        str(int(q)) for q in item.target
                    ),
                    parameters=(
                        ", ".join(str(p) for p in params)
                        if params else ""
                    ),
                )
            col += 1
        return mapping

    # ------------------------------------------------------------------
    # Column geometry
    # ------------------------------------------------------------------

    @classmethod
    def _col_geometry(
            cls, layout: CircuitLayout) -> tuple[list[float], list[float]]:
        n = max(layout.num_moments, 1)
        widths = [cls.COL_WIDTH] * n
        for e in layout.elements:
            if isinstance(e, GateBox):
                tw = len(e.label) * cls.GATE_FONT_SIZE * \
                    0.012 + cls.GATE_BOX_PADDING
                widths[e.col] = max(widths[e.col], tw + cls.COL_GAP)
        centers: list[float] = []
        cur = 0.0
        for w in widths:
            centers.append(cur + w / 2)
            cur += w
        return centers, widths

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    @classmethod
    def _qx(cls, col: int, col_x: list[float]) -> float:
        return col_x[col] if 0 <= col < len(col_x) else 0.0

    @classmethod
    def _qy(cls, row: int) -> float:
        return -row * cls.ROW_HEIGHT

    @classmethod
    def _gate_box_w(cls, label: str) -> float:
        return max(
            cls.GATE_BOX_MIN_WIDTH,
            len(label) *
            cls.GATE_FONT_SIZE *
            0.012 +
            cls.GATE_BOX_PADDING)

    # ------------------------------------------------------------------
    # Main render entry point
    # ------------------------------------------------------------------

    @classmethod
    def _render_layout(
        cls,
        circuit: cir.Circuit,
        layout: CircuitLayout,
        verbatim_ranges: list[VerbatimRange],
        tooltips: dict[tuple[int, int], TooltipData],
    ) -> go.Figure:
        """Convert *layout* (plus side-band data) into a go.Figure."""
        n_rows = max(layout.num_qubits, 1)
        col_x, col_w = cls._col_geometry(layout)
        total_w = sum(col_w)
        right_edge = total_w
        left_wire = col_x[0] - col_w[0] / 2 - cls.WIRE_EXTEND if col_x else 0
        right_wire = right_edge + cls.WIRE_EXTEND

        y_top = cls.ROW_HEIGHT * 0.8
        y_bottom = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.8

        # Which columns belong to a verbatim region?
        vb_cols: set[int] = set()
        for vr in verbatim_ranges:
            for c in range(vr.col_start, vr.col_end + 1):
                vb_cols.add(c)

        # Collect all traces flat; track indices inside verbatim regions
        # so the updatemenu can toggle them.
        all_traces: list[go.Scatter] = []
        # Index ranges for toggling
        always_visible_range: list[int] = []
        inside_vb_range: list[int] = []
        collapsed_vb_range: list[int] = []

        # ---- 1.  Background wires & qubit labels (always visible) ----
        _start = len(all_traces)
        cls._add_wires(all_traces, layout, left_wire, right_wire)
        cls._add_qlabels(all_traces, layout, left_wire)
        cls._add_moment_labels(all_traces, layout, col_x, y_top, y_bottom)
        cls._add_footer(all_traces, layout, left_wire, y_bottom)
        always_visible_range = list(range(_start, len(all_traces)))

        # ---- 2.  Connections (visibility depends on verbatim status) ----
        for elem in layout.elements:
            if not isinstance(elem, Connection):
                continue
            before = len(all_traces)
            cls._add_connection(all_traces, elem, cls._qx(elem.col, col_x))
            if elem.col in vb_cols:
                inside_vb_range.append(before)
            else:
                always_visible_range.append(before)

        # ---- 3.  Gate boxes, control dots, swap markers, barriers ----
        for elem in layout.elements:
            cls._render_elem(all_traces, elem, col_x, tooltips, vb_cols,
                             always_visible_range, inside_vb_range)

        # ---- 4.  Verbatim collapsed overlays ----
        _start = len(all_traces)
        cls._add_vb_collapsed(all_traces, layout, verbatim_ranges, col_x)
        collapsed_vb_range = list(range(_start, len(all_traces)))

        # ---- Remove duplicate connections spanning verbatim regions ----
        # (Verbatim regions already own connections in the collapsed overlay)

        # ---- 5.  Build figure ----
        fig = go.Figure()
        for t in all_traces:
            fig.add_trace(t)

        # Default: collapsed state
        all_idx = set(range(len(all_traces)))
        always_set = set(always_visible_range)
        vb_inside_v = len(inside_vb_range) > 0

        if vb_inside_v:
            coll_vis = [False] * len(all_traces)
            for i in always_set:
                coll_vis[i] = True
            for i in collapsed_vb_range:
                coll_vis[i] = True

            exp_vis = [False] * len(all_traces)
            for i in always_set:
                exp_vis[i] = True
            for i in inside_vb_range:
                exp_vis[i] = True

            fig.update_layout(
                updatemenus=[
                    {
                        "type": "buttons",
                        "direction": "right",
                        "x": 0.5,
                        "y": 1.08,
                        "xanchor": "center",
                        "buttons": [
                            {
                                "label": "Collapse verbatim boxes",
                                "method": "update",
                                "args": [
                                    {"visible": coll_vis},
                                    {
                                        "title": (
                                            "Circuit Diagram"
                                            " (verbatim boxes collapsed)"
                                        ),
                                    },
                                ],
                            },
                            {
                                "label": "Expand verbatim boxes",
                                "method": "update",
                                "args": [
                                    {"visible": exp_vis},
                                    {
                                        "title": (
                                            "Circuit Diagram"
                                            " (verbatim boxes expanded)"
                                        ),
                                    },
                                ],
                            },
                        ],
                    }
                ]
            )

        # ---- 6.  Apply initial visibility ----
        if vb_inside_v:
            for i in range(len(all_traces)):
                if i in always_set or i in collapsed_vb_range:
                    all_traces[i].visible = True
                else:
                    all_traces[i].visible = False

        # ---- 7.  Axes / layout ----
        y_extra = 0
        if verbatim_ranges:
            y_extra = 0.6
        footer_lines = cls._build_footer_lines(layout)
        yb = y_bottom - 0.4
        if footer_lines:
            yb -= len(footer_lines) * cls.ROW_HEIGHT * 0.5

        fig.update_layout(
            xaxis={
                "range": [left_wire - 1.5, right_wire + 0.5],
                "visible": False,
                "constrain": "domain",
            },
            yaxis={
                "range": [yb, y_top + 0.4 + y_extra],
                "visible": False,
                "scaleanchor": "x",
                "scaleratio": 1,
            },
            width=max(500, int((right_wire - left_wire + 2) * 80)),
            height=max(250, int((y_top - yb + y_extra) * 80)),
            margin={
                "l": 60, "r": 30,
                "t": 50 + (30 if verbatim_ranges else 0),
                "b": 40,
            },
            template="none",
            hovermode="closest",
            dragmode="pan",
            title="Circuit Diagram (verbatim boxes collapsed)"
            if verbatim_ranges else "Circuit Diagram",
        )
        return fig

    # ------------------------------------------------------------------
    # Element rendering dispatcher
    # ------------------------------------------------------------------

    @classmethod
    def _render_elem(
        cls,
        all_traces: list,
        elem: object,
        col_x: list[float],
        tooltips: dict,
        vb_cols: set[int],
        always_idx: list[int],
        vb_idx: list[int],
    ) -> None:
        if isinstance(elem, GateBox):
            before = len(all_traces)
            td = tooltips.get((elem.col, elem.row))
            hover = cls._tooltip_html(td) if td else elem.label
            cls._add_gate_box(
                all_traces, elem, cls._qx(
                    elem.col, col_x), hover)
            if elem.col in vb_cols:
                vb_idx.extend(range(before, len(all_traces)))
            else:
                always_idx.extend(range(before, len(all_traces)))
        elif isinstance(elem, ControlDot):
            before = len(all_traces)
            cls._add_control_dot(all_traces, elem, cls._qx(elem.col, col_x))
            if elem.col in vb_cols:
                vb_idx.append(before)
            else:
                always_idx.append(before)
        elif isinstance(elem, SwapMarker):
            before = len(all_traces)
            cls._add_swap(all_traces, elem, cls._qx(elem.col, col_x))
            if elem.col in vb_cols:
                vb_idx.append(before)
            else:
                always_idx.append(before)
        elif isinstance(elem, BarrierMarker):
            before = len(all_traces)
            cls._add_barrier(all_traces, elem, cls._qx(elem.col, col_x))
            always_idx.append(before)

    # ------------------------------------------------------------------
    # Individual drawing helpers
    # ------------------------------------------------------------------

    @classmethod
    def _tooltip_html(cls, td: TooltipData) -> str:
        lines = [f"<b>{td.gate_name}</b>", f"Target: q{td.target_qubits}"]
        if td.parameters:
            lines.append(f"Params: {td.parameters}")
        lines.append("<i>Device metadata: N/A</i>")
        return "<br>".join(lines)

    @classmethod
    def _add_wires(
        cls, traces: list, layout: CircuitLayout, lx: float, rx: float
    ) -> None:
        for ri, _label in enumerate(layout.qubit_labels):
            y = cls._qy(ri)
            traces.append(go.Scatter(
                x=[lx, rx], y=[y, y],
                mode="lines",
                line={"color": cls.WIRE_COLOR, "width": cls.WIRE_LW},
                showlegend=False, hoverinfo="skip",
            ))

    @classmethod
    def _add_qlabels(
        cls, traces: list, layout: CircuitLayout, lx: float
    ) -> None:
        for ri, label in enumerate(layout.qubit_labels):
            y = cls._qy(ri)
            traces.append(go.Scatter(
                x=[lx - 0.15], y=[y],
                mode="text",
                text=[f"{label} :"],
                textposition="middle right",
                textfont={
                    "family": "monospace",
                    "size": cls.QUBIT_FONT_SIZE,
                    "color": "black",
                },
                showlegend=False, hoverinfo="skip",
            ))

    @classmethod
    def _add_moment_labels(
        cls, traces: list, layout: CircuitLayout,
        col_x: list[float], yt: float, yb: float,
    ) -> None:
        ranges: list[tuple[str, int, int]] = []
        for ci, label in enumerate(layout.moment_labels):
            if ranges and ranges[-1][0] == label:
                ranges[-1] = (label, ranges[-1][1], ci)
            else:
                ranges.append((label, ci, ci))
        for label, cs, ce in ranges:
            cx = (col_x[cs] + col_x[ce]) / \
                2 if cs < len(col_x) and ce < len(col_x) else 0
            for y in (yt, yb):
                traces.append(
                    go.Scatter(
                        x=[cx],
                        y=[y],
                        mode="text",
                        text=[label],
                        textposition="middle center",
                        textfont={
                            "family": "monospace",
                            "size": cls.MOMENT_FONT_SIZE,
                            "color": "#555555",
                        },
                        showlegend=False,
                        hoverinfo="skip",
                    ))

    @classmethod
    def _build_footer_lines(cls, layout: CircuitLayout) -> list[str]:
        lines = []
        if layout.global_phase:
            lines.append(f"Global phase: {layout.global_phase}")
        if layout.additional_result_types:
            lines.append(
                f"Additional result types: {
                    ', '.join(
                        layout.additional_result_types)}")
        if layout.unassigned_parameters:
            lines.append(
                f"Unassigned parameters: {
                    ', '.join(
                        layout.unassigned_parameters)}")
        return lines

    @classmethod
    def _add_footer(
        cls, traces: list, layout: CircuitLayout,
        lx: float, yb: float,
    ) -> None:
        lines = cls._build_footer_lines(layout)
        fy = yb - cls.ROW_HEIGHT * 0.7
        for i, line in enumerate(lines):
            traces.append(go.Scatter(
                x=[lx], y=[fy - i * cls.ROW_HEIGHT * 0.5],
                mode="text", text=[line],
                textposition="top left",
                textfont={
                    "family": "monospace",
                    "size": cls.FOOTER_FONT_SIZE,
                    "color": "#333333",
                },
                showlegend=False, hoverinfo="skip",
            ))

    @classmethod
    def _add_gate_box(
        cls, traces: list, elem: GateBox, x: float, hover: str,
    ) -> None:
        y = cls._qy(elem.row)
        hh = cls.GATE_BOX_HEIGHT / 2
        bw = cls._gate_box_w(elem.label)

        traces.append(go.Scatter(
            x=[x - bw / 2, x + bw / 2, x + bw / 2, x - bw / 2, x - bw / 2],
            y=[y - hh, y - hh, y + hh, y + hh, y - hh],
            mode="lines",
            fill="toself",
            fillcolor=cls.GATE_FILL,
            line={"color": cls.GATE_EDGE, "width": 1.2},
            showlegend=False,
            hoverinfo="text",
            text=hover,
            hovertemplate="%{text}<extra></extra>",
        ))
        traces.append(
            go.Scatter(
                x=[x],
                y=[y],
                mode="text",
                text=[
                    elem.label],
                textposition="middle center",
                textfont={
                    "family": "monospace",
                    "size": cls.GATE_FONT_SIZE,
                    "color": cls.GATE_TEXT,
                },
                showlegend=False,
                hoverinfo="skip",
            ))

    @classmethod
    def _add_control_dot(
            cls,
            traces: list,
            elem: ControlDot,
            x: float) -> None:
        y = cls._qy(elem.row)
        fill = cls.CONTROL_DOT_FILL if elem.filled else "white"
        line_w = 0 if elem.filled else 1.5
        text = "Control" if elem.filled else "Anti-control"
        traces.append(go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker={
                "symbol": "circle",
                "size": cls.CONTROL_DOT_RADIUS,
                "color": fill,
                "line": {"color": cls.CONTROL_DOT_FILL, "width": line_w},
            },
            showlegend=False,
            hoverinfo="text", text=text,
            hovertemplate="%{text}<extra></extra>",
        ))

    @classmethod
    def _add_swap(cls, traces: list, elem: SwapMarker, x: float) -> None:
        y = cls._qy(elem.row)
        traces.append(go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker={
                "symbol": "x",
                "size": cls.SWAP_SIZE,
                "color": cls.CONNECTION_COLOR,
                "line": {"width": 2},
            },
            showlegend=False, hoverinfo="skip",
        ))

    @classmethod
    def _add_connection(cls, traces: list, elem: Connection, x: float) -> None:
        traces.append(go.Scatter(
            x=[x, x],
            y=[cls._qy(elem.row_start), cls._qy(elem.row_end)],
            mode="lines",
            line={"color": cls.CONNECTION_COLOR, "width": cls.CONNECTION_LW},
            showlegend=False, hoverinfo="skip",
        ))

    @classmethod
    def _add_barrier(cls, traces: list, elem: BarrierMarker, x: float) -> None:
        y = cls._qy(elem.row)
        hh = cls.ROW_HEIGHT * cls.BARRIER_HEIGHT_FRAC / 2
        hw = cls.BARRIER_WIDTH / 2
        traces.append(go.Scatter(
            x=[x - hw, x + hw, x + hw, x - hw, x - hw],
            y=[y - hh, y - hh, y + hh, y + hh, y - hh],
            mode="lines",
            fill="toself",
            fillcolor=cls.BARRIER_FILL,
            line={"color": cls.BARRIER_EDGE, "width": cls.BARRIER_LW},
            showlegend=False, hoverinfo="skip",
        ))

    # ------------------------------------------------------------------
    # Verbatim collapse / expand
    # ------------------------------------------------------------------

    @classmethod
    def _add_vb_collapsed(
        cls, traces: list, layout: CircuitLayout,
        verbatim_ranges: list[VerbatimRange], col_x: list[float],
    ) -> None:
        """Append traces for the collapsed verbatim-box overlay."""
        for vr in verbatim_ranges:
            if vr.col_start >= len(col_x) or vr.col_end >= len(col_x):
                continue
            x1 = col_x[vr.col_start]
            x2 = col_x[vr.col_end]
            cx = (x1 + x2) / 2
            bw = abs(x2 - x1) + cls.COL_WIDTH * 0.5
            y1 = cls._qy(vr.row_top)
            y2 = cls._qy(vr.row_bottom)
            mid_y = (y1 + y2) / 2
            bh = abs(y2 - y1) + cls.GATE_BOX_HEIGHT

            label = f"Verbatim ({
                vr.gate_count} gate{
                's' if vr.gate_count != 1 else ''})"

            # Dashed border box
            traces.append(go.Scatter(
                x=[cx - bw / 2, cx + bw / 2,
                   cx + bw / 2, cx - bw / 2, cx - bw / 2],
                y=[mid_y - bh / 2, mid_y - bh / 2,
                   mid_y + bh / 2, mid_y + bh / 2, mid_y - bh / 2],
                mode="lines",
                fill="toself",
                fillcolor=cls.VB_FILL,
                line={"color": cls.VB_EDGE, "width": 2, "dash": "dash"},
                showlegend=False,
                hoverinfo="text",
                text=(
                    f"Verbatim box: {vr.gate_count}"
                    f" gate{'s' if vr.gate_count != 1 else ''}. "
                    "Click 'Expand verbatim boxes'"
                    " above to view."
                ),
                hovertemplate="%{text}<extra></extra>",
            ))
            # Label
            traces.append(
                go.Scatter(
                    x=[cx],
                    y=[mid_y],
                    mode="text",
                    text=[label],
                    textposition="middle center",
                    textfont={
                        "family": "monospace",
                        "size": cls.VB_FONT_SIZE,
                        "color": cls.VB_EDGE,
                    },
                    showlegend=False,
                    hoverinfo="skip",
                ))
            # Vertical dashed line spanning all qubits of the verbatim box
            if vr.row_top != vr.row_bottom:
                traces.append(go.Scatter(
                    x=[cx, cx], y=[y1, y2],
                    mode="lines",
                    line={"color": cls.VB_EDGE, "width": 1.5, "dash": "dash"},
                    showlegend=False, hoverinfo="skip",
                ))
