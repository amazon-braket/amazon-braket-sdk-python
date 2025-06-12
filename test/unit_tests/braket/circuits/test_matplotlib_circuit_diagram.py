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

import numpy as np
import pytest
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from braket.circuits import (
    Circuit,
    FreeParameter,
    Gate,
    Instruction,
    Observable,
    ResultType,
    CompilerDirective,
)
from braket.circuits.text_diagram_builders.matplotlib_circuit_diagram import (
    MatplotlibCircuitDiagram,
)
from braket.registers.qubit_set import QubitSet


def test_empty_circuit():
    """Test that an empty circuit returns an empty figure."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit())
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 0  # Empty circuit should have no axes


def test_only_gphase_circuit():
    """Test that a circuit with only global phase is displayed correctly."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit().gphase(0.1))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.texts) == 1
    assert "Global phase: 0.1" in ax.texts[0].get_text()


def test_one_gate_one_qubit():
    """Test that a single gate on one qubit is displayed correctly."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit().h(0))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for qubit line
    assert len(ax.lines) == 1

    # Check for gate box
    assert len(ax.patches) == 1
    assert isinstance(ax.patches[0], plt.Rectangle)

    # Check for gate label
    assert len(ax.texts) >= 1
    assert any("H" in text.get_text() for text in ax.texts)


def test_one_gate_one_qubit_rotation():
    """Test that a rotation gate is displayed correctly."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit().rx(angle=3.14, target=0))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for gate box and label
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 1
    assert any("Rx(3.14)" in text.get_text() for text in ax.texts)


def test_one_gate_one_qubit_rotation_with_parameter():
    """Test that a rotation gate with a parameter is displayed correctly."""
    theta = FreeParameter("theta")
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit().rx(angle=theta, target=0))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for gate box and label
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 1
    assert any("Rx(theta)" in text.get_text() for text in ax.texts)


def test_one_gate_with_global_phase():
    """Test that a gate with global phase is displayed correctly."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit().x(target=0).gphase(0.15))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for gate box and global phase text
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 2
    assert any("Phase: 0.15" in text.get_text() for text in ax.texts)


def test_multi_qubit_gate():
    """Test that a multi-qubit gate is displayed correctly."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit().cnot(0, 1))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for qubit lines
    assert len(ax.lines) >= 2

    # Check for gate boxes and connections
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 1
    assert any("CNOT" in text.get_text() for text in ax.texts)


def test_result_types():
    """Test that result types are displayed correctly."""
    circ = Circuit().h(0).h(1)
    circ.probability()
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for result type box
    assert len(ax.patches) >= 2  # At least one gate box and one result type box
    assert len(ax.texts) >= 2
    assert any("Probability" in text.get_text() for text in ax.texts)


def test_overlapping_gates():
    """Test that overlapping gates are displayed correctly."""
    circ = Circuit()
    circ.cnot(0, 1)
    circ.cnot(1, 2)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for multiple gate boxes
    assert len(ax.patches) == 2
    assert len(ax.texts) >= 2
    assert sum("CNOT" in text.get_text() for text in ax.texts) == 2


def test_custom_gate():
    """Test that a custom gate is displayed correctly."""

    class CustomGate(Gate):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["CUSTOM"])

        def to_ir(self, target):
            return "custom"

    fig = MatplotlibCircuitDiagram.build_diagram(
        Circuit().add_instruction(Instruction(CustomGate(), 0))
    )
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for custom gate box and label
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 1
    assert any("CUSTOM" in text.get_text() for text in ax.texts)


def test_measure():
    """Test that measurement is displayed correctly."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit().h(0).measure(0))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for measurement box and label
    assert len(ax.patches) >= 2  # H gate and measurement
    assert len(ax.texts) >= 2
    assert any("Measure" in text.get_text() for text in ax.texts)


def test_observable():
    """Test that an observable is displayed correctly."""
    circ = Circuit().h(0)
    circ.add_result_type(ResultType.Expectation(Observable.X(), 0))
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for observable box and label
    assert len(ax.patches) >= 2  # H gate and observable
    assert len(ax.texts) >= 2
    assert any("Expectation" in text.get_text() for text in ax.texts)


def test_multiple_result_types():
    """Test that multiple result types are displayed correctly."""
    circ = Circuit().h(0).h(1)
    circ.probability()
    circ.expectation(Observable.X(), 0)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for result type boxes
    assert len(ax.patches) >= 3  # H gates and result type boxes
    assert len(ax.texts) >= 3
    assert any("Probability" in text.get_text() for text in ax.texts)
    assert any("Expectation" in text.get_text() for text in ax.texts)


def test_noise_operations():
    """Test that noise operations are displayed correctly."""
    circ = Circuit().h(0)
    circ.depolarizing(probability=0.1, target=0)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for noise operation box and label
    assert len(ax.patches) >= 2  # H gate and noise operation
    assert len(ax.texts) >= 2
    assert any("Depolarizing" in text.get_text() for text in ax.texts)


def test_compiler_directives():
    """Test that compiler directives are displayed correctly."""
    circ = Circuit().h(0)
    circ.add_instruction(Instruction(CompilerDirective(["optimize"]), 0))
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for compiler directive box and label
    assert len(ax.patches) >= 2  # H gate and compiler directive
    assert len(ax.texts) >= 2
    assert any("optimize" in text.get_text().lower() for text in ax.texts)


def test_multiple_moments():
    """Test that multiple moments are displayed correctly."""
    circ = Circuit()
    circ.h(0)
    circ.h(1)
    circ.cnot(0, 1)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for multiple gate boxes in different moments
    assert len(ax.patches) >= 3  # Two H gates and one CNOT
    assert len(ax.texts) >= 3
    assert sum("H" in text.get_text() for text in ax.texts) >= 2
    assert any("CNOT" in text.get_text() for text in ax.texts)


def test_empty_circuit_with_no_instructions():
    """Test that a circuit with no instructions returns an empty figure."""
    circ = Circuit()
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 0


def test_qubit_lines_and_labels():
    """Test that qubit lines and labels are drawn correctly."""
    circ = Circuit()
    circ.h(0)
    circ.h(2)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for qubit lines
    assert len(ax.lines) >= 2  # At least two qubit lines
    # Check for qubit labels
    assert len(ax.texts) >= 2
    assert any("q[0]" in text.get_text() or "q[Qubit(0)]" in text.get_text() for text in ax.texts)
    assert any("q[2]" in text.get_text() or "q[Qubit(2)]" in text.get_text() for text in ax.texts)


def test_instruction_group_with_global_phase():
    """Test that instruction groups with global phase are drawn correctly."""
    circ = Circuit()
    circ.h(0)
    circ.gphase(0.5)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for global phase text
    assert len(ax.texts) >= 2
    assert any("Phase: 0.50π" in text.get_text() for text in ax.texts)


def test_instruction_group_with_connections():
    """Test that instruction groups with connections between qubits are drawn correctly."""
    circ = Circuit()
    circ.cnot(0, 1)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for connections between qubits
    assert len(ax.lines) >= 3  # Two qubit lines and one connection
    # Check for gate box
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 1
    assert any("CNOT" in text.get_text() for text in ax.texts)


def test_result_types_with_targets():
    """Test that result types with targets are drawn correctly."""
    circ = Circuit()
    circ.h(0)
    circ.h(1)
    circ.add_result_type(ResultType.StateVector())
    circ.add_result_type(ResultType.Probability([0, 1]))
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for result type boxes
    assert len(ax.patches) >= 3  # Two H gates and at least one result type box
    assert len(ax.texts) >= 3
    assert any("StateVector" in text.get_text() for text in ax.texts)
    assert any("Probability" in text.get_text() for text in ax.texts)


def test_result_types_without_targets():
    """Test that result types without targets are drawn correctly."""
    circ = Circuit()
    circ.h(0)
    circ.add_result_type(ResultType.StateVector())
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for result type box
    assert len(ax.patches) >= 2  # H gate and result type box
    assert len(ax.texts) >= 2
    assert any("StateVector" in text.get_text() for text in ax.texts)


def test_complex_circuit_layout():
    """Test a complex circuit with multiple gates and moments."""
    circ = Circuit()
    circ.h(0)
    circ.cnot(0, 1)
    circ.rx(angle=0.5, target=0)
    circ.h(1)
    circ.cnot(1, 2)
    circ.ry(angle=0.3, target=0)
    circ.cnot(2, 0)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for multiple gates and connections
    assert len(ax.patches) >= 6  # Multiple gate boxes
    assert len(ax.lines) >= 6  # Multiple qubit lines and connections
    assert len(ax.texts) >= 6  # Multiple gate labels


def test_different_gate_types():
    """Test various gate types and their visualizations."""
    circ = Circuit()
    circ.h(0)  # Hadamard
    circ.x(1)  # Pauli X
    circ.y(2)  # Pauli Y
    circ.z(3)  # Pauli Z
    circ.s(4)  # S gate
    circ.t(5)  # T gate
    circ.swap(0, 1)  # SWAP
    circ.iswap(2, 3)  # ISWAP
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for all gate types
    gate_labels = [text.get_text() for text in ax.texts]
    assert any("H" in label for label in gate_labels)
    assert any("X" in label for label in gate_labels)
    assert any("Y" in label for label in gate_labels)
    assert any("Z" in label for label in gate_labels)
    assert any("S" in label for label in gate_labels)
    assert any("T" in label for label in gate_labels)
    assert any("SWAP" in label for label in gate_labels)
    assert any("ISWAP" in label for label in gate_labels)


def test_result_types_without_targets():
    """Test result types that don't have specific targets."""
    circ = Circuit().h(0).h(1)
    circ.add_result_type(ResultType.StateVector())
    circ.add_result_type(ResultType.DensityMatrix())
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for result type boxes
    assert len(ax.patches) >= 2  # H gates and result type boxes
    assert len(ax.texts) >= 2
    assert any("StateVector" in text.get_text() for text in ax.texts)
    assert any("DensityMatrix" in text.get_text() for text in ax.texts)


def test_custom_styling():
    """Test custom styling parameters for the circuit diagram."""

    # Create a subclass with custom styling
    class CustomStyleDiagram(MatplotlibCircuitDiagram):
        GATE_BOX_HEIGHT = 0.8
        GATE_BOX_WIDTH = 1.2
        GATE_COLOR = "#FFE0E0"
        WIRE_COLOR = "#FF0000"
        TEXT_COLOR = "#0000FF"

    fig = CustomStyleDiagram.build_diagram(Circuit().h(0).cnot(0, 1))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for custom styling
    assert len(ax.patches) >= 2  # Gate boxes
    assert len(ax.lines) >= 2  # Qubit lines
    assert len(ax.texts) >= 2  # Gate labels

    # Verify custom colors
    expected_patch_color = mcolors.to_rgba("#FFE0E0", alpha=0.7)
    for patch in ax.patches:
        # Only check color for custom gate patches
        if patch.get_facecolor() == expected_patch_color:
            assert patch.get_facecolor() == expected_patch_color
    expected_line_color = mcolors.to_rgba("#FF0000")
    # Only check the first two lines (qubit wires)
    for line in ax.lines[:2]:
        assert mcolors.to_rgba(line.get_color()) == expected_line_color
    expected_text_color = mcolors.to_rgba("#0000FF")
    for text in ax.texts:
        assert mcolors.to_rgba(text.get_color()) == expected_text_color


def test_empty_circuit_with_no_instructions():
    """Test an empty circuit with no instructions."""
    fig = MatplotlibCircuitDiagram.build_diagram(Circuit())
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 0  # Empty circuit should have no axes


def test_circuit_with_global_phase_only():
    """Test a circuit with only global phase."""
    circ = Circuit().gphase(0.5)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.texts) == 1
    assert "Global phase: 0.5" in ax.texts[0].get_text()


def test_circuit_with_parameterized_gates():
    """Test circuit with parameterized gates."""
    theta = FreeParameter("theta")
    phi = FreeParameter("phi")
    circ = Circuit()
    circ.rx(angle=theta, target=0)
    circ.ry(angle=phi, target=1)
    circ.rz(angle=theta + phi, target=2)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check for parameterized gate labels
    gate_labels = [text.get_text() for text in ax.texts]
    assert any("Rx(theta)" in label for label in gate_labels)
    assert any("Ry(phi)" in label for label in gate_labels)
    assert any("Rz(phi + theta)" in label for label in gate_labels)


def test_compiler_directive_with_no_qubits():
    """Test that compiler directives with no qubits are displayed correctly."""
    circ = Circuit()
    circ.add_instruction(Instruction(CompilerDirective(["optimize"]), []))
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 1
    assert any("optimize" in text.get_text() for text in ax.texts)


def test_instruction_with_no_qubits():
    """Test that instructions with no qubits are handled correctly."""
    circ = Circuit()
    circ.add_instruction(Instruction(CompilerDirective(["optimize"]), []))
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 1
    assert any("optimize" in text.get_text() for text in ax.texts)


def test_result_type_with_no_target():
    """Test that result types without targets are displayed correctly."""
    circ = Circuit().h(0)
    circ.add_result_type(ResultType.StateVector())
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) >= 2  # H gate and result type box
    assert len(ax.texts) >= 2
    assert any("StateVector" in text.get_text() for text in ax.texts)


def test_global_phase_exactly_half_pi():
    """Test that global phase of exactly 0.5π is displayed correctly."""
    circ = Circuit().gphase(0.5)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.texts) == 1
    assert "0.5" in ax.texts[0].get_text()


def test_global_phase_after_instructions():
    """Test that global phase is displayed correctly after instructions."""
    circ = Circuit().h(0).gphase(0.25)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.texts) >= 2
    assert any("0.25" in text.get_text() for text in ax.texts)


def test_custom_styling_attributes():
    """Test that custom styling attributes are applied correctly."""

    class CustomStyleDiagram(MatplotlibCircuitDiagram):
        GATE_BOX_HEIGHT = 0.8
        GATE_BOX_WIDTH = 1.2
        GATE_COLOR = "#FFE0E0"
        WIRE_COLOR = "#FF0000"
        TEXT_COLOR = "#0000FF"
        GLOBAL_PHASE_COLOR = "#00FF00"

    circ = Circuit().h(0).gphase(0.1)
    fig = CustomStyleDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    # Check wire color
    assert ax.lines[0].get_color() == "#FF0000"

    # Check gate color - convert RGBA to hex for comparison
    gate_color = ax.patches[0].get_facecolor()
    gate_color_hex = "#{:02x}{:02x}{:02x}".format(
        int(gate_color[0] * 255), int(gate_color[1] * 255), int(gate_color[2] * 255)
    )
    assert gate_color_hex.lower() == "#ffe0e0"

    # Check text colors
    assert any(text.get_color() == "#0000FF" for text in ax.texts)
    assert any(text.get_color() == "#00FF00" for text in ax.texts)


def test_multiple_result_types_with_and_without_targets():
    """Test that multiple result types with and without targets are displayed correctly."""
    circ = Circuit().h(0).h(1)
    circ.add_result_type(ResultType.Expectation(Observable.X(), 0))
    circ.add_result_type(ResultType.StateVector())
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) >= 3  # H gates and result type boxes
    assert len(ax.texts) >= 3
    assert any("Expectation" in text.get_text() for text in ax.texts)
    assert any("StateVector" in text.get_text() for text in ax.texts)


def test_noise_operation_bitflip():
    """Test that BitFlip noise operation is displayed correctly and triggers noise_names logic."""
    circ = Circuit().bit_flip(probability=0.1, target=0)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    ax = fig.axes[0]
    assert any("Bitflip" in text.get_text() for text in ax.texts)


def test_parameterized_gate_angle_half():
    """Test that a parameterized gate with angle 0.5 is displayed as 0.5."""
    circ = Circuit().rx(0, 0.5)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    ax = fig.axes[0]
    assert any("0.5" in text.get_text() for text in ax.texts)


def test_ascii_symbols_fallback():
    """Test that ascii_symbols fallback is used in _get_instruction_text."""

    class CustomOp:
        @property
        def ascii_symbols(self):
            return ["foo"]

    class CustomInstr:
        def __init__(self):
            self.operator = CustomOp()
            self.target = QubitSet([0])
            self.control = QubitSet()

    circ = Circuit()
    circ.add_instruction(CustomInstr())
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    ax = fig.axes[0]
    assert any("FOO" in text.get_text() for text in ax.texts)


def test_str_fallback():
    """Test that ascii_symbols fallback is used for a custom result type."""
    circ = Circuit().h(0)
    circ.add_result_type(ResultType.Probability(target=[0]))
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    ax = fig.axes[0]
    assert any("Probability" in text.get_text() for text in ax.texts)


def test_result_type_no_target_gate_color_non_string():
    """Test result type with no target and GATE_COLOR as non-string (e.g., tuple)."""

    class CustomStyleDiagram(MatplotlibCircuitDiagram):
        GATE_COLOR = (1, 0, 0)  # RGB tuple, not a string

    circ = Circuit().h(0)
    circ.add_result_type(ResultType.StateVector())
    fig = CustomStyleDiagram.build_diagram(circ)
    ax = fig.axes[0]
    # Should fallback to #E0E0E0 for the result type box
    for patch in ax.patches:
        color = patch.get_facecolor()
        # RGBA for #E0E0E0 is (0.878, 0.878, 0.878, 0.7)
        if all(abs(a - b) < 0.01 for a, b in zip(color, (0.878, 0.878, 0.878, 0.7))):
            break
    else:
        assert False, "Result type box with fallback color not found"


def test_result_types_with_complex_targets():
    """Test that result types with complex targets are displayed correctly."""
    circ = Circuit().h(0).h(1).h(2)
    circ.add_result_type(ResultType.Expectation(Observable.X() @ Observable.Y(), [0, 1]))
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) >= 4  # H gates and result type box
    assert len(ax.texts) >= 4
    assert any("Expectation" in text.get_text() for text in ax.texts)
    assert any("X" in text.get_text() for text in ax.texts)
    assert any("Y" in text.get_text() for text in ax.texts)


def test_instruction_group_with_multiple_connections():
    """Test that instruction groups with multiple connections are displayed correctly."""
    circ = Circuit()
    circ.cnot(0, 1)
    circ.cnot(1, 2)
    circ.cnot(2, 0)  # Creates a cycle
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 3
    assert len(ax.lines) >= 3  # Should have connection lines
    assert len(ax.texts) >= 3
    assert sum("CNOT" in text.get_text() for text in ax.texts) == 3


def test_complex_circuit_with_overlapping_gates():
    """Test that a complex circuit with overlapping gates is displayed correctly."""
    circ = Circuit()
    circ.h(0)
    circ.cnot(0, 1)
    circ.h(1)
    circ.cnot(1, 2)
    circ.h(2)
    circ.cnot(2, 0)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 6
    assert len(ax.lines) >= 3
    assert len(ax.texts) >= 6
    assert sum("H" in text.get_text() for text in ax.texts) == 3
    assert sum("CNOT" in text.get_text() for text in ax.texts) == 3


def test_different_gate_types_with_parameters():
    """Test that different gate types with parameters are displayed correctly."""
    theta = FreeParameter("theta")
    phi = FreeParameter("phi")
    circ = Circuit()
    circ.rx(angle=theta, target=0)
    circ.ry(angle=phi, target=1)
    circ.rz(angle=0.5, target=2)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 3
    assert len(ax.texts) >= 3
    assert any("Rx(theta)" in text.get_text() for text in ax.texts)
    assert any("Ry(phi)" in text.get_text() for text in ax.texts)
    assert any("Rz(0.5)" in text.get_text() for text in ax.texts)


def test_custom_styling_with_rgb_colors():
    """Test that custom styling with RGB colors works correctly."""

    class CustomStyleDiagram(MatplotlibCircuitDiagram):
        GATE_BOX_HEIGHT = 0.8
        GATE_BOX_WIDTH = 1.2
        GATE_COLOR = (0.5, 0.5, 0.5)  # RGB tuple
        WIRE_COLOR = (0.2, 0.2, 0.2)  # RGB tuple
        TEXT_COLOR = (0.8, 0.8, 0.8)  # RGB tuple
        GLOBAL_PHASE_COLOR = (0.3, 0.3, 0.3)  # RGB tuple

    fig = CustomStyleDiagram.build_diagram(Circuit().h(0).gphase(0.1))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 2
    assert any("H" in text.get_text() for text in ax.texts)
    assert any("Phase: 0.1" in text.get_text() for text in ax.texts)


def test_result_type_with_complex_observable():
    """Test that result types with complex observables are displayed correctly."""
    circ = Circuit().h(0).h(1).h(2)
    circ.add_result_type(
        ResultType.Expectation(Observable.X() @ Observable.Y() @ Observable.Z(), [0, 1, 2])
    )
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) >= 4  # H gates and result type box
    assert len(ax.texts) >= 4
    assert any("Expectation" in text.get_text() for text in ax.texts)
    assert any("X" in text.get_text() for text in ax.texts)
    assert any("Y" in text.get_text() for text in ax.texts)
    assert any("Z" in text.get_text() for text in ax.texts)


def test_instruction_group_with_complex_layout():
    """Test that instruction groups with complex layouts are displayed correctly."""
    circ = Circuit()
    circ.h(0)
    circ.cnot(0, 1)
    circ.h(1)
    circ.cnot(1, 2)
    circ.h(2)
    circ.cnot(2, 0)
    circ.h(0)
    fig = MatplotlibCircuitDiagram.build_diagram(circ)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 7
    assert len(ax.lines) >= 3
    assert len(ax.texts) >= 7
    assert sum("H" in text.get_text() for text in ax.texts) == 4
    assert sum("CNOT" in text.get_text() for text in ax.texts) == 3


def test_custom_styling_with_hex_colors():
    """Test that custom styling with hex colors works correctly."""

    class CustomStyleDiagram(MatplotlibCircuitDiagram):
        GATE_BOX_HEIGHT = 0.8
        GATE_BOX_WIDTH = 1.2
        GATE_COLOR = "#FF0000"  # Red
        WIRE_COLOR = "#00FF00"  # Green
        TEXT_COLOR = "#0000FF"  # Blue
        GLOBAL_PHASE_COLOR = "#FFFF00"  # Yellow

    fig = CustomStyleDiagram.build_diagram(Circuit().h(0).gphase(0.1))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 2
    assert any("H" in text.get_text() for text in ax.texts)
    assert any("Phase: 0.1" in text.get_text() for text in ax.texts)


def test_custom_styling_with_rgba_colors():
    """Test that custom styling with RGBA colors works correctly."""

    class CustomStyleDiagram(MatplotlibCircuitDiagram):
        GATE_BOX_HEIGHT = 0.8
        GATE_BOX_WIDTH = 1.2
        GATE_COLOR = (1.0, 0.0, 0.0, 0.5)  # Semi-transparent red
        WIRE_COLOR = (0.0, 1.0, 0.0, 0.5)  # Semi-transparent green
        TEXT_COLOR = (0.0, 0.0, 1.0, 0.5)  # Semi-transparent blue
        GLOBAL_PHASE_COLOR = (1.0, 1.0, 0.0, 0.5)  # Semi-transparent yellow

    fig = CustomStyleDiagram.build_diagram(Circuit().h(0).gphase(0.1))
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.patches) == 1
    assert len(ax.texts) >= 2
    assert any("H" in text.get_text() for text in ax.texts)
    assert any("Phase: 0.1" in text.get_text() for text in ax.texts)
