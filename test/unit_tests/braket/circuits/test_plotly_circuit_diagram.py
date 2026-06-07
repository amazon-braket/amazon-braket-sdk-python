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


def _hover_templates(fig: go.Figure) -> list[str]:
    return [trace.hovertemplate for trace in fig.data if trace.hovertemplate]


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
    assert "H" in _annotation_text(fig)
    assert any(
        "Gate: H<br>Qubit: q0<br>Parameters: None"
        "<br>Device metadata: N/A (not attached)" in template
        for template in _hover_templates(fig)
    )
    assert any(shape.type == "rect" for shape in fig.layout.shapes)


def test_multi_qubit_gate_renders_control_and_connection_hover():
    fig = _fig(Circuit().cnot(0, 1))
    hover_templates = _hover_templates(fig)
    assert any("Control<br>Qubit: q0" in template for template in hover_templates)
    assert any("Gate: X<br>Qubit: q1" in template for template in hover_templates)
    assert any("Connection<br>From: q0<br>To: q1" in template for template in hover_templates)


def test_parameterized_gate_footer_lists_unassigned_parameter():
    theta = FreeParameter("theta")
    fig = _fig(Circuit().rx(angle=theta, target=0))
    assert "Rx(theta)" in _annotation_text(fig)
    assert "Unassigned parameters: theta" in _annotation_text(fig)
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
def test_circuit_show_forwards_device_metadata_to_plotly_alias(alias):
    fig = (
        Circuit()
        .cnot(0, 1)
        .show(
            alias,
            device_metadata={"CNot": {"fidelity": 0.997, "duration": "35 ns"}},
        )
    )

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
    assert "None^2" not in _annotation_text(fig)
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
        shape.type == "rect" and shape.fillcolor == PlotlyCircuitDiagram.BARRIER_FILL_COLOR
        for shape in fig.layout.shapes
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

    assert "M" in _annotation_text(fig)
    assert any(
        "Gate: M<br>Qubit: q0<br>Parameters: None" in template for template in _hover_templates(fig)
    )


def test_unitary_renders_generic_gate_hover():
    fig = _fig(Circuit().unitary(matrix=np.array([[0, 1], [1, 0]]), targets=[0]))

    assert "U" in _annotation_text(fig)
    assert any(
        "Gate: U<br>Qubit: q0<br>Parameters: None" in template for template in _hover_templates(fig)
    )


def test_observable_result_type_hover_uses_observable_parameter_text():
    fig = _fig(Circuit().h(0).expectation(observable=Observable.X(), target=0))

    assert "Expectation(X)" in _annotation_text(fig)
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
    assert "H" in _annotation_text(fig)


def test_circuit_show_accepts_plotly_alias():
    fig = Circuit().h(0).show("plotly")
    assert isinstance(fig, go.Figure)


def test_circuit_show_accepts_interactive_alias():
    fig = Circuit().h(0).show("interactive")
    assert isinstance(fig, go.Figure)


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
    annotation_text = _visible_annotation_text(fig)
    assert "Verbatim" in annotation_text
    assert "StartVerbatim" not in annotation_text
    assert "EndVerbatim" not in annotation_text
    assert len(fig.layout.updatemenus) == 1
    assert [button.label for button in fig.layout.updatemenus[0].buttons] == [
        "Collapse verbatim",
        "Expand verbatim",
    ]
    expanded_annotations = fig.layout.updatemenus[0].buttons[1].args[1]["annotations"]
    visible_expanded_annotations = [
        annotation["text"] for annotation in expanded_annotations if annotation["visible"]
    ]
    assert "StartVerbatim" in visible_expanded_annotations
    assert "EndVerbatim" in visible_expanded_annotations


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
    expanded_annotations = fig.layout.updatemenus[0].buttons[1].args[1]["annotations"]
    visible_expanded_annotations = [
        annotation["text"] for annotation in expanded_annotations if annotation["visible"]
    ]

    assert any(text.startswith("Rx(") for text in visible_expanded_annotations)
    assert "Probability" in visible_expanded_annotations
    assert fig.to_json()


def test_verbatim_expanded_state_preserves_device_metadata():
    fig = PlotlyCircuitDiagram.build_diagram(
        Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)),
        device_metadata={"CNot": "two-qubit native"},
    )

    expanded_hover_templates = [
        trace.hovertemplate for trace in fig.data if trace.hovertemplate and trace.visible is False
    ]

    assert any(
        "Gate: X<br>Qubit: q1<br>Parameters: None<br>Device metadata: two-qubit native" in template
        for template in expanded_hover_templates
    )


def test_target_result_type_renders_as_result_type_column():
    fig = _fig(Circuit().h(0).probability(target=[0]))
    assert "Result Types" in _annotation_text(fig)
    assert "Probability" in _annotation_text(fig)


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
