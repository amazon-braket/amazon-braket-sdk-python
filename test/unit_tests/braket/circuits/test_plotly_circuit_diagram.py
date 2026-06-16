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

Layout tests mirror the corresponding Matplotlib tests in
test_matplotlib_circuit_diagram.py.  When plotly is available the
figure-level tests also run.
"""

from __future__ import annotations

import numpy as np
import pytest

from braket.circuits import (
    Circuit,
    FreeParameter,
    Gate,
    Instruction,
    Noise,
    Observable,
    Operator,
)
from braket.circuits.compiler_directives import Barrier
from braket.circuits.graphical_diagram_builders import (
    graphical_diagram_utils as utils,
)
from braket.circuits.graphical_diagram_builders.plotly_circuit_diagram import (
    PlotlyCircuitDiagram,
)

pytest.importorskip(
    "braket.circuits.graphical_diagram_builders.plotly_circuit_diagram")

from braket.circuits.graphical_diagram_builders.plotly_circuit_diagram import (  # noqa: E402
    PlotlyCircuitDiagram,
    VerbatimRange,
)


# -- helpers ----------------------------------------------------------------

def _layout(circ: Circuit) -> utils.CircuitLayout:
    return PlotlyCircuitDiagram._compute_layout(circ)


def _elements_of_type(layout: utils.CircuitLayout, cls):
    return [e for e in layout.elements if isinstance(e, cls)]


def _gate_labels(layout: utils.CircuitLayout) -> list[str]:
    return [e.label for e in layout.elements if isinstance(e, utils.GateBox)]


def _tooltips(circ: Circuit) -> dict:
    layout = _layout(circ)
    return PlotlyCircuitDiagram._build_tooltips(circ, layout)


def _verbatim(circ: Circuit) -> list[VerbatimRange]:
    layout = _layout(circ)
    return PlotlyCircuitDiagram._detect_verbatim(circ, layout)


# -- empty / trivial --------------------------------------------------------

def test_empty_circuit():
    """Layout is valid even for a circuit with no instructions."""
    layout = _layout(Circuit())
    assert layout.num_qubits == 0
    assert layout.num_moments == 0


# -- single-qubit gates ----------------------------------------------------

def test_one_gate_one_qubit():
    layout = _layout(Circuit().h(0))
    assert layout.qubit_labels == ["q0"]
    assert layout.num_moments == 1
    gates = _elements_of_type(layout, utils.GateBox)
    assert len(gates) == 1
    assert gates[0] == utils.GateBox(col=0, row=0, label="H")


def test_one_gate_one_qubit_rotation():
    layout = _layout(Circuit().rx(angle=3.14, target=0))
    gates = _elements_of_type(layout, utils.GateBox)
    assert len(gates) == 1
    assert gates[0].label == "Rx(3.14)"


def test_one_gate_one_qubit_rotation_with_parameter():
    theta = FreeParameter("theta")
    layout = _layout(Circuit().rx(angle=theta, target=0))
    gates = _elements_of_type(layout, utils.GateBox)
    assert len(gates) == 1
    assert gates[0].label == "Rx(theta)"
    assert layout.unassigned_parameters == ["theta"]


@pytest.mark.parametrize("target", [0, 1])
def test_one_gate_with_global_phase(target):
    layout = _layout(Circuit().x(target=target).gphase(0.15))
    assert layout.global_phase == 0.15
    gates = _elements_of_type(layout, utils.GateBox)
    assert any(g.label == "X" for g in gates)


def test_one_gate_with_zero_global_phase():
    layout = _layout(Circuit().gphase(-0.15).x(target=0).gphase(0.15))
    assert layout.global_phase == pytest.approx(0.0)


def test_one_gate_one_qubit_rotation_with_unicode():
    theta = FreeParameter("\u03b8")
    layout = _layout(Circuit().rx(angle=theta, target=0))
    gates = _elements_of_type(layout, utils.GateBox)
    assert gates[0].label == "Rx(\u03b8)"
    assert layout.unassigned_parameters == ["\u03b8"]


def test_one_gate_with_parametric_expression_global_phase():
    theta = FreeParameter("\u03b8")
    circ = Circuit().x(target=0).gphase(2 * theta).x(0).gphase(1)
    layout = _layout(circ)
    assert layout.global_phase is not None
    assert layout.unassigned_parameters == ["\u03b8"]


def test_one_gate_one_qubit_rotation_with_parameter_assigned():
    theta = FreeParameter("theta")
    circ = Circuit().rx(angle=theta, target=0)
    new_circ = circ.make_bound_circuit({"theta": np.pi})
    layout = _layout(new_circ)
    gates = _elements_of_type(layout, utils.GateBox)
    assert gates[0].label == "Rx(3.14)"
    assert layout.unassigned_parameters == []


def test_qubit_width():
    layout = _layout(Circuit().h(0).h(100))
    assert layout.qubit_labels == ["q0", "q100"]
    assert layout.num_qubits == 2
    gates = _elements_of_type(layout, utils.GateBox)
    assert len(gates) == 2
    assert all(g.label == "H" for g in gates)


def test_different_size_boxes():
    layout = _layout(Circuit().cnot(0, 1).rx(2, 0.3))
    gates = _elements_of_type(layout, utils.GateBox)
    gate_labels = [g.label for g in gates]
    assert "X" in gate_labels
    assert "Rx(0.30)" in gate_labels
    controls = _elements_of_type(layout, utils.ControlDot)
    assert len(controls) == 1
    assert controls[0].filled is True


def test_swap():
    layout = _layout(Circuit().swap(0, 2).x(1))
    swaps = _elements_of_type(layout, utils.SwapMarker)
    assert len(swaps) == 2
    assert {s.row for s in swaps} == {0, 2}
    gates = _elements_of_type(layout, utils.GateBox)
    assert any(g.label == "X" for g in gates)


def test_gate_width():
    class Foo(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["FOO"])

        def to_ir(self, target):
            return "foo"

    circ = Circuit().h(0).h(1).add_instruction(Instruction(Foo(), 0))
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert "FOO" in gate_labels
    assert gate_labels.count("H") == 2


def test_time_width():
    circ = Circuit()
    num_qubits = 8
    for qubit in range(num_qubits - 1):
        circ.cnot(qubit, qubit + 1)
    layout = _layout(circ)
    assert layout.num_qubits == 8
    assert layout.num_moments == 7
    gates = _elements_of_type(layout, utils.GateBox)
    assert all(g.label == "X" for g in gates)
    controls = _elements_of_type(layout, utils.ControlDot)
    assert len(controls) == 7
    connections = _elements_of_type(layout, utils.Connection)
    assert len(connections) == 7


def test_connector_across_two_qubits():
    layout = _layout(Circuit().cnot(4, 3).h(range(2, 6)))
    connections = _elements_of_type(layout, utils.Connection)
    assert any(c.row_start == 1 and c.row_end == 2 for c in connections)


def test_neg_control_qubits():
    layout = _layout(Circuit().x(1, control=[0, 2], control_state=[0, 1]))
    controls = _elements_of_type(layout, utils.ControlDot)
    filled_states = {c.row: c.filled for c in controls}
    assert filled_states[0] is False
    assert filled_states[2] is True


def test_only_neg_control_qubits():
    layout = _layout(Circuit().x(2, control=[0, 1], control_state=0))
    controls = _elements_of_type(layout, utils.ControlDot)
    assert len(controls) == 2
    assert all(c.filled is False for c in controls)


def test_connector_across_three_qubits():
    layout = _layout(Circuit().x(control=(3, 4), target=5).h(range(2, 6)))
    controls = _elements_of_type(layout, utils.ControlDot)
    assert len(controls) == 2


def test_overlapping_qubits():
    circ = Circuit().cnot(0, 2).x(control=1, target=3).h(0)
    layout = _layout(circ)
    assert layout.num_moments >= 3
    gates = _elements_of_type(layout, utils.GateBox)
    assert any(g.label == "H" for g in gates)


def test_overlapping_qubits_angled_gates():
    circ = Circuit().zz(0, 2, 0.15).x(control=1, target=3).h(0)
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert "ZZ(0.15)" in gate_labels
    assert "H" in gate_labels


def test_connector_across_gt_two_qubits():
    layout = _layout(Circuit().h(4).x(control=3, target=5).h(4).h(2))
    connections = _elements_of_type(layout, utils.Connection)
    assert any(conn.row_start <= 2 <= conn.row_end for conn in connections)


def test_connector_across_non_used_qubits():
    layout = _layout(Circuit().h(4).cnot(3, 100).h(4).h(101))
    assert layout.num_qubits == 4


# -- verbatim boxes ---------------------------------------------------------

def test_verbatim_1q_no_preceding():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0)))
    gate_labels = _gate_labels(layout)
    assert "StartVerbatim" in gate_labels
    assert "EndVerbatim" in gate_labels
    assert "H" in gate_labels


def test_verbatim_1q_preceding():
    layout = _layout(Circuit().h(0).add_verbatim_box(Circuit().h(0)))
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("H") == 2
    assert "StartVerbatim" in gate_labels
    assert "EndVerbatim" in gate_labels


def test_verbatim_1q_following():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0)).h(0))
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("H") == 2
    assert "StartVerbatim" in gate_labels
    assert "EndVerbatim" in gate_labels


def test_verbatim_2q_no_preceding():
    layout = _layout(Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)))
    gate_labels = _gate_labels(layout)
    assert "StartVerbatim" in gate_labels
    assert "EndVerbatim" in gate_labels
    assert "H" in gate_labels
    assert "X" in gate_labels


def test_verbatim_2q_preceding():
    layout = _layout(
        Circuit().h(0).add_verbatim_box(
            Circuit().h(0).cnot(
                0, 1)))
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("H") == 2


def test_verbatim_2q_following():
    layout = _layout(
        Circuit().add_verbatim_box(
            Circuit().h(0).cnot(
                0, 1)).h(0))
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("H") == 2


def test_verbatim_3q_no_preceding():
    layout = _layout(
        Circuit().add_verbatim_box(
            Circuit().h(0).cnot(
                0,
                1).cnot(
                1,
                2)))
    gate_labels = _gate_labels(layout)
    assert "StartVerbatim" in gate_labels
    assert "EndVerbatim" in gate_labels


def test_verbatim_3q_preceding():
    layout = _layout(
        Circuit().h(0).add_verbatim_box(
            Circuit().h(0).cnot(
                0, 1).cnot(
                1, 2)))
    assert layout.num_moments >= 4


def test_verbatim_3q_following():
    layout = _layout(
        Circuit().add_verbatim_box(
            Circuit().h(0).cnot(
                0,
                1).cnot(
                1,
                2)).h(0))
    assert layout.num_moments >= 4


def test_verbatim_different_qubits():
    circ = Circuit().h(1).add_verbatim_box(Circuit().h(0)).cnot(3, 4)
    layout = _layout(circ)
    assert layout.num_qubits == 4


def test_verbatim_qubset_qubits():
    circ = Circuit().h(1).cnot(
        0,
        1).cnot(
        1,
        2).add_verbatim_box(
            Circuit().h(1)).cnot(
                2,
        3)
    layout = _layout(circ)
    assert layout.num_qubits == 4


# -- result types ----------------------------------------------------------

def test_single_qubit_result_types_target_none():
    layout = _layout(Circuit().h(0).probability())
    gate_labels = _gate_labels(layout)
    assert "Probability" in gate_labels


def test_result_types_target_none():
    layout = _layout(Circuit().h(0).h(100).probability())
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("Probability") == 2


def test_result_types_target_some():
    circ = Circuit().h(0).h(1).h(100).expectation(
        observable=Observable.Y() @ Observable.Z(), target=[0, 100]
    )
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert any("Expectation" in g for g in gate_labels)


def test_additional_result_types():
    circ = Circuit().h(0).h(1).h(100).state_vector().amplitude(["110", "001"])
    layout = _layout(circ)
    assert "StateVector" in layout.additional_result_types
    assert "Amplitude(110,001)" in layout.additional_result_types


def test_multiple_result_types():
    circ = Circuit().cnot(0, 2).cnot(1, 3).h(0).variance(
        observable=Observable.Y(), target=0
    ).expectation(observable=Observable.Y(), target=2).sample(
        observable=Observable.Y()
    )
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert any("Variance" in g for g in gate_labels)
    assert any("Expectation" in g for g in gate_labels)
    assert any("Sample" in g for g in gate_labels)


# -- noise ------------------------------------------------------------------

def test_noise_1qubit():
    layout = _layout(Circuit().h(0).x(1).bit_flip(1, 0.1))
    gate_labels = _gate_labels(layout)
    assert "BF(0.1)" in gate_labels


def test_noise_2qubit():
    layout = _layout(Circuit().h(1).kraus((0, 2), [np.eye(4)]))
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("KR") == 2


def test_noise_multi_probabilities():
    layout = _layout(Circuit().h(0).x(1).pauli_channel(1, 0.1, 0.2, 0.3))
    gate_labels = _gate_labels(layout)
    assert "PC(0.1,0.2,0.3)" in gate_labels


def test_noise_multi_probabilities_with_parameter():
    a = FreeParameter("a")
    c = FreeParameter("c")
    d = FreeParameter("d")
    layout = _layout(Circuit().h(0).x(1).pauli_channel(1, a, c, d))
    gate_labels = _gate_labels(layout)
    assert "PC(a,c,d)" in gate_labels
    assert sorted(layout.unassigned_parameters) == ["a", "c", "d"]


# -- pulse gates -----------------------------------------------------------

def test_pulse_gate_1_qubit_circuit():
    from braket.pulse import Frame, Port, PulseSequence

    circ = Circuit().h(0).pulse_gate(
        0, PulseSequence().set_phase(Frame("x", Port("px", 1e-9), 1e9, 0), 0)
    )
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert "PG" in gate_labels


def test_pulse_gate_multi_qubit_circuit():
    from braket.pulse import Frame, Port, PulseSequence

    circ = Circuit().h(0).pulse_gate(
        [0, 1],
        PulseSequence().set_phase(Frame("x", Port("px", 1e-9), 1e9, 0), 0),
    )
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("PG") == 2


# -- power ------------------------------------------------------------------

def test_power():
    class Foo(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["FOO"])

    class CFoo(Gate):
        def __init__(self):
            super().__init__(qubit_count=2, ascii_symbols=["C", "FOO"])

    circ = Circuit().h(0, power=1).h(1, power=0).h(2, power=-3.14)
    circ.add_instruction(Instruction(Foo(), 0, power=-1))
    circ.add_instruction(Instruction(CFoo(), (0, 1), power=2))
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert "H" in gate_labels
    assert "H^0" in gate_labels
    assert "H^-3.14" in gate_labels
    assert "FOO^-1" in gate_labels
    assert "FOO^2" in gate_labels


# -- measure ----------------------------------------------------------------

def test_measure():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).cnot(2, 3).measure([0, 2, 3])
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("M") == 3


def test_measure_with_multiple_measures():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).cnot(
        2, 3).measure([0, 2]).measure(3).measure(1)
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert gate_labels.count("M") == 4


# -- barrier ----------------------------------------------------------------

def test_barrier_circuit_visualization_without_other_gates():
    layout = _layout(Circuit().barrier(target=[0, 100]))
    barriers = _elements_of_type(layout, utils.BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 1]


def test_barrier_with_other_gates():
    layout = _layout(Circuit().x(0).barrier(target=[0, 100]).h(3))
    barriers = _elements_of_type(layout, utils.BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 2]
    gate_labels = _gate_labels(layout)
    assert "X" in gate_labels
    assert "H" in gate_labels


def test_barrier_single_qubit():
    layout = _layout(Circuit().x(0).x(1).barrier(target=[0]).h(2))
    barriers = _elements_of_type(layout, utils.BarrierMarker)
    assert len(barriers) == 1
    assert barriers[0].row == 0


def test_barrier_global_marks_all_qubits():
    circ = Circuit().x(0).x(1)
    circ.add_instruction(Instruction(Barrier([]), []))
    circ.h(2)
    layout = _layout(circ)
    barriers = _elements_of_type(layout, utils.BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 1, 2]


def test_barrier_non_contiguous_target():
    circ = Circuit().h(0).h(1).h(2).barrier([0, 2]).cnot(0, 1).cnot(1, 2)
    layout = _layout(circ)
    barriers = _elements_of_type(layout, utils.BarrierMarker)
    assert sorted(b.row for b in barriers) == [0, 2]


def test_barrier_target_not_mutated():
    circ = Circuit()
    circ.h(0).h(1).h(2).barrier([0, 1]).rx(2, 0.5).cnot(0, 1)
    barrier_instr = circ.instructions[3]
    original_target = list(barrier_instr.target)
    assert len(original_target) == 2

    _layout(circ)
    assert len(barrier_instr.target) == 2
    assert list(barrier_instr.target) == original_target


# -- ignore non-gate operators ---------------------------------------------

def test_ignore_non_gates():
    class Foo(Operator):
        @property
        def name(self) -> str:
            return "foo"

        def to_ir(self, target):
            return "foo"

    circ = Circuit().h(0).h(1).cnot(
        1, 2).add_instruction(
        Instruction(
            Foo(), 0))
    layout = _layout(circ)
    gate_labels = _gate_labels(layout)
    assert "foo" not in gate_labels
    assert "H" in gate_labels


# -- tooltip data -----------------------------------------------------------

def test_tooltip_single_gate():
    circ = Circuit().h(0)
    tt = _tooltips(circ)
    assert (0, 0) in tt
    assert tt[(0, 0)].gate_name == "H"
    assert tt[(0, 0)].target_qubits == "0"


def test_tooltip_parametrized_gate():
    circ = Circuit().rx(angle=0.5, target=1)
    tt = _tooltips(circ)
    assert (0, 0) in tt
    assert "Rx" in tt[(0, 0)].gate_name
    assert tt[(0, 0)].parameters != ""


def test_tooltip_multi_qubit_gate():
    circ = Circuit().cnot(0, 1)
    tt = _tooltips(circ)
    key = (0, 0) if (0, 0) in tt else (0, 1)
    assert tt[key].gate_name == "CNot"
    assert "0" in tt[key].target_qubits and "1" in tt[key].target_qubits


def test_tooltip_all_gates_have_entry():
    circ = Circuit().h(0).x(1).cnot(0, 1).rz(2, 0.25)
    layout = _layout(circ)
    tt = _tooltips(circ)
    gate_boxes = [e for e in layout.elements if isinstance(e, utils.GateBox)]
    for g in gate_boxes:
        if g.label in ("StartVerbatim", "EndVerbatim"):
            continue
        assert (
            g.col, g.row) in tt, f"Missing tooltip for {
            g.label} at ({
            g.col}, {
                g.row})"


# -- verbatim region detection ----------------------------------------------

def test_verbatim_detection_simple():
    circ = Circuit().add_verbatim_box(Circuit().h(0).x(0))
    vr = _verbatim(circ)
    assert len(vr) == 1
    assert vr[0].gate_count == 2


def test_verbatim_detection_multiple():
    circ = Circuit().h(0).add_verbatim_box(
        Circuit().x(0)).h(0).add_verbatim_box(
        Circuit().y(0))
    vr = _verbatim(circ)
    assert len(vr) == 2


def test_verbatim_detection_gate_count():
    circ = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1).rz(2, 0.5))
    vr = _verbatim(circ)
    assert len(vr) == 1
    assert vr[0].gate_count == 3


def test_no_verbatim_detected_when_absent():
    circ = Circuit().h(0).x(1).cnot(0, 1)
    vr = _verbatim(circ)
    assert len(vr) == 0


# -- column geometry --------------------------------------------------------

def test_col_geometry_single_column():
    layout = _layout(Circuit().h(0))
    col_x, col_w = PlotlyCircuitDiagram._col_geometry(layout)
    assert len(col_x) == 1
    assert len(col_w) == 1
    assert col_w[0] >= PlotlyCircuitDiagram.COL_WIDTH


def test_col_geometry_multiple_columns():
    layout = _layout(Circuit().h(0).x(0).cnot(0, 1))
    col_x, col_w = PlotlyCircuitDiagram._col_geometry(layout)
    assert len(col_x) >= 2


# -- updatemenu structure (requires plotly) ---------------------------------

@pytest.mark.skipif(
    not pytest.importorskip(
        "plotly.graph_objects",
        reason="plotly not installed"),
    reason="plotly not installed",
)
def test_build_diagram_returns_figure():
    """End-to-end smoke test that requires plotly to be installed."""
    from plotly.graph_objects import Figure

    for circ in [
        Circuit().h(0),
        Circuit().cnot(0, 1),
        Circuit().h(0).cnot(0, 1).cnot(1, 2),
        Circuit().swap(0, 2).x(1),
        Circuit().h(0).h(1).h(100).state_vector(),
        Circuit().h(0).cnot(0, 1).measure([0, 1]),
    ]:
        fig = PlotlyCircuitDiagram.build_diagram(circ)
        assert isinstance(fig, Figure)


@pytest.mark.skipif(
    not pytest.importorskip(
        "plotly.graph_objects",
        reason="plotly not installed"),
    reason="plotly not installed",
)
def test_figure_with_verbatim_has_updatemenu():
    from plotly.graph_objects import Figure

    circ = Circuit().h(0).add_verbatim_box(Circuit().x(0).y(0))
    fig = PlotlyCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert fig.layout.updatemenus is not None
    assert len(fig.layout.updatemenus) >= 1


@pytest.mark.skipif(
    not pytest.importorskip(
        "plotly.graph_objects",
        reason="plotly not installed"),
    reason="plotly not installed",
)
def test_empty_circuit_figure():
    from plotly.graph_objects import Figure

    fig = PlotlyCircuitDiagram.build_diagram(Circuit())
    assert isinstance(fig, Figure)


# -- show() / plotly() API ----------------------------------------------------

def test_show_returns_none():
    """show() should be side-effect only (returns None) for both backends."""
    circ = Circuit().h(0)
    assert circ.show() is None
    assert circ.show("interactive") is None


def test_plotly_returns_figure():
    """plotly() should return a go.Figure."""
    from plotly.graph_objects import Figure

    circ = Circuit().h(0)
    fig = circ.plotly()
    assert isinstance(fig, Figure)


def test_plotly_global_phase_only():
    """A circuit with only global phase should produce a non-empty figure."""
    from plotly.graph_objects import Figure

    circ = Circuit().gphase(0.5)
    fig = circ.plotly()
    assert isinstance(fig, Figure)


def test_plotly_empty_circuit():
    from plotly.graph_objects import Figure

    fig = Circuit().plotly()
    assert isinstance(fig, Figure)


# -- per-box updatemenus ------------------------------------------------------

def test_single_vb_has_one_updatemenu():
    from plotly.graph_objects import Figure

    circ = Circuit().h(0).add_verbatim_box(Circuit().x(0).y(0))
    fig = PlotlyCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert fig.layout.updatemenus is not None
    assert len(fig.layout.updatemenus) == 1
    assert len(fig.layout.updatemenus[0].buttons) == 2
    assert "Collapse box 1" in fig.layout.updatemenus[0].buttons[0].label
    assert "Expand box 1" in fig.layout.updatemenus[0].buttons[1].label


def test_multiple_vb_has_per_box_updatemenus():
    from plotly.graph_objects import Figure

    circ = (
        Circuit()
        .add_verbatim_box(Circuit().x(0))
        .h(0)
        .add_verbatim_box(Circuit().y(0))
    )
    fig = PlotlyCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert fig.layout.updatemenus is not None
    assert len(fig.layout.updatemenus) == 2
    for i, menu in enumerate(fig.layout.updatemenus):
        assert len(menu.buttons) == 2
        assert f"Collapse box {i + 1}" in menu.buttons[0].label
        assert f"Expand box {i + 1}" in menu.buttons[1].label


def test_no_vb_has_no_updatemenu():
    from plotly.graph_objects import Figure

    circ = Circuit().h(0).cnot(0, 1)
    fig = PlotlyCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert fig.layout.updatemenus is None or len(fig.layout.updatemenus) == 0


# -- figure title -------------------------------------------------------------

def test_figure_title_with_vb():
    circ = Circuit().add_verbatim_box(Circuit().x(0))
    fig = PlotlyCircuitDiagram.build_diagram(circ)
    assert "verbatim boxes collapsed" in fig.layout.title.text


def test_figure_title_without_vb():
    circ = Circuit().h(0)
    fig = PlotlyCircuitDiagram.build_diagram(circ)
    assert "verbatim" not in fig.layout.title.text


# -- trace consolidation ------------------------------------------------------

def test_large_circuit_trace_count():
    """A 50-gate circuit should produce far fewer traces than 2 per gate."""
    circ = Circuit()
    for i in range(50):
        circ.h(i % 10)
    fig = PlotlyCircuitDiagram.build_diagram(circ)
    n_traces = len(fig.data)
    # Structural traces + gate polygons + 1 text + 0 non-gate
    # Upper bound: wires(10) + qlabels(10) + moment_labels(≤100) + footer(0)
    #   + gate polygons(50) + gate text(1 consolidated) < 200
    assert n_traces < 200, f"Expected < 200 traces, got {n_traces}"


# -- verbatim detection edge cases -------------------------------------------

def test_verbatim_empty_box():
    """An empty verbatim box (no inner gates) should still produce a range."""
    from braket.circuits.compiler_directives import StartVerbatimBox, EndVerbatimBox

    circ = Circuit()
    circ.add_instruction(Instruction(StartVerbatimBox(), []))
    circ.add_instruction(Instruction(EndVerbatimBox(), []))
    vr = _verbatim(circ)
    assert len(vr) == 1
    assert vr[0].gate_count == 0
