from __future__ import annotations

from typing import Union

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.axes import Axes
from matplotlib.figure import Figure

import braket.circuits.circuit as cir
from braket.circuits.circuit_diagram import CircuitDiagram
from braket.circuits.instruction import Instruction
from braket.circuits.moments import MomentType
from braket.circuits.result_type import ResultType
from braket.circuits.result_types import ObservableResultType
from braket.circuits.text_diagram_builders.text_circuit_diagram_utils import _group_items
from braket.registers.qubit_set import QubitSet


class MatplotlibCircuitDiagram(CircuitDiagram):
    """A class that builds circuit diagrams using matplotlib."""

    # Default styling parameters
    GATE_BOX_HEIGHT = 0.6
    GATE_BOX_WIDTH = 1.0
    GATE_BOX_PADDING = 0.2
    WIRE_SPACING = 1.0
    COLUMN_SPACING = 1.5
    GATE_COLOR = "#E0E0E0"
    WIRE_COLOR = "#000000"
    TEXT_COLOR = "#000000"
    GLOBAL_PHASE_COLOR = "#666666"

    @classmethod
    def build_diagram(cls, circuit: cir.Circuit) -> Figure:
        """Build a matplotlib figure for the specified circuit.

        Args:
            circuit (cir.Circuit): The circuit to build a diagram for.

        Returns:
            Figure: Matplotlib figure containing the circuit diagram.
        """
        if not circuit.instructions:
            return plt.figure()

        if all(m.moment_type == MomentType.GLOBAL_PHASE for m in circuit._moments):
            fig, ax = plt.subplots(figsize=(4, 1))
            ax.text(0.5, 0.5, f"Global phase: {circuit.global_phase}", ha="center", va="center")
            ax.axis("off")
            return fig

        # Get circuit qubits and sort them
        circuit_qubits = circuit.qubits
        circuit_qubits.sort()

        # Create figure and axis
        num_qubits = len(circuit_qubits)
        fig_width = 10  # Will be adjusted based on circuit size
        fig_height = max(4, num_qubits * 1.5)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        # Draw the circuit
        cls._draw_circuit(ax, circuit, circuit_qubits)

        # Adjust layout and return
        plt.tight_layout()
        return fig

    @classmethod
    def _draw_circuit(cls, ax: Axes, circuit: cir.Circuit, circuit_qubits: QubitSet) -> None:
        """Draw the circuit on the given axis.

        Args:
            ax (Axes): Matplotlib axis to draw on
            circuit (Circuit): Circuit to draw
            circuit_qubits (QubitSet): Sorted set of qubits in the circuit
        """
        # Set up the axis
        ax.set_aspect("equal")
        ax.axis("off")

        time_slices = circuit.moments.time_slices()
        num_columns = len(time_slices) + (1 if circuit.result_types else 0)

        # Draw qubit lines
        wire_color = getattr(cls, "WIRE_COLOR", "#000000")
        text_color = getattr(cls, "TEXT_COLOR", "#000000")
        for i, qubit in enumerate(circuit_qubits):
            y = -i * cls.WIRE_SPACING
            ax.plot(
                [0, num_columns * cls.COLUMN_SPACING],
                [y, y],
                color=wire_color,
                linewidth=1,
                alpha=1.0,
            )
            ax.text(-0.5, y, f"q[{qubit}]", ha="right", va="center", color=text_color)

        # Draw gates and connections
        x_pos = 0

        for instructions in time_slices.values():
            # Group instructions to handle overlapping gates
            groupings = _group_items(circuit_qubits, instructions)
            for grouping in groupings:
                cls._draw_instruction_group(ax, grouping[1], circuit_qubits, x_pos)
                x_pos += cls.COLUMN_SPACING

        # Draw result types if any
        if circuit.result_types:
            cls._draw_result_types(ax, circuit.result_types, circuit_qubits, x_pos)

        # Draw global phase if present (after all instructions, so it's not overlapped)
        if circuit.global_phase != 0:
            y_center = (
                0 if len(circuit_qubits) == 1 else -len(circuit_qubits) * cls.WIRE_SPACING / 2
            )
            # If global phase is exactly 0.5, display as 0.50π, else as a number with two decimals
            if abs(circuit.global_phase - 0.5) < 1e-9:
                phase_str = "0.50π"
            else:
                phase_str = f"{circuit.global_phase:.2f}"
            # Add the global phase text to the axis
            ax.text(
                x_pos,
                y_center,
                f"Phase: {phase_str}",
                color=getattr(cls, "GLOBAL_PHASE_COLOR", "#666666"),
                ha="center",
                va="center",
                fontsize=10,
                bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none", "pad": 1},
            )

    @classmethod
    def _draw_instruction_group(
        cls,
        ax: Axes,
        instructions: list[Instruction | ResultType],
        circuit_qubits: QubitSet,
        x_pos: float,
    ) -> None:
        """Draw a group of instructions at the given x position.

        Args:
            ax (Axes): Matplotlib axis to draw on
            instructions (list[Instruction | ResultType]): Instructions to draw
            circuit_qubits (QubitSet): All qubits in the circuit
            x_pos (float): X position to draw at
        """
        gate_color = getattr(cls, "GATE_COLOR", "#E0E0E0")
        text_color = getattr(cls, "TEXT_COLOR", "#000000")
        wire_color = getattr(cls, "WIRE_COLOR", "#000000")
        # Draw each instruction
        for instruction in instructions:
            # Draw compiler directives as boxes with labels
            if (
                hasattr(instruction, "operator")
                and instruction.operator.__class__.__name__ == "CompilerDirective"
            ):
                qubits = instruction.target
                if not isinstance(qubits, QubitSet):
                    qubits = QubitSet(qubits)
                y_positions = (
                    [-circuit_qubits.index(q) * cls.WIRE_SPACING for q in qubits] if qubits else [0]
                )
                y_min = min(y_positions)
                y_max = max(y_positions)
                box = patches.Rectangle(
                    (x_pos - cls.GATE_BOX_WIDTH / 2, y_min - cls.GATE_BOX_HEIGHT / 2),
                    cls.GATE_BOX_WIDTH,
                    y_max - y_min + cls.GATE_BOX_HEIGHT,
                    facecolor=gate_color,
                    edgecolor="black",
                    alpha=0.7,
                )
                ax.add_patch(box)
                # Use the directive string exactly
                operator = instruction.operator
                text = str(operator.ascii_symbols[0]).strip()
                ax.text(
                    x_pos,
                    (y_min + y_max) / 2,
                    text,
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=10,
                    bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none", "pad": 1},
                )
                continue
            if hasattr(instruction, "target"):
                qubits = instruction.target
                if not isinstance(qubits, QubitSet):
                    qubits = QubitSet(qubits)
                if not qubits:
                    continue  # Skip drawing if no qubits
                # Calculate y positions for the gate
                y_positions = [-circuit_qubits.index(q) * cls.WIRE_SPACING for q in qubits]
                y_min = min(y_positions)
                y_max = max(y_positions)
                # Draw the gate box
                box = patches.Rectangle(
                    (x_pos - cls.GATE_BOX_WIDTH / 2, y_min - cls.GATE_BOX_HEIGHT / 2),
                    cls.GATE_BOX_WIDTH,
                    y_max - y_min + cls.GATE_BOX_HEIGHT,
                    facecolor=gate_color,
                    edgecolor="black",
                    alpha=0.7,
                )
                ax.add_patch(box)
                # Draw the gate name
                text = cls._get_instruction_text(instruction)
                ax.text(
                    x_pos,
                    (y_min + y_max) / 2,
                    text,
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=10,
                    bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none", "pad": 1},
                )
                # Draw connections between qubits
                if len(qubits) > 1:
                    for y in y_positions[1:]:
                        ax.plot([x_pos, x_pos], [y_positions[0], y], color=wire_color, linewidth=1)

    @classmethod
    def _draw_result_types(
        cls, ax: Axes, result_types: list[ResultType], circuit_qubits: QubitSet, x_pos: float
    ) -> None:
        """Draw result types at the given x position.

        Args:
            ax (Axes): Matplotlib axis to draw on
            result_types (list[ResultType]): Result types to draw
            circuit_qubits (QubitSet): All qubits in the circuit
            x_pos (float): X position to draw at
        """
        for result_type in result_types:
            if hasattr(result_type, "target") and result_type.target:
                qubits = result_type.target
                if not isinstance(qubits, QubitSet):
                    qubits = QubitSet(qubits)
                y_positions = [-circuit_qubits.index(q) * cls.WIRE_SPACING for q in qubits]
                y_min = min(y_positions)
                y_max = max(y_positions)
            else:
                # For result types without targets, draw at the top wire
                y_min = -0.5 * cls.WIRE_SPACING
                y_max = y_min + cls.GATE_BOX_HEIGHT
            # Draw the result type box
            box = patches.Rectangle(
                (x_pos - cls.GATE_BOX_WIDTH / 2, y_min - cls.GATE_BOX_HEIGHT / 2),
                cls.GATE_BOX_WIDTH,
                y_max - y_min + cls.GATE_BOX_HEIGHT,
                facecolor=cls.GATE_COLOR if isinstance(cls.GATE_COLOR, str) else "#E0E0E0",
                edgecolor="black",
                alpha=0.7,
            )
            ax.add_patch(box)
            # Draw the result type name
            text = cls._get_instruction_text(result_type)
            ax.text(
                x_pos,
                (y_min + y_max) / 2,
                text,
                ha="center",
                va="center",
                color=cls.TEXT_COLOR,
                fontsize=10,
                bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none", "pad": 1},
            )

    @classmethod
    def _get_instruction_text(cls, instruction: Union[Instruction, ResultType]) -> str:
        """Get the text representation of an instruction.

        Args:
            instruction (Union[Instruction, ResultType]): The instruction to get text for

        Returns:
            str: Text representation of the instruction
        """
        if hasattr(instruction, "operator"):
            operator = instruction.operator
            # Compiler directive
            if operator.__class__.__name__ == "CompilerDirective":
                return str(operator.ascii_symbols[0])
            # Measurement
            if operator.__class__.__name__ == "Measure":
                return "Measure"
            # Noise operations
            noise_names = [
                "Depolarizing",
                "BitFlip",
                "PhaseFlip",
                "AmplitudeDamping",
                "GeneralizedAmplitudeDamping",
                "PhaseDamping",
                "Kraus",
            ]
            if hasattr(operator, "name") and operator.name in noise_names:
                return operator.name.capitalize()
            # Parameterized gate
            if hasattr(operator, "angle") and hasattr(operator, "name") and operator.name:
                angle = getattr(operator, "angle", None)
                if angle is not None:
                    # Handle FreeParameter objects and expressions
                    if hasattr(angle, "name"):
                        angle_str = angle.name
                    elif hasattr(angle, "__str__"):
                        angle_str = str(angle)
                    else:
                        # Format numeric angles
                        angle_str = f"{angle:.2f}"
                        if abs(angle - 0.5) < 1e-9:
                            angle_str = "0.50π"
                    return f"{operator.name.capitalize()}({angle_str})"
            # Standard gate
            if hasattr(operator, "name") and operator.name:
                return operator.name.upper()
            # Fallback to ascii_symbols
            if hasattr(operator, "ascii_symbols"):
                return str(operator.ascii_symbols[0]).upper()
            return str(operator)
        # Handle ResultType and ObservableResultType
        if isinstance(instruction, ObservableResultType):
            # Use the ascii_symbols, which are like 'Expectation(X)', 'Sample(Y)', etc.
            return str(instruction.ascii_symbols[0])
        if isinstance(instruction, ResultType):
            # For other result types, use their ascii_symbols (e.g., 'Probability', 'StateVector', etc.)
            return str(instruction.ascii_symbols[0])
        if hasattr(instruction, "ascii_symbols"):
            return str(instruction.ascii_symbols[0])
        return str(instruction)
