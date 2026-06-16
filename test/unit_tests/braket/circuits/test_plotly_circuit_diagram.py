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

"""Tests for PlotlyCircuitDiagram."""

# ruff: noqa: ANN001, ANN201, S101

import builtins

import numpy as np
import pytest

from braket.circuits import Circuit, FreeParameter, Observable
from braket.circuits.graphical_diagram_builders.graphical_diagram_utils import (
    BarrierMarker,
    CircuitLayout,
    Connection,
    GateBox,
)
from braket.circuits.graphical_diagram_builders.plotly_circuit_diagram import (
    PlotlyCircuitDiagram,
)

go = pytest.importorskip("plotly.graph_objects")


def _fig(circ: Circuit) -> go.Figure:
    return PlotlyCircuitDiagram.build_diagram(circ)


def _annotation_text(fig: go.Figure) -> list[str]:
    return [annotation.text for annotation in fig.layout.annotations]


def _visible_annotation_text(fig: go.Figure) -> list[str]:
    return [
        annotation.text
        for annotation in fig.layout.annotations
        if annotation.visible is None or annotation.visible
    ]


def _trace_text(fig: go.Figure, *, visible: bool | None = None) -> list[str]:
    text: list[str] = []
    for trace in fig.data:
        trace_visible = trace.visible if trace.visible is not None else True
        if visible is not None and trace_visible is not visible:
            continue
        if trace.text is None:
            continue
        if isinstance(trace.text, str):
            text.append(trace.text)
        else:
            text.extend(str(item) for item in trace.text)
    return text


def _figure_text(fig: go.Figure) -> list[str]:
    return _annotation_text(fig) + _trace_text(fig)


def _visible_figure_text(fig: go.Figure) -> list[str]:
    return _visible_annotation_text(fig) + _trace_text(fig, visible=True)


def _hover_templates(fig: go.Figure, *, visible: bool | None = None) -> list[str]:
    text: list[str] = []
    for trace in fig.data:
        trace_visible = trace.visible if trace.visible is not None else True
        if visible is not None and trace_visible is not visible:
            continue
        if not trace.hovertemplate:
            continue
        if trace.text is None:
            text.append(trace.hovertemplate)
        elif isinstance(trace.text, str):
            text.append(trace.text)
        else:
            text.extend(str(item) for item in trace.text)
    return text


def _figure_text_after_button(fig: go.Figure, button) -> list[str]:
    visible_by_trace = dict(zip(button.args[1], button.args[0]["visible"], strict=True))
    text: list[str] = []
    for index, trace in enumerate(fig.data):
        trace_visible = visible_by_trace.get(
            index,
            trace.visible if trace.visible is not None else True,
        )
        if not trace_visible or trace.text is None:
            continue
        if isinstance(trace.text, str):
            text.append(trace.text)
        else:
            text.extend(str(item) for item in trace.text)
    return _visible_annotation_text(fig) + text


def test_empty_circuit_returns_plotly_figure():
    fig = _fig(Circuit())
    assert isinstance(fig, go.Figure)
    assert "(empty circuit)" in _annotation_text(fig)


def test_only_gphase_circuit_returns_plotly_figure():
    fig = _fig(Circuit().gphase(0.1))
    assert isinstance(fig, go.Figure)
    assert "Global phase: 0.1" in _annotation_text(fig)


def test_one_gate_one_qubit_renders_gate_annotation_and_hover():
    fig = _fig(Circuit().h(0))
    assert isinstance(fig, go.Figure)
    assert "H" in _figure_text(fig)
    assert any(
        "Gate: H<br>Qubit: q0<br>Parameters: None"
        "<br>Device metadata: N/A (not attached)" in template
        for template in _hover_templates(fig)
    )
    assert any(trace.fill == "toself" for trace in fig.data)


def test_multi_qubit_gate_renders_control_and_connection_hover():
    fig = _fig(Circuit().cnot(0, 1))
    hover_templates = _hover_templates(fig)
    assert any("Control<br>Qubit: q0" in template for template in hover_templates)
    assert any("Gate: X<br>Qubit: q1" in template for template in hover_templates)
    assert any("Connection<br>From: q0<br>To: q1" in template for template in hover_templates)


def test_parameterized_gate_footer_lists_unassigned_parameter():
    theta = FreeParameter("theta")
    fig = _fig(Circuit().rx(angle=theta, target=0))
    assert "Rx(theta)" in _figure_text(fig)
    assert "Unassigned parameters: theta" in _figure_text(fig)
    assert any("Parameters: theta" in template for template in _hover_templates(fig))
    assert any(
        "Device metadata: N/A (not attached)" in template for template in _hover_templates(fig)
    )


def test_device_metadata_mapping_populates_gate_hover_from_operator_name():
    fig = PlotlyCircuitDiagram.build_diagram(
        Circuit().cnot(0, 1),
        device_metadata={"CNot": {"fidelity": 0.997, "duration": "35 ns"}},
    )

    assert any(
        "Gate: X<br>Qubit: q1<br>Parameters: None"
        "<br>Device metadata: fidelity: 0.997, duration: 35 ns" in template
        for template in _hover_templates(fig)
    )


def test_device_metadata_mapping_populates_gate_hover_from_rendered_label():
    theta = FreeParameter("theta")
    fig = PlotlyCircuitDiagram.build_diagram(
        Circuit().rx(angle=theta, target=0),
        device_metadata={"Rx(theta)": "calibrated"},
    )

    assert any(
        "Gate: Rx(theta)<br>Qubit: q0<br>Parameters: theta"
        "<br>Device metadata: calibrated" in template
        for template in _hover_templates(fig)
    )


@pytest.mark.parametrize("alias", ["interactive", "plotly"])
def test_circuit_show_forwards_device_metadata_to_plotly_alias(alias, monkeypatch):
    shown = {}

    def fake_show(self):
        shown["figure"] = self

    monkeypatch.setattr(go.Figure, "show", fake_show)

    result = (
        Circuit()
        .cnot(0, 1)
        .show(
            alias,
            device_metadata={"CNot": {"fidelity": 0.997, "duration": "35 ns"}},
        )
    )

    assert result is None
    fig = shown["figure"]
    assert isinstance(fig, go.Figure)
    assert any(
        "Gate: X<br>Qubit: q1<br>Parameters: None"
        "<br>Device metadata: fidelity: 0.997, duration: 35 ns" in template
        for template in _hover_templates(fig)
    )


def test_parameterized_gate_hover_uses_rendered_float_format():
    fig = _fig(Circuit().rx(0, 0.5))

    assert any(
        "Gate: Rx(0.50)<br>Qubit: q0<br>Parameters: 0.50" in template
        for template in _hover_templates(fig)
    )


def test_multi_parameter_gate_hover_uses_rendered_float_format():
    fig = _fig(Circuit().u(0, 0.1, 0.2, 0.3))

    assert any(
        "Gate: U(0.10, 0.20, 0.30)<br>Qubit: q0<br>Parameters: 0.10, 0.20, 0.30" in template
        for template in _hover_templates(fig)
    )


def test_powered_parameterized_gate_hover_uses_rendered_float_format():
    fig = _fig(Circuit().rx(0, 0.5, power=2))

    assert any(
        "Gate: Rx(0.50)^2<br>Qubit: q0<br>Parameters: 0.50" in template
        for template in _hover_templates(fig)
    )


def test_powered_gphase_after_gate_does_not_render_none_label():
    fig = _fig(Circuit().h(0).gphase(0.5, power=2))

    assert "Global phase: 1.0" in _annotation_text(fig)
    assert "None^2" not in _figure_text(fig)
    assert not any("Gate: None^2" in template for template in _hover_templates(fig))


def test_device_metadata_name_fallback_matches_parameterized_gate():
    fig = PlotlyCircuitDiagram.build_diagram(
        Circuit().rx(0, 0.5),
        device_metadata={"Rx": "native calibrated gate"},
    )

    assert any(
        "Gate: Rx(0.50)<br>Qubit: q0<br>Parameters: 0.50"
        "<br>Device metadata: native calibrated gate" in template
        for template in _hover_templates(fig)
    )


def test_device_metadata_empty_mapping_renders_not_attached():
    fig = PlotlyCircuitDiagram.build_diagram(Circuit().h(0), device_metadata={"H": {}})

    assert any(
        "Gate: H<br>Qubit: q0<br>Parameters: None"
        "<br>Device metadata: N/A (not attached)" in template
        for template in _hover_templates(fig)
    )


def test_additional_result_types_footer():
    fig = _fig(Circuit().h(0).state_vector().amplitude(["0"]))
    annotation_text = _annotation_text(fig)
    assert any(
        text == "Additional result types: StateVector, Amplitude(0)" for text in annotation_text
    )


def test_barrier_renders_shape_and_hover():
    fig = _fig(Circuit().x(0).barrier(target=[0]).h(1))
    assert any("Barrier<br>Qubit: q0" in template for template in _hover_templates(fig))
    assert any(
        trace.fill == "toself" and trace.fillcolor == PlotlyCircuitDiagram.BARRIER_FILL_COLOR
        for trace in fig.data
    )


def test_swap_renders_hover_marker():
    fig = _fig(Circuit().swap(0, 2).x(1))
    hover_templates = _hover_templates(fig)
    assert sum("SWAP<br>Qubit:" in template for template in hover_templates) == 2


def test_controlled_swap_renders_controls_swaps_and_connection():
    fig = _fig(Circuit().cswap(0, 1, 2))
    hover_templates = _hover_templates(fig)

    assert any("Control<br>Qubit: q0" in template for template in hover_templates)
    assert sum("SWAP<br>Qubit:" in template for template in hover_templates) == 2
    assert any("Connection<br>From: q0<br>To: q2" in template for template in hover_templates)


def test_measure_renders_gate_hover():
    fig = _fig(Circuit().h(0).measure(0))

    assert "M" in _figure_text(fig)
    assert any(
        "Gate: M<br>Qubit: q0<br>Parameters: None" in template for template in _hover_templates(fig)
    )


def test_unitary_renders_generic_gate_hover():
    fig = _fig(Circuit().unitary(matrix=np.array([[0, 1], [1, 0]]), targets=[0]))

    assert "U" in _figure_text(fig)
    assert any(
        "Gate: U<br>Qubit: q0<br>Parameters: None" in template for template in _hover_templates(fig)
    )


def test_observable_result_type_hover_uses_observable_parameter_text():
    fig = _fig(Circuit().h(0).expectation(observable=Observable.X(), target=0))

    assert "Expectation(X)" in _figure_text(fig)
    assert any(
        "Gate: Expectation(X)<br>Qubit: q0<br>Parameters: X" in template
        for template in _hover_templates(fig)
    )


def test_render_layout_ignores_unknown_element():
    class UnknownElement:
        col = 0
        row = 0

    layout = CircuitLayout(
        num_qubits=1,
        num_moments=1,
        qubit_labels=["q0"],
        moment_labels=["0"],
        elements=[GateBox(col=0, row=0, label="H"), UnknownElement()],
        global_phase=None,
        additional_result_types=[],
        unassigned_parameters=[],
    )
    fig = PlotlyCircuitDiagram._render_layout(layout)
    assert isinstance(fig, go.Figure)
    assert "H" in _figure_text(fig)


def test_circuit_show_accepts_plotly_alias(monkeypatch):
    shown = {}

    def fake_show(self):
        shown["figure"] = self

    monkeypatch.setattr(go.Figure, "show", fake_show)
    assert Circuit().h(0).show("plotly") is None
    assert isinstance(shown["figure"], go.Figure)


def test_circuit_show_accepts_interactive_alias(monkeypatch):
    shown = {}

    def fake_show(self):
        shown["figure"] = self

    monkeypatch.setattr(go.Figure, "show", fake_show)
    assert Circuit().h(0).show("interactive") is None
    assert isinstance(shown["figure"], go.Figure)


def test_circuit_show_rejects_unknown_diagram_alias():
    with pytest.raises(ValueError, match="interactive"):
        Circuit().h(0).show("unknown")


def test_missing_plotly_raises_helpful_error(monkeypatch):
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "plotly.graph_objects":
            raise ImportError("No module named plotly")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(ImportError, match=r"amazon-braket-sdk\[interactive\]"):
        PlotlyCircuitDiagram._get_plotly()


def test_global_phase_footer_in_rendered_layout():
    fig = _fig(Circuit().h(0).gphase(0.25))
    assert "Global phase: 0.25" in _annotation_text(fig)


def test_explicit_barrier_layout_element_renders():
    layout = CircuitLayout(
        num_qubits=1,
        num_moments=1,
        qubit_labels=["q0"],
        moment_labels=["0"],
        elements=[BarrierMarker(col=0, row=0)],
        global_phase=None,
        additional_result_types=[],
        unassigned_parameters=[],
    )
    fig = PlotlyCircuitDiagram._render_layout(layout)
    assert any("Barrier<br>Qubit: q0" in template for template in _hover_templates(fig))


def test_verbatim_block_collapses_by_default_and_can_expand():
    fig = _fig(Circuit().h(0).add_verbatim_box(Circuit().h(0).cnot(0, 1)).x(1))
    visible_text = _visible_figure_text(fig)
    assert "Verbatim" in visible_text
    assert "StartVerbatim" not in visible_text
    assert "EndVerbatim" not in visible_text
    assert len(fig.layout.updatemenus) == 1
    assert [button.label for button in fig.layout.updatemenus[0].buttons] == [
        "Collapse verbatim 1",
        "Expand verbatim 1",
    ]
    expanded_text = _figure_text_after_button(fig, fig.layout.updatemenus[0].buttons[1])
    assert "StartVerbatim" in expanded_text
    assert "EndVerbatim" in expanded_text


def test_verbatim_range_detection_deduplicates_multirow_boundaries():
    layout = PlotlyCircuitDiagram._compute_layout(
        Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    )
    assert PlotlyCircuitDiagram._find_verbatim_ranges(layout) == [(0, 3)]


def test_verbatim_range_detection_handles_nested_and_adjacent_blocks():
    nested_layout = PlotlyCircuitDiagram._compute_layout(
        Circuit().add_verbatim_box(Circuit().h(0).add_verbatim_box(Circuit().x(0)).y(0))
    )
    adjacent_layout = PlotlyCircuitDiagram._compute_layout(
        Circuit().add_verbatim_box(Circuit().h(0)).add_verbatim_box(Circuit().x(0))
    )

    assert PlotlyCircuitDiagram._find_verbatim_ranges(nested_layout) == [(0, 6)]
    assert PlotlyCircuitDiagram._find_verbatim_ranges(adjacent_layout) == [(0, 2), (3, 5)]


def test_nested_verbatim_expanded_state_renders_inner_gate_and_result_type():
    circuit = (
        Circuit()
        .add_verbatim_box(Circuit().h(0).add_verbatim_box(Circuit().rx(0, 0.5)).cnot(0, 1))
        .probability(target=[0])
    )

    fig = _fig(circuit)
    expanded_text = _figure_text_after_button(fig, fig.layout.updatemenus[0].buttons[1])

    assert any(text.startswith("Rx(") for text in expanded_text)
    assert "Probability" in expanded_text
    assert fig.to_json()


def test_verbatim_expanded_state_preserves_device_metadata():
    fig = PlotlyCircuitDiagram.build_diagram(
        Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)),
        device_metadata={"CNot": "two-qubit native"},
    )

    assert any(
        "Gate: X<br>Qubit: q1<br>Parameters: None<br>Device metadata: two-qubit native" in template
        for template in _hover_templates(fig, visible=False)
    )


def test_target_result_type_renders_as_result_type_column():
    fig = _fig(Circuit().h(0).probability(target=[0]))
    assert "Result Types" in _figure_text(fig)
    assert "Probability" in _figure_text(fig)


def test_anti_control_renders_open_control_hover():
    fig = _fig(Circuit().x(0, control=[1], control_state=[0]))
    assert any("Anti-control<br>Qubit: q1" in template for template in _hover_templates(fig))


def test_large_circuit_smoke_serializes_to_json():
    circuit = Circuit()
    for qubit in range(20):
        circuit.h(qubit)
    for qubit in range(19):
        circuit.cnot(qubit, qubit + 1)

    fig = _fig(circuit)

    assert fig.data
    assert fig.layout.width >= 500
    assert fig.layout.height >= 220
    assert fig.to_json()


def test_element_rows_returns_empty_for_unknown_element():
    class UnknownElement:
        col = 0
        row = 0

    assert PlotlyCircuitDiagram._element_rows(UnknownElement()) == set()


def test_adjacent_verbatim_boxes_have_independent_trace_buttons():
    fig = _fig(Circuit().add_verbatim_box(Circuit().h(0)).add_verbatim_box(Circuit().x(0)))

    assert len(fig.layout.updatemenus) == 2
    first_indices = set(fig.layout.updatemenus[0].buttons[1].args[1])
    second_indices = set(fig.layout.updatemenus[1].buttons[1].args[1])
    assert first_indices.isdisjoint(second_indices)
    assert "H" in _figure_text_after_button(fig, fig.layout.updatemenus[0].buttons[1])
    assert "X" in _figure_text_after_button(fig, fig.layout.updatemenus[1].buttons[1])


def test_gate_hover_points_are_batched_into_one_trace():
    fig = _fig(Circuit().h(0).x(1).y(2))

    transparent_hover_traces = [
        trace
        for trace in fig.data
        if trace.hovertemplate == "%{text}<extra></extra>"
        and trace.marker
        and trace.marker.color == "rgba(0,0,0,0)"
    ]
    assert len(transparent_hover_traces) == 1
    assert {"Gate: H", "Gate: X", "Gate: Y"}.issubset({
        text.split("<br>", maxsplit=1)[0] for text in transparent_hover_traces[0].text
    })


def test_non_verbatim_elements_remain_visible_when_verbatim_box_collapses():
    # Controls, swaps, connections and a barrier live outside the verbatim box, so they
    # must remain visible while only the verbatim box's own traces are toggled.
    circuit = Circuit().cnot(0, 1).swap(0, 1).barrier().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    fig = _fig(circuit)
    assert fig.to_json()


def test_build_collapsed_verbatim_elements_empty_range_spans_all_qubits():
    layout = CircuitLayout(
        num_qubits=3,
        num_moments=1,
        qubit_labels=["q0", "q1", "q2"],
        moment_labels=["0"],
        elements=[],
        global_phase=None,
        additional_result_types=[],
        unassigned_parameters=[],
    )
    elements = PlotlyCircuitDiagram._build_collapsed_verbatim_elements(layout, 0, 0, 0)
    gate_rows = sorted(elem.row for elem in elements if isinstance(elem, GateBox))
    assert gate_rows == [0, 1, 2]
    assert all(elem.label == "Verbatim" for elem in elements if isinstance(elem, GateBox))
    assert any(isinstance(elem, Connection) for elem in elements)


def test_build_collapsed_verbatim_elements_single_row_omits_connection():
    layout = CircuitLayout(
        num_qubits=3,
        num_moments=1,
        qubit_labels=["q0", "q1", "q2"],
        moment_labels=["0"],
        elements=[GateBox(col=0, row=1, label="H")],
        global_phase=None,
        additional_result_types=[],
        unassigned_parameters=[],
    )
    elements = PlotlyCircuitDiagram._build_collapsed_verbatim_elements(layout, 0, 0, 0)
    assert elements == [GateBox(col=0, row=1, label="Verbatim")]
    assert not any(isinstance(elem, Connection) for elem in elements)


def test_device_metadata_none_value_renders_not_attached():
    fig = PlotlyCircuitDiagram.build_diagram(Circuit().h(0), device_metadata={"H": None})
    assert any(
        "Device metadata: N/A (not attached)" in template for template in _hover_templates(fig)
    )


def test_format_device_metadata_none_renders_not_attached():
    assert PlotlyCircuitDiagram._format_device_metadata(None) == "N/A (not attached)"


def test_parameter_text_from_label_unclosed_parenthesis_returns_none():
    assert PlotlyCircuitDiagram._parameter_text_from_label("Rx(0.5") is None
