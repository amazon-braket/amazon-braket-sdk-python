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

# ruff: noqa: S101

from __future__ import annotations

import pytest
from plotly.graph_objects import Figure

from braket.circuits import Circuit, FreeParameter
from braket.circuits.graphical_diagram_builders.plotly_circuit_diagram import (
    PlotlyCircuitDiagram,
)


def _fig(circuit: Circuit) -> Figure:
    return PlotlyCircuitDiagram.build_diagram(circuit)


def _trace_texts(fig: Figure) -> list[str]:
    return [text for _, text in _trace_text_pairs(fig)]


def _trace_text_pairs(fig: Figure) -> list[tuple[object, str]]:
    pairs: list[tuple[object, str]] = []
    for trace in fig.data:
        trace_text = getattr(trace, "text", None)
        if trace_text is None:
            continue
        if isinstance(trace_text, str):
            pairs.append((trace, trace_text))
        else:
            pairs.extend((trace, str(text)) for text in trace_text)
    return pairs


def _hover_templates(fig: Figure) -> list[str]:
    return [
        trace.hovertemplate
        for trace in fig.data
        if getattr(trace, "hovertemplate", None) is not None
    ]


def test_empty_circuit_returns_figure() -> None:
    fig = _fig(Circuit())
    assert isinstance(fig, Figure)
    assert "(empty circuit)" in fig.layout.annotations[0].text


def test_only_global_phase_returns_figure() -> None:
    fig = _fig(Circuit().gphase(0.1))
    assert isinstance(fig, Figure)
    assert "Global phase: 0.1" in fig.layout.annotations[0].text


def test_single_qubit_gate_hover_text() -> None:
    fig = _fig(Circuit().h(0))
    hover = "\n".join(_hover_templates(fig))
    assert "Gate name: H" in hover
    assert "Target qubit(s): q0" in hover
    assert "Gate parameters: None" in hover
    assert "Device metadata: Not provided" in hover


def test_parameterized_gate_hover_text_and_footer() -> None:
    theta = FreeParameter("theta")
    fig = _fig(Circuit().rx(0, theta))
    hover = "\n".join(_hover_templates(fig))
    annotations = "\n".join(annotation.text for annotation in fig.layout.annotations)
    assert "Gate name: Rx" in hover
    assert "Gate parameters: theta" in hover
    assert "Unassigned parameters: theta" in annotations


def test_device_metadata_hook_appears_in_hover_text() -> None:
    fig = PlotlyCircuitDiagram.build_diagram(
        Circuit().h(0),
        device_metadata={"H:q0": {"fidelity": 0.99}},
    )
    hover = "\n".join(_hover_templates(fig))
    assert "Device metadata: {'fidelity': 0.99}" in hover


def test_multi_qubit_gate_draws_control_connection_and_target() -> None:
    fig = _fig(Circuit().cnot(0, 1))
    hover = "\n".join(_hover_templates(fig))
    assert "Control qubit: q0" in hover
    assert "Gate name: X" in hover
    assert "Target qubit(s): q1" in hover
    assert any(trace.mode == "lines" for trace in fig.data)


def test_large_circuit_returns_zoomable_figure() -> None:
    circuit = Circuit()
    for qubit in range(8):
        circuit.h(qubit)
    for qubit in range(7):
        circuit.cnot(qubit, qubit + 1)

    fig = _fig(circuit)
    assert isinstance(fig, Figure)
    assert fig.layout.hovermode == "closest"
    assert fig.layout.xaxis.visible is False
    assert fig.layout.yaxis.visible is False


def test_verbatim_block_collapsed_by_default_and_expandable() -> None:
    fig = _fig(Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)))
    visible_texts = [text for trace, text in _trace_text_pairs(fig) if trace.visible is not False]
    hidden_texts = [text for trace, text in _trace_text_pairs(fig) if trace.visible is False]

    assert PlotlyCircuitDiagram.VERBATIM_LABEL in _trace_texts(fig)
    assert PlotlyCircuitDiagram.VERBATIM_LABEL in visible_texts
    assert "H" in hidden_texts
    assert "X" in hidden_texts
    assert fig.layout.updatemenus[0].buttons[0].label == "Collapse verbatim boxes"
    assert fig.layout.updatemenus[0].buttons[1].label == "Expand verbatim boxes"


def test_multiple_verbatim_blocks_use_same_toggle() -> None:
    circuit = Circuit().add_verbatim_box(Circuit().h(0)).x(0)
    circuit += Circuit().add_verbatim_box(Circuit().cnot(0, 1))

    fig = _fig(circuit)
    assert _trace_texts(fig).count(PlotlyCircuitDiagram.VERBATIM_LABEL) == 2
    assert len(fig.layout.updatemenus[0].buttons) == 2


def test_circuit_show_interactive_returns_plotly_figure() -> None:
    fig = Circuit().h(0).show("interactive")
    assert isinstance(fig, Figure)


@pytest.mark.parametrize("diagram_name", ["plotly", "interactive"])
def test_circuit_show_string_aliases(diagram_name: str) -> None:
    assert isinstance(Circuit().h(0).show(diagram_name), Figure)


def test_circuit_show_unknown_string_raises() -> None:
    with pytest.raises(ValueError, match="Unknown circuit diagram type"):
        Circuit().h(0).show("unknown")
