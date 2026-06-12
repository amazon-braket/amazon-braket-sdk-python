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

"""Unit tests for PlotlyCircuitDiagram."""

from __future__ import annotations

import pytest

pytest.importorskip("plotly")  # skip entire module if plotly not installed

import plotly.graph_objects as go  # noqa: E402
FigureType = go.Figure  # FigureWidget is a subclass; Figure is always available

from braket.circuits import Circuit  # noqa: E402
from braket.circuits.free_parameter import FreeParameter  # noqa: E402
from braket.circuits.graphical_diagram_builders.plotly_circuit_diagram import (  # noqa: E402
    PlotlyCircuitDiagram,
    _RenderState,
    _VerbatimBlock,
)


def _make_state(circuit: Circuit) -> _RenderState:
    layout = PlotlyCircuitDiagram._compute_layout(circuit)
    blocks = PlotlyCircuitDiagram._identify_blocks(circuit, layout)
    return _RenderState(layout=layout, verbatim_blocks=blocks)


def _collect_hover_texts(fig: go.FigureWidget) -> list[str]:
    texts: list[str] = []
    for trace in fig.data:
        ht = trace.hovertext
        if ht and isinstance(ht, str):
            texts.append(ht)
        elif ht and isinstance(ht, (list, tuple)):
            texts.extend(t for t in ht if t)
    return texts


def _collect_trace_texts(fig: go.FigureWidget) -> list[str]:
    texts: list[str] = []
    for trace in fig.data:
        if trace.mode and "text" in trace.mode and trace.text:
            if isinstance(trace.text, str):
                texts.append(trace.text)
            else:
                texts.extend(t for t in trace.text if t)
    return texts


class TestBasicRendering:
    def test_empty_circuit_returns_figure(self):
        circ = Circuit()
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)

    def test_single_qubit_gate(self):
        circ = Circuit().h(0)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)
        texts = _collect_trace_texts(fig)
        assert any("H" in t for t in texts), f"H gate label not found; trace texts: {texts}"

    def test_multi_qubit_gate_cnot(self):
        circ = Circuit().cnot(0, 1)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)
        texts = _collect_trace_texts(fig)
        hovers = _collect_hover_texts(fig)
        assert any("X" in t for t in texts), f"CNOT target 'X' label not found; texts: {texts}"
        assert any("Control" in h for h in hovers), f"Control hover not found; hovers: {hovers}"

    def test_multi_qubit_gate_swap(self):
        circ = Circuit().swap(0, 1)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)
        swap_traces = [t for t in fig.data if t.mode and "markers" in t.mode]
        assert any("SWAP" in (t.hovertext or "") for t in swap_traces), (
            "SWAP hover text not found"
        )

    def test_circuit_with_multiple_qubits(self):
        circ = Circuit().h(0).h(1).h(2).cnot(0, 2)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)
        # Should have wire labels q0, q1, q2
        texts = _collect_trace_texts(fig)
        assert any("q0" in t for t in texts)
        assert any("q2" in t for t in texts)

    def test_large_circuit_does_not_crash(self):
        circ = Circuit()
        for q in range(10):
            circ.h(q)
        for q in range(9):
            circ.cnot(q, q + 1)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)


class TestParameterizedGates:
    def test_rotation_gate_rx(self):
        circ = Circuit().rx(0, 0.5)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        texts = _collect_trace_texts(fig)
        assert any("Rx" in t or "rx" in t.lower() for t in texts), (
            f"Rx label not found; texts: {texts}"
        )

    def test_rotation_gate_rz(self):
        circ = Circuit().rz(0, 1.57)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        texts = _collect_trace_texts(fig)
        assert any("Rz" in t or "rz" in t.lower() for t in texts)

    def test_free_parameter_gate(self):
        theta = FreeParameter("theta")
        circ = Circuit().rx(0, theta)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)
        title_text = fig.layout.title.text or ""
        assert "theta" in title_text, (
            f"Unassigned parameter 'theta' not in title: {title_text!r}"
        )

    def test_multiple_parameterized_gates(self):
        theta = FreeParameter("theta")
        phi = FreeParameter("phi")
        circ = Circuit().rx(0, theta).ry(1, phi)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        title_text = fig.layout.title.text or ""
        assert "theta" in title_text
        assert "phi" in title_text


class TestHoverTooltips:
    def test_hover_contains_gate_name(self):
        circ = Circuit().h(0)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        hovers = _collect_hover_texts(fig)
        assert any("H" in h for h in hovers), f"Gate name 'H' not in hovers: {hovers}"

    def test_hover_contains_qubit_row(self):
        circ = Circuit().h(0)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        hovers = _collect_hover_texts(fig)
        assert any("Qubit row" in h for h in hovers), f"'Qubit row' not in hovers: {hovers}"

    def test_hover_metadata_placeholder(self):
        circ = Circuit().h(0)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        hovers = _collect_hover_texts(fig)
        # Without device_metadata, placeholder should say N/A
        assert any("N/A" in h for h in hovers), f"metadata placeholder N/A not found: {hovers}"

    def test_hover_custom_device_metadata(self):
        circ = Circuit().h(0)
        fig = PlotlyCircuitDiagram.build_diagram(circ, device_metadata={"H": "fidelity: 0.999"})
        hovers = _collect_hover_texts(fig)
        assert any("fidelity: 0.999" in h for h in hovers), (
            f"custom metadata not found in hovers: {hovers}"
        )

    def test_hover_control_dot(self):
        circ = Circuit().cnot(0, 1)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        hovers = _collect_hover_texts(fig)
        assert any("Control" in h for h in hovers), f"'Control' not in hovers: {hovers}"

    def test_hover_swap_marker(self):
        circ = Circuit().swap(0, 1)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        hovers = _collect_hover_texts(fig)
        assert any("SWAP" in h for h in hovers), f"'SWAP' not in hovers: {hovers}"


class TestVerbatimBoxes:
    def _make_verbatim_circuit(self) -> Circuit:
        inner = Circuit().h(0).cnot(0, 1)
        circ = Circuit().add_verbatim_box(inner)
        return circ

    def test_verbatim_blocks_detected(self):
        circ = self._make_verbatim_circuit()
        state = _make_state(circ)
        assert len(state.verbatim_blocks) == 1
        block = state.verbatim_blocks[0]
        assert block.col_start < block.col_end

    def test_collapsed_state_by_default(self):
        circ = self._make_verbatim_circuit()
        state = _make_state(circ)
        assert not state.verbatim_blocks[0].expanded

    def test_collapsed_block_label_visible(self):
        circ = self._make_verbatim_circuit()
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        texts = _collect_trace_texts(fig)
        assert any("verbatim" in t.lower() for t in texts), (
            f"verbatim label not found in trace texts: {texts}"
        )

    def test_expanded_block_label_changes(self):
        circ = self._make_verbatim_circuit()
        state = _make_state(circ)
        state.verbatim_blocks[0].expanded = True
        fig = PlotlyCircuitDiagram._build_figure(state)
        texts = _collect_trace_texts(fig)
        assert any("expanded" in t.lower() for t in texts), (
            f"'expanded' label not found: {texts}"
        )

    def test_toggle_changes_state(self):
        circ = self._make_verbatim_circuit()
        state = _make_state(circ)
        assert not state.verbatim_blocks[0].expanded
        # Simulate toggling
        state.verbatim_blocks[0].expanded = True
        assert state.verbatim_blocks[0].expanded
        state.verbatim_blocks[0].expanded = False
        assert not state.verbatim_blocks[0].expanded

    def test_collapsed_hides_inner_gate_labels(self):
        circ = self._make_verbatim_circuit()
        state = _make_state(circ)
        fig = PlotlyCircuitDiagram._build_figure(state)
        texts = _collect_trace_texts(fig)
        inner_gate_labels = {"H", "CNOT"}
        found = {t for t in texts if t in inner_gate_labels}
        assert len(found) == 0, f"Inner gate labels visible in collapsed state: {found}"

    def test_expanded_shows_inner_gate_labels(self):
        circ = self._make_verbatim_circuit()
        state = _make_state(circ)
        state.verbatim_blocks[0].expanded = True
        fig = PlotlyCircuitDiagram._build_figure(state)
        texts = _collect_trace_texts(fig)
        assert any("H" in t for t in texts), f"H gate not visible when expanded: {texts}"

    def test_circuit_with_outer_and_verbatim_gates(self):
        inner = Circuit().h(0)
        circ = Circuit().rx(0, 0.3).add_verbatim_box(inner).rx(0, 0.3)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)

    def test_multiple_verbatim_blocks(self):
        inner = Circuit().h(0)
        circ = (
            Circuit()
            .add_verbatim_box(inner)
            .h(0)
            .add_verbatim_box(inner)
        )
        state = _make_state(circ)
        assert len(state.verbatim_blocks) == 2


class TestEdgeCases:
    def test_empty_circuit(self):
        circ = Circuit()
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)

    def test_global_phase_only_circuit(self):
        from braket.circuits.gates import GPhase
        circ = Circuit().add_instruction(__import__("braket.circuits", fromlist=["Instruction"]).Instruction(GPhase(0.5)))
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)

    def test_circuit_with_barrier(self):
        circ = Circuit().h(0).h(1).barrier([0, 1]).cnot(0, 1)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)

    def test_circuit_with_result_type(self):
        from braket.circuits import ResultType
        circ = Circuit().h(0).cnot(0, 1)
        circ.probability(target=[0, 1])
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)

    def test_figure_has_correct_qubit_count(self):
        circ = Circuit().h(0).h(1).h(2)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        texts = _collect_trace_texts(fig)
        qubit_labels = [t for t in texts if t.startswith("<b>q") and ":" in t]
        assert len(qubit_labels) == 3

    def test_deeply_nested_gates_do_not_crash(self):
        circ = Circuit()
        for _ in range(20):
            circ.h(0).cnot(0, 1).rx(0, 0.1)
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, go.Figure)


class TestCircuitAPIIntegration:
    def test_show_interactive_returns_figure_widget(self):
        circ = Circuit().h(0).cnot(0, 1)
        fig = circ.show("interactive")
        assert isinstance(fig, go.Figure)

    def test_show_default_still_works(self):
        import matplotlib.figure
        circ = Circuit().h(0)
        fig = circ.show()
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_show_unknown_string_raises(self):
        circ = Circuit().h(0)
        with pytest.raises(ValueError, match="Unknown renderer"):
            circ.show("unknown_renderer")

    def test_show_class_argument_still_works(self):
        from braket.circuits.graphical_diagram_builders.matplotlib_circuit_diagram import (
            MatplotlibCircuitDiagram,
        )
        import matplotlib.figure
        circ = Circuit().h(0)
        fig = circ.show(MatplotlibCircuitDiagram)
        assert isinstance(fig, matplotlib.figure.Figure)
