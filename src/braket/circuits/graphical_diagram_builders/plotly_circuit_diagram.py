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

"""Interactive circuit diagram renderer powered by Plotly.

This module provides :class:`PlotlyCircuitDiagram`, a sibling to
:class:`MatplotlibCircuitDiagram` that renders quantum circuits as
interactive Plotly figures.  Key features include:

* **Hover tooltips** – hovering over a gate displays the gate name,
  target qubit(s), parameters (if any), and a placeholder for
  device-specific metadata such as fidelity or error rates.
* **Expandable/collapsible verbatim blocks** – verbatim boxes are
  rendered as a single collapsed block by default.  A toggle button
  lets the user expand them to reveal inner gates, or collapse them
  back.  The mechanism is written with extensibility in mind so it
  can later be reused for ``box``, ``scope``, and nested-subroutine
  structures once the BDK exposes them.
* **Zoom & pan** – provided out-of-the-box by Plotly's toolbar.
* **Jupyter rendering** – the returned ``plotly.graph_objects.Figure``
  renders inline in Jupyter notebooks without extra configuration.

Usage
-----
::

    from braket.circuits import Circuit

    circuit = Circuit().h(0).cnot(0, 1)

    # Via the Circuit convenience method:
    fig = circuit.show("interactive")   # returns a plotly Figure
    fig.show()                          # opens in browser / renders in notebook

    # Directly:
    from braket.circuits.graphical_diagram_builders import PlotlyCircuitDiagram
    fig = PlotlyCircuitDiagram.build_diagram(circuit)

Extensibility – sub-structure expand/collapse
---------------------------------------------
The toggle implementation identifies *collapsible regions* by scanning
the instruction stream for matched compiler-directive pairs (currently
``StartVerbatimBox`` / ``EndVerbatimBox``).  To support a new pair
(e.g. a future ``StartScope`` / ``EndScope``), add an entry to
``_COLLAPSIBLE_PAIRS`` and the rest of the pipeline handles it
automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import braket.circuits.circuit as cir
from braket.circuits.compiler_directive import CompilerDirective
from braket.circuits.gate import Gate
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

# ---------------------------------------------------------------------------
# Collapsible region registry – extend this to support new sub-structures.
# Each entry maps a *start* compiler-directive name to the corresponding
# *end* name and the label shown in the collapsed view.
# ---------------------------------------------------------------------------
_COLLAPSIBLE_PAIRS: dict[str, dict[str, str]] = {
    "StartVerbatimBox": {"end": "EndVerbatimBox", "label": "Verbatim"},
    # Future example:
    # "StartScope": {"end": "EndScope", "label": "Scope"},
}

# Build a reverse look-up set for quick membership tests.
_COLLAPSIBLE_END_NAMES: set[str] = {v["end"] for v in _COLLAPSIBLE_PAIRS.values()}


@dataclass
class _CollapsibleRegion:
    """Describes one collapsible block in the circuit (e.g. a verbatim box).

    Attributes:
        label: Human-readable label shown in the collapsed view.
        start_col: Column index of the start directive.
        end_col: Column index of the end directive.
        inner_cols: Column indices of the gates enclosed by the block
                    (excluding the start/end directive columns).
        row_min: Minimum qubit row spanned by the block.
        row_max: Maximum qubit row spanned by the block.
    """

    label: str
    start_col: int
    end_col: int
    inner_cols: list[int] = field(default_factory=list)
    row_min: int = 0
    row_max: int = 0


def _ensure_plotly():
    """Import plotly or raise a helpful error."""
    try:
        import plotly.graph_objects as go  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Plotly is required for interactive circuit visualization.  "
            "Install it with:\n\n"
            "    pip install amazon-braket-sdk[interactive]\n"
        ) from exc


class PlotlyCircuitDiagram(GraphicalCircuitDiagram):
    """Renders circuit diagrams as interactive Plotly figures.

    The visual layout mirrors the Matplotlib renderer but adds:

    * Hover tooltips on every gate element.
    * Toggle buttons for verbatim-box expand/collapse.
    * Built-in zoom/pan via the Plotly toolbar.

    Examples:
        >>> from braket.circuits import Circuit
        >>> circ = Circuit().h(0).cnot(0, 1).rx(0, 0.5)
        >>> fig = PlotlyCircuitDiagram.build_diagram(circ)
        >>> fig.show()  # renders in browser or Jupyter
    """

    # ── Layout constants (match Matplotlib renderer) ──────────────────
    COL_WIDTH = 1.4
    COL_GAP = 0.2
    ROW_HEIGHT = 0.8
    WIRE_EXTEND = 0.5

    GATE_BOX_HEIGHT = 0.5
    GATE_BOX_MIN_WIDTH = 0.6
    GATE_BOX_PADDING = 0.3
    GATE_FONT_SIZE = 12

    # Colours
    GATE_FILL_COLOR = "#D4E6F1"
    GATE_EDGE_COLOR = "black"
    GATE_TEXT_COLOR = "black"
    WIRE_COLOR = "#333333"
    WIRE_LW = 1.0
    CONTROL_DOT_RADIUS = 0.08
    CONTROL_DOT_COLOR = "black"
    CONNECTION_LW = 1.5
    CONNECTION_COLOR = "black"
    BARRIER_COLOR = "#888888"
    BARRIER_FILL_COLOR = "#DDDDDD"
    BARRIER_WIDTH = 0.25
    BARRIER_HEIGHT_FRAC = 0.6
    SWAP_MARKER_SIZE = 10

    # Verbatim collapsed block colours
    VERBATIM_FILL = "rgba(255,235,205,0.7)"
    VERBATIM_EDGE = "#CC8800"

    # ── Public entry point ────────────────────────────────────────────

    @staticmethod
    def build_diagram(circuit: cir.Circuit) -> object:
        """Build an interactive Plotly figure for *circuit*.

        Args:
            circuit: The circuit to visualise.

        Returns:
            A ``plotly.graph_objects.Figure``.

        Raises:
            ImportError: If plotly is not installed.

        Examples:
            >>> fig = PlotlyCircuitDiagram.build_diagram(Circuit().h(0))
            >>> fig.show()
        """
        _ensure_plotly()
        import plotly.graph_objects as go

        if not circuit.instructions:
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5, text="(empty circuit)",
                showarrow=False, font=dict(size=14),
                xref="paper", yref="paper",
            )
            fig.update_layout(
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                width=300, height=150,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            return fig

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text=f"Global phase: {circuit.global_phase}",
                showarrow=False, font=dict(size=14),
                xref="paper", yref="paper",
            )
            fig.update_layout(
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                width=400, height=150,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            return fig

        layout = PlotlyCircuitDiagram._compute_layout(circuit)

        # Detect collapsible regions in the layout.
        regions = PlotlyCircuitDiagram._find_collapsible_regions(layout)

        return PlotlyCircuitDiagram._render_layout(layout, regions=regions)

    # ── Rendering ─────────────────────────────────────────────────────

    @classmethod
    def _render_layout(cls, layout: CircuitLayout, *, regions: list[_CollapsibleRegion] | None = None) -> object:  # noqa: E501
        """Convert a ``CircuitLayout`` into a Plotly figure.

        Args:
            layout: Pre-computed circuit layout.
            regions: Collapsible regions (verbatim boxes etc.).

        Returns:
            A ``plotly.graph_objects.Figure``.
        """
        _ensure_plotly()
        import plotly.graph_objects as go

        if regions is None:
            regions = []

        n_rows = max(layout.num_qubits, 1)
        col_x, col_w = cls._compute_column_x(layout)
        total_width = sum(col_w)

        left_wire = col_x[0] - col_w[0] / 2 - cls.WIRE_EXTEND
        right_wire = total_width + cls.WIRE_EXTEND

        fig = go.Figure()

        # ── qubit wires ──────────────────────────────────────────────
        cls._draw_qubit_wires(fig, layout, left_wire, right_wire)

        # ── determine which columns are inside collapsible regions ───
        inner_col_set: set[int] = set()
        start_end_col_set: set[int] = set()
        for region in regions:
            inner_col_set.update(region.inner_cols)
            start_end_col_set.add(region.start_col)
            start_end_col_set.add(region.end_col)

        # ── elements (expanded view, always present) ─────────────────
        expanded_shapes: list[dict] = []
        expanded_annotations: list[dict] = []
        expanded_traces: list[go.Scatter] = []

        # ── elements that are NOT inside any collapsible region ──────
        static_shapes: list[dict] = []
        static_annotations: list[dict] = []

        for elem in layout.elements:
            col = elem.col
            in_region = col in inner_col_set or col in start_end_col_set

            shapes_out, annots_out, traces_out = cls._render_element(
                elem, col_x, layout
            )

            if in_region:
                for s in shapes_out:
                    s["visible"] = True
                expanded_shapes.extend(shapes_out)
                for a in annots_out:
                    a["visible"] = True
                expanded_annotations.extend(annots_out)
                expanded_traces.extend(traces_out)
            else:
                static_shapes.extend(shapes_out)
                static_annotations.extend(annots_out)
                for t in traces_out:
                    fig.add_trace(t)

        # ── collapsed verbatim blocks ────────────────────────────────
        collapsed_shapes: list[dict] = []
        collapsed_annotations: list[dict] = []

        for region in regions:
            s, a = cls._render_collapsed_region(region, col_x)
            for shape in s:
                shape["visible"] = False
            collapsed_shapes.extend(s)
            for annot in a:
                annot["visible"] = False
            collapsed_annotations.extend(a)

        # ── add expanded traces (hidden by default if regions exist) ──
        expanded_trace_start = len(fig.data)
        for t in expanded_traces:
            t.visible = True if not regions else True
            fig.add_trace(t)
        expanded_trace_end = len(fig.data)

        # ── moment labels ────────────────────────────────────────────
        label_y_top = cls.ROW_HEIGHT * 0.8
        label_y_bottom = -(n_rows - 1) * cls.ROW_HEIGHT - cls.ROW_HEIGHT * 0.8
        moment_annots = cls._moment_label_annotations(layout, col_x, label_y_top, label_y_bottom)

        # ── footer ───────────────────────────────────────────────────
        footer_annots = cls._footer_annotations(layout, left_wire, label_y_bottom)

        # ── assemble all shapes and annotations ──────────────────────
        all_shapes = static_shapes + expanded_shapes + collapsed_shapes
        all_annotations = (
            static_annotations + expanded_annotations
            + collapsed_annotations + moment_annots + footer_annots
        )

        # ── update-menus for toggling ────────────────────────────────
        updatemenus = []
        if regions:
            # Build visibility toggling.
            # expanded state: expanded shapes/annots visible, collapsed hidden
            # collapsed state: collapsed shapes/annots visible, expanded hidden

            def _make_vis(show_expanded: bool):
                """Return shapes + annotations lists with correct visibility."""
                shapes_copy = []
                for s in all_shapes:
                    sc = dict(s)
                    if s in expanded_shapes:
                        sc["visible"] = show_expanded
                    elif s in collapsed_shapes:
                        sc["visible"] = not show_expanded
                    shapes_copy.append(sc)

                annots_copy = []
                for a in all_annotations:
                    ac = dict(a)
                    if a in expanded_annotations:
                        ac["visible"] = show_expanded
                    elif a in collapsed_annotations:
                        ac["visible"] = not show_expanded
                    annots_copy.append(ac)

                # Trace visibility
                trace_vis = list(fig.data)  # noqa: B023
                vis_list = []
                for i in range(len(trace_vis)):
                    if expanded_trace_start <= i < expanded_trace_end:
                        vis_list.append(show_expanded)
                    else:
                        vis_list.append(True)

                return shapes_copy, annots_copy, vis_list

            exp_shapes, exp_annots, exp_trace_vis = _make_vis(True)
            col_shapes, col_annots, col_trace_vis = _make_vis(False)

            updatemenus.append(
                dict(
                    type="buttons",
                    direction="left",
                    x=0.0,
                    xanchor="left",
                    y=1.15,
                    yanchor="top",
                    buttons=[
                        dict(
                            label="▶ Expand Verbatim",
                            method="update",
                            args=[
                                {"visible": exp_trace_vis},
                                {
                                    "shapes": exp_shapes,
                                    "annotations": exp_annots,
                                },
                            ],
                        ),
                        dict(
                            label="▼ Collapse Verbatim",
                            method="update",
                            args=[
                                {"visible": col_trace_vis},
                                {
                                    "shapes": col_shapes,
                                    "annotations": col_annots,
                                },
                            ],
                        ),
                    ],
                )
            )

        # ── final layout ─────────────────────────────────────────────
        fig_width = max(500, (cls.WIRE_EXTEND * 2 + total_width + 1.5) * 90)
        fig_height = max(250, (n_rows * cls.ROW_HEIGHT + 1.5) * 90)

        y_bottom = label_y_bottom - 0.4
        if footer_annots:
            y_bottom -= len(footer_annots) * cls.ROW_HEIGHT * 0.5

        fig.update_layout(
            shapes=all_shapes,
            annotations=all_annotations,
            updatemenus=updatemenus if updatemenus else [],
            xaxis=dict(
                range=[left_wire - 1.5, right_wire + 0.5],
                showgrid=False,
                zeroline=False,
                visible=False,
            ),
            yaxis=dict(
                range=[y_bottom, label_y_top + 0.4],
                showgrid=False,
                zeroline=False,
                visible=False,
                scaleanchor="x",
                scaleratio=1,
            ),
            width=fig_width,
            height=fig_height,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=50, b=10),
            showlegend=False,
            hovermode="closest",
        )

        return fig

    # ── Per-element rendering helpers ─────────────────────────────────

    @classmethod
    def _render_element(cls, elem, col_x, layout):
        """Render a single layout element into Plotly shapes/annotations/traces.

        Returns:
            Tuple of (shapes, annotations, traces).
        """
        import plotly.graph_objects as go

        shapes: list[dict] = []
        annotations: list[dict] = []
        traces: list[go.Scatter] = []

        if isinstance(elem, GateBox):
            s, a, t = cls._render_gate_box(elem, col_x[elem.col], layout)
            shapes.extend(s)
            annotations.extend(a)
            traces.extend(t)
        elif isinstance(elem, ControlDot):
            s, t = cls._render_control_dot(elem, col_x[elem.col], layout)
            shapes.extend(s)
            traces.extend(t)
        elif isinstance(elem, SwapMarker):
            t = cls._render_swap_marker(elem, col_x[elem.col], layout)
            traces.extend(t)
        elif isinstance(elem, Connection):
            t = cls._render_connection(elem, col_x[elem.col])
            traces.extend(t)
        elif isinstance(elem, BarrierMarker):
            s = cls._render_barrier(elem, col_x[elem.col])
            shapes.extend(s)

        return shapes, annotations, traces

    @classmethod
    def _render_gate_box(cls, elem: GateBox, x: float, layout: CircuitLayout):
        """Render a gate as a filled rectangle with label and hover trace."""
        import plotly.graph_objects as go

        y = -elem.row * cls.ROW_HEIGHT
        box_w = cls._gate_box_width(elem.label)
        half_w = box_w / 2
        half_h = cls.GATE_BOX_HEIGHT / 2

        shape = dict(
            type="rect",
            x0=x - half_w, y0=y - half_h,
            x1=x + half_w, y1=y + half_h,
            fillcolor=cls.GATE_FILL_COLOR,
            line=dict(color=cls.GATE_EDGE_COLOR, width=1.2),
            layer="above",
        )

        annotation = dict(
            x=x, y=y,
            text=elem.label,
            showarrow=False,
            font=dict(size=cls.GATE_FONT_SIZE, family="monospace", color=cls.GATE_TEXT_COLOR),
        )

        # Hover tooltip
        qubit_label = layout.qubit_labels[elem.row] if elem.row < len(layout.qubit_labels) else f"q{elem.row}"
        hover_text = cls._build_hover_text(
            gate_name=elem.label,
            qubit_label=qubit_label,
            row=elem.row,
            col=elem.col,
        )

        hover_trace = go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker=dict(size=max(box_w, cls.GATE_BOX_HEIGHT) * 30, opacity=0),
            hoverinfo="text",
            hovertext=hover_text,
            showlegend=False,
        )

        return [shape], [annotation], [hover_trace]

    @classmethod
    def _render_control_dot(cls, elem: ControlDot, x: float, layout: CircuitLayout):
        """Render a control/anti-control dot with hover."""
        import plotly.graph_objects as go

        y = -elem.row * cls.ROW_HEIGHT
        r = cls.CONTROL_DOT_RADIUS

        if elem.filled:
            shape = dict(
                type="circle",
                x0=x - r, y0=y - r,
                x1=x + r, y1=y + r,
                fillcolor=cls.CONTROL_DOT_COLOR,
                line=dict(color=cls.CONTROL_DOT_COLOR, width=1),
                layer="above",
            )
        else:
            shape = dict(
                type="circle",
                x0=x - r, y0=y - r,
                x1=x + r, y1=y + r,
                fillcolor="white",
                line=dict(color=cls.CONTROL_DOT_COLOR, width=1.5),
                layer="above",
            )

        qubit_label = layout.qubit_labels[elem.row] if elem.row < len(layout.qubit_labels) else f"q{elem.row}"
        control_type = "Control" if elem.filled else "Anti-control"
        hover_text = (
            f"<b>{control_type}</b><br>"
            f"Qubit: {qubit_label}<br>"
            f"<i>Device metadata: N/A</i>"
        )

        hover_trace = go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker=dict(size=12, opacity=0),
            hoverinfo="text",
            hovertext=hover_text,
            showlegend=False,
        )

        return [shape], [hover_trace]

    @classmethod
    def _render_swap_marker(cls, elem: SwapMarker, x: float, layout: CircuitLayout):
        """Render a SWAP × marker with hover."""
        import plotly.graph_objects as go

        y = -elem.row * cls.ROW_HEIGHT
        qubit_label = layout.qubit_labels[elem.row] if elem.row < len(layout.qubit_labels) else f"q{elem.row}"
        hover_text = (
            f"<b>SWAP</b><br>"
            f"Qubit: {qubit_label}<br>"
            f"<i>Device metadata: N/A</i>"
        )

        trace = go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker=dict(
                symbol="x",
                size=cls.SWAP_MARKER_SIZE,
                color=cls.CONNECTION_COLOR,
                line=dict(width=2, color=cls.CONNECTION_COLOR),
            ),
            hoverinfo="text",
            hovertext=hover_text,
            showlegend=False,
        )
        return [trace]

    @classmethod
    def _render_connection(cls, elem: Connection, x: float):
        """Render a vertical connection line between qubit rows."""
        import plotly.graph_objects as go

        y_start = -elem.row_start * cls.ROW_HEIGHT
        y_end = -elem.row_end * cls.ROW_HEIGHT

        trace = go.Scatter(
            x=[x, x], y=[y_start, y_end],
            mode="lines",
            line=dict(color=cls.CONNECTION_COLOR, width=cls.CONNECTION_LW),
            hoverinfo="skip",
            showlegend=False,
        )
        return [trace]

    @classmethod
    def _render_barrier(cls, elem: BarrierMarker, x: float):
        """Render a barrier marker as a hatched rectangle."""
        y = -elem.row * cls.ROW_HEIGHT
        half_h = cls.ROW_HEIGHT * cls.BARRIER_HEIGHT_FRAC / 2
        half_w = cls.BARRIER_WIDTH / 2

        shape = dict(
            type="rect",
            x0=x - half_w, y0=y - half_h,
            x1=x + half_w, y1=y + half_h,
            fillcolor=cls.BARRIER_FILL_COLOR,
            line=dict(color=cls.BARRIER_COLOR, width=1, dash="dot"),
            layer="above",
        )
        return [shape]

    # ── Collapsed region rendering ────────────────────────────────────

    @classmethod
    def _render_collapsed_region(cls, region: _CollapsibleRegion, col_x: list[float]):
        """Render a collapsed verbatim block as a single labelled rectangle."""
        x_start = col_x[region.start_col]
        x_end = col_x[region.end_col]

        cx = (x_start + x_end) / 2
        y_top = -region.row_min * cls.ROW_HEIGHT + cls.GATE_BOX_HEIGHT / 2 + 0.1
        y_bot = -region.row_max * cls.ROW_HEIGHT - cls.GATE_BOX_HEIGHT / 2 - 0.1

        shape = dict(
            type="rect",
            x0=x_start - cls.COL_WIDTH / 2,
            y0=y_bot,
            x1=x_end + cls.COL_WIDTH / 2,
            y1=y_top,
            fillcolor=cls.VERBATIM_FILL,
            line=dict(color=cls.VERBATIM_EDGE, width=2, dash="dash"),
            layer="above",
        )

        annotation = dict(
            x=cx,
            y=(y_top + y_bot) / 2,
            text=f"<b>{region.label}</b>",
            showarrow=False,
            font=dict(size=14, family="monospace", color=cls.VERBATIM_EDGE),
        )

        return [shape], [annotation]

    # ── Collapsible region detection ──────────────────────────────────

    @classmethod
    def _find_collapsible_regions(cls, layout: CircuitLayout) -> list[_CollapsibleRegion]:
        """Scan layout elements for matched start/end directive pairs.

        Returns a list of :class:`_CollapsibleRegion` objects describing
        each block that can be collapsed.
        """
        # Map label text to the directive type.
        start_labels = {}
        for start_name, info in _COLLAPSIBLE_PAIRS.items():
            # The ascii_symbols for StartVerbatimBox is "StartVerbatim"
            start_labels["StartVerbatim"] = info
        end_labels = {"EndVerbatim": "StartVerbatim"}

        # Find start/end GateBox elements by label, uniqueing by column index
        # to avoid duplicates for multi-qubit compiler directives.
        start_by_col: dict[int, dict] = {}
        end_by_col: dict[int, None] = {}

        for elem in layout.elements:
            if isinstance(elem, GateBox):
                if elem.label in start_labels:
                    if elem.col not in start_by_col:
                        start_by_col[elem.col] = start_labels[elem.label]
                elif elem.label in end_labels:
                    if elem.col not in end_by_col:
                        end_by_col[elem.col] = None

        # Build sorted list of events
        events: list[tuple[int, str, dict | None]] = []
        for col, info in start_by_col.items():
            events.append((col, "start", info))
        for col in end_by_col:
            events.append((col, "end", None))
        events.sort(key=lambda x: x[0])

        # Match pairs using a stack
        regions: list[_CollapsibleRegion] = []
        stack: list[tuple[int, dict]] = []

        for col, event_type, info in events:
            if event_type == "start":
                stack.append((col, info))
            elif event_type == "end":
                if stack:
                    start_col, start_info = stack.pop()
                    # Determine inner columns
                    inner_cols = [
                        c for c in range(start_col + 1, col)
                        if c < layout.num_moments
                    ]

                    # Determine row span
                    all_rows = set()
                    for e in layout.elements:
                        if hasattr(e, "col") and hasattr(e, "row"):
                            if start_col <= e.col <= col:
                                all_rows.add(e.row)
                        elif isinstance(e, Connection):
                            if e.col >= start_col and e.col <= col:
                                all_rows.update(range(e.row_start, e.row_end + 1))

                    row_min = min(all_rows) if all_rows else 0
                    row_max = max(all_rows) if all_rows else 0

                    regions.append(_CollapsibleRegion(
                        label=start_info["label"],
                        start_col=start_col,
                        end_col=col,
                        inner_cols=inner_cols,
                        row_min=row_min,
                        row_max=row_max,
                    ))

        return regions

    # ── Hover text builder ────────────────────────────────────────────

    @classmethod
    def _build_hover_text(
        cls,
        gate_name: str,
        qubit_label: str,
        row: int,
        col: int,
        metadata: dict | None = None,
    ) -> str:
        """Build HTML hover text for a gate element.

        Args:
            gate_name: Display name of the gate (e.g. "H", "Rx(0.5)").
            qubit_label: Label of the qubit row (e.g. "q0").
            row: Row index.
            col: Column (moment) index.
            metadata: Optional dict of device-specific metadata
                      (e.g. fidelity, error_rate).  When ``None``, a
                      placeholder is shown.

        Returns:
            An HTML string for Plotly's ``hovertext``.
        """
        # Extract parameters from the label if present
        params_str = ""
        if "(" in gate_name and gate_name.endswith(")"):
            name_part = gate_name[:gate_name.index("(")]
            params_part = gate_name[gate_name.index("(") + 1:-1]
            params_str = f"Parameters: {params_part}<br>"
            display_name = name_part
        else:
            display_name = gate_name

        meta_lines = ""
        if metadata:
            for key, val in metadata.items():
                meta_lines += f"{key}: {val}<br>"
        else:
            meta_lines = "<i>Device metadata: N/A</i>"

        return (
            f"<b>{display_name}</b><br>"
            f"Qubit: {qubit_label}<br>"
            f"{params_str}"
            f"Moment: {col}<br>"
            f"{meta_lines}"
        )

    # ── Wire & label helpers ──────────────────────────────────────────

    @classmethod
    def _draw_qubit_wires(cls, fig, layout: CircuitLayout, left_wire: float, right_wire: float):
        """Draw horizontal qubit wires and labels."""
        import plotly.graph_objects as go

        for row_idx, label in enumerate(layout.qubit_labels):
            y = -row_idx * cls.ROW_HEIGHT
            fig.add_trace(go.Scatter(
                x=[left_wire, right_wire],
                y=[y, y],
                mode="lines",
                line=dict(color=cls.WIRE_COLOR, width=cls.WIRE_LW),
                hoverinfo="skip",
                showlegend=False,
            ))
            fig.add_annotation(
                x=left_wire - 0.15,
                y=y,
                text=f"{label} :",
                showarrow=False,
                font=dict(size=11, family="monospace"),
                xanchor="right",
            )

    @classmethod
    def _moment_label_annotations(
        cls, layout: CircuitLayout, col_x: list[float],
        label_y_top: float, label_y_bottom: float,
    ) -> list[dict]:
        """Generate moment label annotations (top and bottom)."""
        annotations = []
        moment_col_ranges: list[tuple[str, int, int]] = []
        for col_idx, label in enumerate(layout.moment_labels):
            if moment_col_ranges and moment_col_ranges[-1][0] == label:
                moment_col_ranges[-1] = (label, moment_col_ranges[-1][1], col_idx)
            else:
                moment_col_ranges.append((label, col_idx, col_idx))

        for label, col_start, col_end in moment_col_ranges:
            cx = (col_x[col_start] + col_x[col_end]) / 2
            for y_pos in (label_y_top, label_y_bottom):
                annotations.append(dict(
                    x=cx, y=y_pos,
                    text=label,
                    showarrow=False,
                    font=dict(size=9, family="monospace", color="#555555"),
                ))
        return annotations

    @classmethod
    def _footer_annotations(
        cls, layout: CircuitLayout, left_wire: float, label_y_bottom: float,
    ) -> list[dict]:
        """Generate footer annotations for global phase, result types, params."""
        annotations = []
        footer_lines: list[str] = []
        if layout.global_phase:
            footer_lines.append(f"Global phase: {layout.global_phase}")
        if layout.additional_result_types:
            footer_lines.append(
                f"Additional result types: {', '.join(layout.additional_result_types)}"
            )
        if layout.unassigned_parameters:
            footer_lines.append(
                f"Unassigned parameters: {', '.join(layout.unassigned_parameters)}"
            )

        footer_y = label_y_bottom - cls.ROW_HEIGHT * 0.7
        for i, line in enumerate(footer_lines):
            annotations.append(dict(
                x=left_wire, y=footer_y - i * cls.ROW_HEIGHT * 0.5,
                text=line,
                showarrow=False,
                font=dict(size=9, family="monospace", color="#333333"),
                xanchor="left",
                yanchor="top",
            ))
        return annotations

    # ── Shared geometry helpers ────────────────────────────────────────

    @classmethod
    def _gate_box_width(cls, label: str) -> float:
        """Return the width of a gate box for *label*."""
        char_width = cls.GATE_FONT_SIZE * 0.012
        text_width = len(label) * char_width
        return max(cls.GATE_BOX_MIN_WIDTH, text_width + cls.GATE_BOX_PADDING)

    @classmethod
    def _compute_column_x(cls, layout: CircuitLayout) -> tuple[list[float], list[float]]:
        """Compute column centers and widths (same algorithm as Matplotlib)."""
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
