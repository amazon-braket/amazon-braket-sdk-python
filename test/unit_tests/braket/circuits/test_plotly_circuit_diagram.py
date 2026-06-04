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

from plotly.graph_objects import Figure

from braket.circuits import Circuit, FreeParameter, circuit, result_types
from braket.circuits.graphical_diagram_builders.plotly_circuit_diagram import (
    PlotlyCircuitDiagram,
)


def _fig(circuit: Circuit) -> Figure:
    return PlotlyCircuitDiagram.build_diagram(circuit)


def _hovertemplates(fig: Figure) -> list[str]:
    return [trace.hovertemplate for trace in fig.data if getattr(trace, "hovertemplate", None)]


def test_empty_circuit_returns_plotly_figure():
    assert isinstance(_fig(Circuit()), Figure)


def test_only_global_phase_returns_plotly_figure():
    assert isinstance(_fig(Circuit().gphase(0.1)), Figure)


def test_single_and_multi_qubit_gate_hover_text():
    theta = FreeParameter("theta")
    fig = _fig(Circuit().h(0).cnot(0, 1).rx(1, theta))

    assert isinstance(fig, Figure)
    hovertemplates = "\n".join(_hovertemplates(fig))
    assert "Gate name: H" in hovertemplates
    assert "Gate name: X" in hovertemplates
    assert "Gate name: Rx" in hovertemplates
    assert "Target qubit: q1" in hovertemplates
    assert "Parameters: theta" in hovertemplates
    assert "Device metadata: unavailable" in hovertemplates


def test_large_circuit_renders_many_hoverable_traces():
    circuit = Circuit()
    for index in range(18):
        control = index % 5
        target = (index + 1) % 5
        circuit.h(control).cnot(control, target).rz(target, FreeParameter(f"theta_{index}"))

    fig = _fig(circuit)

    assert isinstance(fig, Figure)
    assert len(fig.data) > 40
    hovertemplates = "\n".join(_hovertemplates(fig))
    assert "Gate name: Rz" in hovertemplates
    assert "Parameters: theta_17" in hovertemplates


def test_nested_subroutine_circuit_renders_expanded_gates():
    @circuit.subroutine()
    def bell_pair(control, target):
        return Circuit().h(control).cnot(control, target)

    @circuit.subroutine()
    def chained_bell_pairs(targets):
        ordered_targets = list(targets)
        for index in range(len(ordered_targets) - 1):
            yield bell_pair(ordered_targets[index], ordered_targets[index + 1])

    fig = _fig(Circuit().add(chained_bell_pairs, [0, 1, 2]))
    trace_names = [trace.name or "" for trace in fig.data]

    assert any(name == "H on q0" for name in trace_names)
    assert any(name == "X on q1" for name in trace_names)
    assert any(name == "control on q0" for name in trace_names)


def test_result_types_and_footer_render():
    fig = _fig(
        Circuit()
        .h(0)
        .add_result_type(result_types.Probability(target=[0]))
        .add_result_type(result_types.StateVector())
    )

    assert any(
        "Additional result types" in annotation.text for annotation in fig.layout.annotations
    )
    assert any(trace.visible is True for trace in fig.data)


def test_verbatim_boxes_are_collapsed_by_default_and_expandable():
    fig = _fig(Circuit().h(0).add_verbatim_box(Circuit().x(0).cnot(0, 1)).h(1))

    collapsed_traces = [trace for trace in fig.data if "collapsed verbatim box" in trace.name]
    hidden_expanded = [
        trace
        for trace in fig.data
        if trace.name
        and ("StartVerbatim" in trace.name or "EndVerbatim" in trace.name or "X on" in trace.name)
        and trace.visible is False
    ]

    assert collapsed_traces
    assert all(trace.visible is True for trace in collapsed_traces)
    assert hidden_expanded
    assert fig.layout.updatemenus
    assert [button.label for button in fig.layout.updatemenus[0].buttons] == [
        "Collapse verbatim boxes",
        "Expand verbatim boxes",
    ]


def test_circuit_show_interactive_returns_plotly_figure():
    fig = Circuit().h(0).show("interactive")
    assert isinstance(fig, Figure)


def test_circuit_show_rejects_unknown_diagram_string():
    try:
        Circuit().h(0).show("unknown")
    except ValueError as error:
        assert "interactive" in str(error)
    else:
        raise AssertionError("Expected ValueError for unknown diagram string")
