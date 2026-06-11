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

"""Tests for PlotlyCircuitDiagram.

Each test mirrors a corresponding test in test_matplotlib_circuit_diagram.py.
Since graphical output cannot be compared as strings we verify:
  - build_diagram() returns a plotly Figure
  - _compute_layout() produces the correct layout primitives
  - Hover text contains correct gate information
  - Verbatim expand/collapse toggle data is correct
"""

import numpy as np
import pytest

from braket.circuits import Circuit, FreeParameter, Gate, Instruction, Noise, Observable, Operator
from braket.circuits.compiler_directives import Barrier
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
from braket.circuits.graphical_diagram_builders.plotly_circuit_diagram import (
    PlotlyCircuitDiagram,
    _CollapsibleRegion,
)
from braket.pulse import Frame, Port, PulseSequence

plotly = pytest.importorskip("plotly")
go = plotly.graph_objects


def _layout(circ: Circuit) -> CircuitLayout:
    return PlotlyCircuitDiagram._compute_layout(circ)


def _fig(circ: Circuit) -> go.Figure:
    return PlotlyCircuitDiagram.build_diagram(circ)


def _elements_of_type(layout: CircuitLayout, cls):
    return [e for e in layout.elements if isinstance(e, cls)]


def _gate_labels(layout: CircuitLayout) -> list[str]:
    return [e.label for e in layout.elements if isinstance(e, GateBox)]


# ── Basic rendering ──────────────────────────────────────────────────


def test_empty_circuit():
    fig = _fig(Circuit())
    assert isinstance(fig, go.Figure)


def test_only_gphase_circuit():
    fig = _fig(Circuit().gphase(0.1))
    assert isinstance(fig, go.Figure)


def test_one_gate_one_qubit():
    layout = _layout(Circuit().h(0))
    assert layout.qubit_labels == ["q0"]
    assert layout.num_moments == 1
    gates = _elements_of_type(layout, GateBox)
    assert len(gates) == 1
    assert gates[0] == GateBox(col=0, row=0, label="H")
    assert isinstance(_fig(Circuit().h(0)), go.Figure)


def test_one_gate_one_qubit_rotation():
    layout = _layout(Circuit().rx(angle=3.14, target=0))
    gates = _elements_of_type(layout, GateBox)
    assert len(gates) == 1
    assert gates[0].label == "Rx(3.14)"


def test_one_gate_one_qubit_rotation_with_parameter():
    theta = FreeParameter("theta")
    layout = _layout(Circuit().rx(angle=theta, target=0))
    gates = _elements_of_type(layout, GateBox)
    assert len(gates) == 1
    assert gates[0].label == "Rx(theta)"
    assert layout.unassigned_parameters == ["theta"]


@pytest.mark.parametrize("target", [0, 1])
def test_one_gate_with_global_phase(target):
    layout = _layout(Circuit().x(target=target).gphase(0.15))
    assert layout.global_phase == 0.15
    gates = _elements_of_type(layout, GateBox)
    assert any(g.label == "X" for g in gates)


def test_one_gate_with_zero_global_phase():
    layout = _layout(Circuit().gphase(-0.15).x(target=0).gphase(0.15))
    assert layout.global_phase == pytest.approx(0.0)


def test_one_gate_one_qubit_rotation_with_unicode():
    theta = FreeParameter("\u03b8")
    layout = _layout(Circuit().rx(angle=theta, target=0))
    gates = _elements_of_type(layout, GateBox)
    assert gates[0].label == "Rx(θ)"
    assert layout.unassigned_parameters == ["θ"]


def test_one_gate_with_parametric_expression_global_phase():
    theta = FreeParameter("\u03b8")
    circ = Circuit().x(target=0).gphase(2 * theta).x(0).gphase(1)
    layout = _layout(circ)
    assert layout.global_phase is not None
    assert layout.unassigned_parameters == ["θ"]


def test_one_gate_one_qubit_rotation_with_parameter_assigned():
    theta = FreeParameter("theta")
    circ = Circuit().rx(angle=theta, target=0)
    new_circ = circ.make_bound_circuit({"theta": np.pi})
    layout = _layout(new_circ)
    gates = _elements_of_type(layout, GateBox)
    assert gates[0].label == "Rx(3.14)"
    assert layout.unassigned_parameters == []


# ── Multi-qubit gates ────────────────────────────────────────────────


def test_qubit_width():
    layout = _layout(Circuit().h(0).h(100))
    assert layout.qubit_labels == ["q0", "q100"]
    assert layout.num_qubits == 2
    gates = _elements_of_type(layout, GateBox)
    assert len(gates) == 2
    assert all(g.label == "H" for g in gates)


def test_different_size_boxes():
    layout = _layout(Circuit().cnot(0, 1).rx(2, 0.3))
    gates = _elements_of_type(layout, GateBox)
    gate_labels = [g.label for g in gates]
    assert "X" in gate_labels
    assert "Rx(0.30)" in gate_labels
    controls = _elements_of_type(layout, ControlDot)
    assert len(controls) == 1
    assert controls[0].filled is True


def test_swap():
    layout = _layout(Circuit().swap(0, 2).x(1))
    swaps = _elements_of_type(layout, SwapMarker)
    assert len(swaps) == 2
    assert {s.row for s in swaps} == {0, 2}
    gates = _elements_of_type(layout, GateBox)
    assert any(g.label == "X" for g in gates)


def test_gate_width():
    class Foo(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["FOO"])

        def to_ir(self, target):
            return "foo"

    circ = Circuit().h(0).h(1).add_instruction(Instruction(Foo(), 0))
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert "FOO" in gate_labels_list
    assert gate_labels_list.count("H") == 2


def test_time_width():
    circ = Circuit()
    num_qubits = 8
    for qubit in range(num_qubits - 1):
        circ.cnot(qubit, qubit + 1)
    layout = _layout(circ)
    assert layout.num_qubits == 8
    assert layout.num_moments == 7
    gates = _elements_of_type(layout, GateBox)
    assert all(g.label == "X" for g in gates)
    controls = _elements_of_type(layout, ControlDot)
    assert len(controls) == 7
    connections = _elements_of_type(layout, Connection)
    assert len(connections) == 7


def test_connector_across_two_qubits():
    layout = _layout(Circuit().cnot(4, 3).h(range(2, 6)))
    connections = _elements_of_type(layout, Connection)
    assert any(c.row_start == 1 and c.row_end == 2 for c in connections)


def test_neg_control_qubits():
    layout = _layout(Circuit().x(1, control=[0, 2], control_state=[0, 1]))
    controls = _elements_of_type(layout, ControlDot)
    filled_states = {c.row: c.filled for c in controls}
    assert filled_states[0] is False
    assert filled_states[2] is True


def test_only_neg_control_qubits():
    layout = _layout(Circuit().x(2, control=[0, 1], control_state=0))
    controls = _elements_of_type(layout, ControlDot)
    assert len(controls) == 2
    assert all(c.filled is False for c in controls)


def test_connector_across_three_qubits():
    layout = _layout(Circuit().x(control=(3, 4), target=5).h(range(2, 6)))
    controls = _elements_of_type(layout, ControlDot)
    assert len(controls) == 2


def test_overlapping_qubits():
    circ = Circuit().cnot(0, 2).x(control=1, target=3).h(0)
    layout = _layout(circ)
    assert layout.num_moments >= 3
    gates = _elements_of_type(layout, GateBox)
    assert any(g.label == "H" for g in gates)


def test_overlapping_qubits_angled_gates():
    circ = Circuit().zz(0, 2, 0.15).x(control=1, target=3).h(0)
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert "ZZ(0.15)" in gate_labels_list
    assert "H" in gate_labels_list


def test_connector_across_gt_two_qubits():
    layout = _layout(Circuit().h(4).x(control=3, target=5).h(4).h(2))
    connections = _elements_of_type(layout, Connection)
    assert any(
        conn.row_start <= 2 <= conn.row_end for conn in connections
    )


def test_connector_across_non_used_qubits():
    layout = _layout(Circuit().h(4).cnot(3, 100).h(4).h(101))
    assert layout.num_qubits == 4  # q3, q4, q100, q101


# ── Verbatim blocks ──────────────────────────────────────────────────


def test_verbatim_1q_no_preceding():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0)))
    gate_labels_list = _gate_labels(layout)
    assert "StartVerbatim" in gate_labels_list
    assert "EndVerbatim" in gate_labels_list
    assert "H" in gate_labels_list


def test_verbatim_1q_preceding():
    layout = _layout(Circuit().h(0).add_verbatim_box(Circuit().h(0)))
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("H") == 2
    assert "StartVerbatim" in gate_labels_list
    assert "EndVerbatim" in gate_labels_list


def test_verbatim_1q_following():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0)).h(0))
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("H") == 2
    assert "StartVerbatim" in gate_labels_list
    assert "EndVerbatim" in gate_labels_list


def test_verbatim_2q_no_preceding():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)))
    gate_labels_list = _gate_labels(layout)
    assert "StartVerbatim" in gate_labels_list
    assert "EndVerbatim" in gate_labels_list
    assert "H" in gate_labels_list
    assert "X" in gate_labels_list


def test_verbatim_2q_preceding():
    layout = _layout(Circuit().h(0).add_verbatim_box(Circuit().h(0).cnot(0, 1)))
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("H") == 2


def test_verbatim_2q_following():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)).h(0))
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("H") == 2


def test_verbatim_3q_no_preceding():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2)))
    gate_labels_list = _gate_labels(layout)
    assert "StartVerbatim" in gate_labels_list
    assert "EndVerbatim" in gate_labels_list


def test_verbatim_3q_preceding():
    layout = _layout(Circuit().h(0).add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2)))
    assert isinstance(
        _fig(Circuit().h(0).add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2))), go.Figure
    )


def test_verbatim_3q_following():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2)).h(0))
    assert isinstance(
        _fig(Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1).cnot(1, 2)).h(0)), go.Figure
    )


def test_verbatim_different_qubits():
    circ = Circuit().h(1).add_verbatim_box(Circuit().h(0)).cnot(3, 4)
    layout = _layout(circ)
    assert layout.num_qubits == 4  # q0, q1, q3, q4


def test_verbatim_qubset_qubits():
    circ = Circuit().h(1).cnot(0, 1).cnot(1, 2).add_verbatim_box(Circuit().h(1)).cnot(2, 3)
    layout = _layout(circ)
    assert layout.num_qubits == 4


# ── Verbatim expand/collapse ─────────────────────────────────────────


def test_verbatim_collapse_regions_detected():
    """Collapsed regions should be found for verbatim boxes."""
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    layout = _layout(circ)
    regions = PlotlyCircuitDiagram._find_collapsible_regions(layout)
    assert len(regions) == 1
    assert regions[0].label == "Verbatim"
    assert regions[0].start_col < regions[0].end_col


def test_verbatim_collapse_region_inner_cols():
    """Inner columns should exclude start/end directive columns."""
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    layout = _layout(circ)
    regions = PlotlyCircuitDiagram._find_collapsible_regions(layout)
    region = regions[0]
    # Inner cols should be between start and end, not including them
    assert all(region.start_col < c < region.end_col for c in region.inner_cols)


def test_verbatim_collapse_toggle_buttons_present():
    """Figure for circuit with verbatim box should have toggle buttons."""
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)
    assert len(fig.layout.updatemenus) > 0
    button_labels = [
        b.label for menu in fig.layout.updatemenus for b in menu.buttons
    ]
    assert any("Expand" in label for label in button_labels)
    assert any("Collapse" in label for label in button_labels)


def test_no_toggle_buttons_without_verbatim():
    """Circuits without verbatim boxes should have no toggle buttons."""
    circ = Circuit().h(0).cnot(0, 1)
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)
    assert len(fig.layout.updatemenus) == 0


def test_verbatim_collapsed_region_rendering():
    """Collapsed region should render with appropriate shapes."""
    circ = Circuit().add_verbatim_box(Circuit().h(0))
    layout = _layout(circ)
    regions = PlotlyCircuitDiagram._find_collapsible_regions(layout)
    col_x, _ = PlotlyCircuitDiagram._compute_column_x(layout)
    shapes, annots = PlotlyCircuitDiagram._render_collapsed_region(regions[0], col_x)
    assert len(shapes) >= 1
    assert len(annots) >= 1
    assert "Verbatim" in annots[0]["text"]


# ── Ignore non-gate operators ────────────────────────────────────────


def test_ignore_non_gates():
    class Foo(Operator):
        @property
        def name(self) -> str:
            return "foo"

        def to_ir(self, target):
            return "foo"

    circ = Circuit().h(0).h(1).cnot(1, 2).add_instruction(Instruction(Foo(), 0))
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert "foo" not in gate_labels_list
    assert "H" in gate_labels_list


# ── Result types ─────────────────────────────────────────────────────


def test_single_qubit_result_types_target_none():
    layout = _layout(Circuit().h(0).probability())
    gate_labels_list = _gate_labels(layout)
    assert "Probability" in gate_labels_list


def test_result_types_target_none():
    layout = _layout(Circuit().h(0).h(100).probability())
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("Probability") == 2


def test_result_types_target_some():
    circ = (
        Circuit()
        .h(0)
        .h(1)
        .h(100)
        .expectation(observable=Observable.Y() @ Observable.Z(), target=[0, 100])
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert any("Expectation" in g for g in gate_labels_list)


def test_additional_result_types():
    circ = Circuit().h(0).h(1).h(100).state_vector().amplitude(["110", "001"])
    layout = _layout(circ)
    assert "StateVector" in layout.additional_result_types
    assert "Amplitude(110,001)" in layout.additional_result_types


def test_multiple_result_types():
    circ = (
        Circuit()
        .cnot(0, 2)
        .cnot(1, 3)
        .h(0)
        .variance(observable=Observable.Y(), target=0)
        .expectation(observable=Observable.Y(), target=2)
        .sample(observable=Observable.Y())
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert any("Variance" in g for g in gate_labels_list)
    assert any("Expectation" in g for g in gate_labels_list)
    assert any("Sample" in g for g in gate_labels_list)


def test_multiple_result_types_with_state_vector_amplitude():
    circ = (
        Circuit()
        .cnot(0, 2)
        .cnot(1, 3)
        .h(0)
        .variance(observable=Observable.Y(), target=0)
        .expectation(observable=Observable.Y(), target=3)
        .expectation(
            observable=Observable.Hermitian(np.array([[1.0, 0.0], [0.0, 1.0]])),
            target=1,
        )
        .amplitude(["0001"])
        .state_vector()
    )
    layout = _layout(circ)
    assert "Amplitude(0001)" in layout.additional_result_types
    assert "StateVector" in layout.additional_result_types


def test_multiple_result_types_with_custom_hermitian_ascii_symbol():
    herm_matrix = (Observable.Y() @ Observable.Z()).to_matrix()
    circ = (
        Circuit()
        .cnot(0, 2)
        .cnot(1, 3)
        .h(0)
        .variance(observable=Observable.Y(), target=0)
        .expectation(observable=Observable.Y(), target=3)
        .expectation(
            observable=Observable.Hermitian(
                matrix=herm_matrix,
                display_name="MyHerm",
            ),
            target=[1, 2],
        )
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert any("MyHerm" in g for g in gate_labels_list)


# ── Noise ─────────────────────────────────────────────────────────────


def test_noise_1qubit():
    layout = _layout(Circuit().h(0).x(1).bit_flip(1, 0.1))
    gate_labels_list = _gate_labels(layout)
    assert "BF(0.1)" in gate_labels_list


def test_noise_2qubit():
    layout = _layout(Circuit().h(1).kraus((0, 2), [np.eye(4)]))
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("KR") == 2


def test_noise_multi_probabilities():
    layout = _layout(Circuit().h(0).x(1).pauli_channel(1, 0.1, 0.2, 0.3))
    gate_labels_list = _gate_labels(layout)
    assert "PC(0.1,0.2,0.3)" in gate_labels_list


def test_noise_multi_probabilities_with_parameter():
    a = FreeParameter("a")
    c = FreeParameter("c")
    d = FreeParameter("d")
    layout = _layout(Circuit().h(0).x(1).pauli_channel(1, a, c, d))
    gate_labels_list = _gate_labels(layout)
    assert "PC(a,c,d)" in gate_labels_list
    assert sorted(layout.unassigned_parameters) == ["a", "c", "d"]


# ── Pulse gates ───────────────────────────────────────────────────────


def test_pulse_gate_1_qubit_circuit():
    circ = (
        Circuit()
        .h(0)
        .pulse_gate(0, PulseSequence().set_phase(Frame("x", Port("px", 1e-9), 1e9, 0), 0))
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert "PG" in gate_labels_list


def test_pulse_gate_multi_qubit_circuit():
    circ = (
        Circuit()
        .h(0)
        .pulse_gate([0, 1], PulseSequence().set_phase(Frame("x", Port("px", 1e-9), 1e9, 0), 0))
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("PG") == 2


# ── Nested targets ────────────────────────────────────────────────────


def test_circuit_with_nested_target_list():
    circ = (
        Circuit()
        .h(0)
        .h(1)
        .expectation(
            observable=(2 * Observable.Y()) @ (-3 * Observable.I())
            - 0.75 * Observable.Y() @ Observable.Z(),
            target=[[0, 1], [0, 1]],
        )
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert any("Hamiltonian" in g for g in gate_labels_list)


def test_hamiltonian():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .rx(0, FreeParameter("theta"))
        .adjoint_gradient(
            4 * (2e-5 * Observable.Z() + 2 * (3 * Observable.X() @ (2 * Observable.Y()))),
            [[0], [1, 2]],
        )
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert any("AdjointGradient" in g for g in gate_labels_list)
    assert layout.unassigned_parameters == ["theta"]


# ── Power ─────────────────────────────────────────────────────────────


def test_power():
    class Foo(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["FOO"])

    class CFoo(Gate):
        def __init__(self):
            super().__init__(qubit_count=2, ascii_symbols=["C", "FOO"])

    class FooFoo(Gate):
        def __init__(self):
            super().__init__(qubit_count=2, ascii_symbols=["FOO", "FOO"])

    circ = Circuit().h(0, power=1).h(1, power=0).h(2, power=-3.14)
    circ.add_instruction(Instruction(Foo(), 0, power=-1))
    circ.add_instruction(Instruction(CFoo(), (0, 1), power=2))
    circ.add_instruction(Instruction(CFoo(), (1, 2), control=0, power=3))
    circ.add_instruction(Instruction(FooFoo(), (1, 3), control=[0, 2], power=4))
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert "H" in gate_labels_list
    assert "H^0" in gate_labels_list
    assert "H^-3.14" in gate_labels_list
    assert "FOO^-1" in gate_labels_list
    assert "FOO^2" in gate_labels_list
    assert "FOO^3" in gate_labels_list
    assert "FOO^4" in gate_labels_list


def test_unbalanced_ascii_symbols():
    class FooFoo(Gate):
        def __init__(self):
            super().__init__(qubit_count=2, ascii_symbols=["FOOO", "FOO"])

    circ = Circuit().add_instruction(Instruction(FooFoo(), (1, 3), control=[0, 2], power=4))
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert "FOOO^4" in gate_labels_list
    assert "FOO^4" in gate_labels_list


# ── Measure ───────────────────────────────────────────────────────────


def test_measure():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).cnot(2, 3).measure([0, 2, 3])
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("M") == 3


def test_measure_with_multiple_measures():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).cnot(2, 3).measure([0, 2]).measure(3).measure(1)
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("M") == 4


def test_measure_multiple_instructions_after():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .cnot(1, 2)
        .cnot(2, 3)
        .measure(0)
        .measure(1)
        .h(3)
        .cnot(3, 4)
        .measure([2, 3])
    )
    layout = _layout(circ)
    assert layout.num_qubits == 5
    gate_labels_list = _gate_labels(layout)
    assert gate_labels_list.count("M") == 4


def test_measure_with_readout_noise():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .apply_readout_noise(Noise.BitFlip(probability=0.1), target_qubits=1)
        .measure([0, 1])
    )
    layout = _layout(circ)
    gate_labels_list = _gate_labels(layout)
    assert "BF(0.1)" in gate_labels_list
    assert gate_labels_list.count("M") == 2


# ── Barrier ───────────────────────────────────────────────────────────


def test_barrier_circuit_visualization_without_other_gates():
    layout = _layout(Circuit().barrier(target=[0, 100]))
    barriers = _elements_of_type(layout, BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 1]


def test_barrier_circuit_visualization_with_other_gates():
    layout = _layout(Circuit().x(0).barrier(target=[0, 100]).h(3))
    barriers = _elements_of_type(layout, BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 2]
    gate_labels_list = _gate_labels(layout)
    assert "X" in gate_labels_list
    assert "H" in gate_labels_list


def test_barrier_single_qubit():
    layout = _layout(Circuit().x(0).x(1).barrier(target=[0]).h(2))
    barriers = _elements_of_type(layout, BarrierMarker)
    assert len(barriers) == 1
    assert barriers[0].row == 0


def test_barrier_multiple_qubits_with_gates():
    layout = _layout(Circuit().x(0).x(1).barrier(target=[0, 1]).h(0).h(2))
    barriers = _elements_of_type(layout, BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 1]
    gate_labels_list = _gate_labels(layout)
    assert "X" in gate_labels_list
    assert "H" in gate_labels_list


def test_barrier_global_marks_all_qubits():
    circ = Circuit().x(0).x(1)
    circ.add_instruction(Instruction(Barrier([]), []))
    circ.h(2)
    layout = _layout(circ)
    barriers = _elements_of_type(layout, BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 1, 2]


def test_barrier_non_contiguous_target_marks_only_targeted_rows():
    circ = Circuit().h(0).h(1).h(2).barrier([0, 2]).cnot(0, 1).cnot(1, 2)
    layout = _layout(circ)
    barriers = _elements_of_type(layout, BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 2]


def test_barrier_contiguous_target_marks_each_targeted_row():
    circ = Circuit().h(0).h(1).h(2).barrier([0, 1]).cnot(0, 1)
    layout = _layout(circ)
    barriers = _elements_of_type(layout, BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 1]


def test_barrier_target_not_mutated_by_diagram():
    circ = Circuit()
    circ.h(0)
    circ.h(1)
    circ.h(2)
    circ.barrier([0, 1])
    circ.rx(2, 0.5)
    circ.cnot(0, 1)

    barrier_instr = circ.instructions[3]
    original_target = list(barrier_instr.target)
    assert len(original_target) == 2
    assert 0 in original_target
    assert 1 in original_target
    assert 2 not in original_target

    _fig(circ)

    assert len(barrier_instr.target) == 2
    assert 0 in barrier_instr.target
    assert 1 in barrier_instr.target
    assert 2 not in barrier_instr.target


# ── Hover tooltip content ─────────────────────────────────────────────


def test_hover_text_gate_name():
    """Hover text should include the gate name."""
    text = PlotlyCircuitDiagram._build_hover_text(
        gate_name="H", qubit_label="q0", row=0, col=0
    )
    assert "<b>H</b>" in text


def test_hover_text_qubit_label():
    """Hover text should include the qubit label."""
    text = PlotlyCircuitDiagram._build_hover_text(
        gate_name="H", qubit_label="q5", row=5, col=0
    )
    assert "q5" in text


def test_hover_text_parameters():
    """Hover text should include gate parameters when present."""
    text = PlotlyCircuitDiagram._build_hover_text(
        gate_name="Rx(3.14)", qubit_label="q0", row=0, col=0
    )
    assert "Parameters: 3.14" in text
    assert "<b>Rx</b>" in text


def test_hover_text_device_metadata_placeholder():
    """Hover text should include device metadata placeholder."""
    text = PlotlyCircuitDiagram._build_hover_text(
        gate_name="H", qubit_label="q0", row=0, col=0
    )
    assert "Device metadata" in text


def test_hover_text_with_metadata():
    """Hover text should include supplied device metadata."""
    text = PlotlyCircuitDiagram._build_hover_text(
        gate_name="H", qubit_label="q0", row=0, col=0,
        metadata={"fidelity": 0.998, "error_rate": 0.002},
    )
    assert "fidelity" in text
    assert "0.998" in text
    assert "error_rate" in text


def test_hover_text_moment_index():
    """Hover text should include the moment/column index."""
    text = PlotlyCircuitDiagram._build_hover_text(
        gate_name="H", qubit_label="q0", row=0, col=3
    )
    assert "Moment: 3" in text


def test_hover_traces_present_in_figure():
    """Build diagram should include hover-enabled traces for gates."""
    circ = Circuit().h(0).cnot(0, 1)
    fig = _fig(circ)
    # Find traces with hovertext
    hover_traces = [
        t for t in fig.data
        if hasattr(t, "hovertext") and t.hovertext is not None
    ]
    assert len(hover_traces) > 0


# ── Build diagram returns Figure ──────────────────────────────────────


@pytest.mark.parametrize(
    "circ",
    [
        Circuit().h(0),
        Circuit().cnot(0, 1),
        Circuit().h(0).cnot(0, 1).cnot(1, 2),
        Circuit().swap(0, 2).x(1),
        Circuit().x(1, control=[0, 2], control_state=[0, 1]),
        Circuit().h(0).h(1).h(100).state_vector(),
        Circuit().h(0).cnot(0, 1).measure([0, 1]),
    ],
    ids=[
        "single_h",
        "cnot",
        "chain",
        "swap_and_x",
        "neg_control",
        "state_vector",
        "measure",
    ],
)
def test_build_diagram_returns_figure(circ):
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)


def test_build_diagram_with_global_phase_footer():
    circ = Circuit().h(0).gphase(0.25)
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)


def test_build_diagram_with_unassigned_parameters_footer():
    circ = Circuit().rx(angle=FreeParameter("theta"), target=0)
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)


def test_build_diagram_with_barrier_and_following_gate():
    circ = Circuit().x(0).barrier(target=[0, 1]).h(0)
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)


def test_draw_elements_ignores_unknown_element():
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


# ── Circuit.show() integration ────────────────────────────────────────


def test_circuit_show_interactive():
    """circuit.show('interactive') should return a plotly Figure."""
    circ = Circuit().h(0).cnot(0, 1)
    fig = circ.show("interactive")
    assert isinstance(fig, go.Figure)


def test_circuit_show_static():
    """circuit.show() should still return a matplotlib Figure."""
    from matplotlib.figure import Figure as MplFigure

    circ = Circuit().h(0).cnot(0, 1)
    fig = circ.show("static")
    assert isinstance(fig, MplFigure)


def test_circuit_show_default_is_static():
    """circuit.show() with no args should default to matplotlib."""
    from matplotlib.figure import Figure as MplFigure

    circ = Circuit().h(0)
    fig = circ.show()
    assert isinstance(fig, MplFigure)


def test_circuit_show_invalid_mode():
    """circuit.show with an invalid mode should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown mode"):
        Circuit().h(0).show("invalid")


def test_circuit_show_with_explicit_class():
    """circuit.show with circuit_diagram_class should use that class."""
    circ = Circuit().h(0)
    fig = circ.show(circuit_diagram_class=PlotlyCircuitDiagram)
    assert isinstance(fig, go.Figure)


# ── Large circuit ─────────────────────────────────────────────────────


def test_large_circuit():
    """A large circuit should render without error."""
    circ = Circuit()
    for i in range(20):
        circ.h(i)
    for i in range(19):
        circ.cnot(i, i + 1)
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)


# ── Deeply nested verbatim blocks ─────────────────────────────────────


def test_circuit_with_multiple_verbatim_blocks():
    """Multiple verbatim boxes should each get their own region."""
    inner1 = Circuit().h(0)
    inner2 = Circuit().x(1)
    circ = Circuit().add_verbatim_box(inner1).add_verbatim_box(inner2)
    layout = _layout(circ)
    regions = PlotlyCircuitDiagram._find_collapsible_regions(layout)
    assert len(regions) == 2
    fig = _fig(circ)
    assert isinstance(fig, go.Figure)
