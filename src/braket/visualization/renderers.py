"""Renderer classes for circuit visualization."""

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

from .config import DEFAULT_CONFIG

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from braket.circuits import Circuit


@dataclass
class GatePosition:
    """Position information for a gate in the visualization.

    Attributes:
        qubit_indices: List of qubit indices this gate operates on.
        time_index: Time slice index for this gate.
        symbol: String representation of the gate (e.g., "H", "CNOT").
        is_controlled: Whether this gate has control qubits.
        control_qubits: List of control qubit indices.
        target_qubits: List of target qubit indices.
    """

    qubit_indices: list[int]
    time_index: int
    symbol: str
    is_controlled: bool
    control_qubits: list[int]
    target_qubits: list[int]


class BaseRenderer(ABC):
    """Abstract base class for circuit renderers.

    This class defines the interface that all renderers must implement and provides
    common utility methods for computing gate positions and qubit labels.
    """

    def __init__(self, circuit: "Circuit", **options):
        """Initialize renderer with circuit and options.

        Args:
            circuit: The Circuit object to render.
            **options: Additional rendering options (e.g., colors, sizes, fonts).
        """
        self.circuit = circuit
        self.options = options

    @abstractmethod
    def render_svg(self) -> str:
        """Render circuit as SVG string.

        Returns:
            str: SVG representation of the circuit.
        """
        ...

    @abstractmethod
    def render_figure(self) -> "Figure":
        """Render circuit as matplotlib Figure.

        Returns:
            matplotlib.figure.Figure: Figure object containing the circuit visualization.
        """
        ...

    def _compute_gate_positions(self) -> list[GatePosition]:
        """Compute gate positions from circuit moments.

        This method iterates through the circuit's moments and extracts position
        information for each gate, including control/target relationships.

        Returns:
            list[GatePosition]: List of gate positions for rendering.
        """
        positions = []

        for key, instruction in self.circuit.moments.items():
            if not hasattr(instruction.operator, "name"):
                continue

            symbol = instruction.operator.name
            all_qubits = [int(q) for q in instruction.target]
            control_qubits = []
            target_qubits = []

            if hasattr(instruction.operator, "ascii_symbols"):
                ascii_symbols = instruction.operator.ascii_symbols
                for i, (qubit, sym) in enumerate(zip(all_qubits, ascii_symbols)):
                    if sym == "C":
                        control_qubits.append(qubit)
                    else:
                        target_qubits.append(qubit)
            else:
                target_qubits = all_qubits

            if instruction.control:
                control_qubits.extend([int(q) for q in instruction.control])

            if not target_qubits:
                target_qubits = all_qubits

            position = GatePosition(
                qubit_indices=all_qubits,
                time_index=key.time,
                symbol=symbol,
                is_controlled=len(control_qubits) > 0,
                control_qubits=control_qubits,
                target_qubits=target_qubits,
            )
            positions.append(position)

        return positions

    def _get_qubit_labels(self) -> list[str]:
        """Get sorted qubit labels from circuit.

        Returns:
            list[str]: List of qubit labels in sorted order (e.g., ["q0", "q1", "q2"]).
        """
        qubits = sorted(self.circuit.qubits)
        return [f"q{int(q)}" for q in qubits]

    def _draw_gate_box(
        self,
        ax,
        x: float,
        y: float,
        symbol: str,
        width: float,
        height: float,
        font_size: int,
        fill: str,
        stroke: str,
    ) -> None:
        """Draw a gate box on matplotlib axes.

        Args:
            ax: Matplotlib axes object.
            x: X-coordinate of gate center.
            y: Y-coordinate of gate center.
            symbol: Gate symbol text.
            width: Box width in visualization units.
            height: Box height in visualization units.
            font_size: Font size for gate symbol.
            fill: Fill color for box.
            stroke: Stroke color for box border.
        """
        rect = patches.Rectangle(
            (x - width / 2, y - height / 2),
            width,
            height,
            linewidth=2,
            edgecolor=stroke,
            facecolor=fill,
            zorder=2,
        )
        ax.add_patch(rect)

        ax.text(x, y, symbol, ha="center", va="center", fontsize=font_size, family="monospace", zorder=3)

    def _draw_control_line(
        self,
        ax,
        x: float,
        control_qubits: list[int],
        target_qubits: list[int],
        num_qubits: int,
        control_radius: float,
        color: str,
    ) -> None:
        """Draw control lines and indicators on matplotlib axes.

        Args:
            ax: Matplotlib axes object.
            x: X-coordinate of the gate.
            control_qubits: List of control qubit indices.
            target_qubits: List of target qubit indices.
            num_qubits: Total number of qubits (for y-axis inversion).
            control_radius: Radius of control indicators.
            color: Line color.
        """
        all_qubits = control_qubits + target_qubits
        y_coords = [num_qubits - 1 - q for q in all_qubits]
        y_min = min(y_coords)
        y_max = max(y_coords)

        ax.plot([x, x], [y_min, y_max], color=color, linewidth=2, zorder=1)

        for ctrl_idx in control_qubits:
            y = num_qubits - 1 - ctrl_idx
            circle = patches.Circle((x, y), control_radius, color=color, zorder=2)
            ax.add_patch(circle)

    def _draw_wire(self, ax, y: float, x_start: float, x_end: float, color: str) -> None:
        """Draw horizontal qubit wire on matplotlib axes.

        Args:
            ax: Matplotlib axes object.
            y: Y-coordinate of the wire.
            x_start: Starting x-coordinate.
            x_end: Ending x-coordinate.
            color: Wire color.
        """
        ax.plot([x_start, x_end], [y, y], color=color, linewidth=1, zorder=0)

    def _draw_gate_box_svg(
        self,
        svg_parts: list[str],
        x: float,
        y: float,
        symbol: str,
        width: float,
        height: float,
        font_size: int,
        fill: str,
        stroke: str,
    ) -> None:
        """Draw a gate box in SVG.

        Args:
            svg_parts: List to append SVG elements to.
            x: X-coordinate of gate center.
            y: Y-coordinate of gate center.
            symbol: Gate symbol text.
            width: Box width in visualization units.
            height: Box height in visualization units.
            font_size: Font size for gate symbol.
            fill: Fill color for box.
            stroke: Stroke color for box border.
        """
        box_width = width * 40
        box_height = height * 40
        box_x = x - box_width / 2
        box_y = y - box_height / 2

        svg_parts.append(
            f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        )

        svg_parts.append(
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" '
            f'font-size="{font_size}" font-family="monospace" fill="{stroke}">'
            f"{symbol}</text>"
        )

    def _draw_control_line_svg(
        self,
        svg_parts: list[str],
        x: float,
        control_qubits: list[int],
        target_qubits: list[int],
        wire_spacing: float,
        margin: float,
        control_radius: float,
        color: str,
    ) -> None:
        """Draw control lines and indicators in SVG.

        Args:
            svg_parts: List to append SVG elements to.
            x: X-coordinate of the gate.
            control_qubits: List of control qubit indices.
            target_qubits: List of target qubit indices.
            wire_spacing: Spacing between wires.
            margin: Top margin.
            control_radius: Radius of control indicators.
            color: Line color.
        """
        all_qubits = control_qubits + target_qubits
        min_qubit = min(all_qubits)
        max_qubit = max(all_qubits)

        y_min = margin + min_qubit * wire_spacing * 50
        y_max = margin + max_qubit * wire_spacing * 50

        svg_parts.append(f'<line x1="{x}" y1="{y_min}" x2="{x}" y2="{y_max}" stroke="{color}" stroke-width="2"/>')

        for ctrl_idx in control_qubits:
            y = margin + ctrl_idx * wire_spacing * 50
            radius = control_radius * 40
            svg_parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')


class DetailedRenderer(BaseRenderer):
    """Renderer for small circuits showing every gate individually.

    This renderer draws each gate as a separate box with clear symbols,
    control lines for multi-qubit gates, and horizontal wires for each qubit.
    Suitable for circuits with ≤20 qubits and ≤50 depth.
    """

    def render_svg(self) -> str:
        """Render circuit as SVG with individual gate boxes.

        Returns:
            str: SVG representation showing all gates individually.
        """
        config = DEFAULT_CONFIG
        gate_width = self.options.get("gate_width", config.gate_width)
        gate_height = self.options.get("gate_height", config.gate_height)
        wire_spacing = self.options.get("wire_spacing", config.wire_spacing)
        time_spacing = self.options.get("time_spacing", config.time_spacing)
        font_size = self.options.get("font_size", config.font_size)
        wire_color = self.options.get("wire_color", config.wire_color)
        gate_fill = self.options.get("gate_fill_color", config.gate_fill_color)
        gate_stroke = self.options.get("gate_stroke_color", config.gate_stroke_color)
        control_radius = self.options.get("control_radius", config.control_radius)

        qubit_labels = self._get_qubit_labels()
        gate_positions = self._compute_gate_positions()

        num_qubits = len(qubit_labels)
        circuit_depth = self.circuit.depth if gate_positions else 0

        label_width = 40
        margin = 20
        svg_width = label_width + (circuit_depth + 1) * time_spacing * 50 + 2 * margin
        svg_height = num_qubits * wire_spacing * 50 + 2 * margin

        svg_parts = [
            f'<svg width="{svg_width}" height="{svg_height}" '
            f'xmlns="http://www.w3.org/2000/svg">'
        ]

        for i, label in enumerate(qubit_labels):
            y = margin + i * wire_spacing * 50
            x_start = label_width + margin
            x_end = svg_width - margin

            svg_parts.append(
                f'<line x1="{x_start}" y1="{y}" x2="{x_end}" y2="{y}" '
                f'stroke="{wire_color}" stroke-width="1"/>'
            )

            svg_parts.append(
                f'<text x="{margin}" y="{y + 5}" '
                f'font-size="{font_size}" font-family="monospace" fill="{wire_color}">'
                f"{label}</text>"
            )

        for gate_pos in gate_positions:
            x_center = label_width + margin + gate_pos.time_index * time_spacing * 50

            if gate_pos.is_controlled:
                self._draw_control_line_svg(
                    svg_parts,
                    x_center,
                    gate_pos.control_qubits,
                    gate_pos.target_qubits,
                    wire_spacing,
                    margin,
                    control_radius,
                    wire_color,
                )

            for qubit_idx in gate_pos.target_qubits:
                y_center = margin + qubit_idx * wire_spacing * 50
                self._draw_gate_box_svg(
                    svg_parts,
                    x_center,
                    y_center,
                    gate_pos.symbol,
                    gate_width,
                    gate_height,
                    font_size,
                    gate_fill,
                    gate_stroke,
                )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    def render_figure(self) -> "Figure":
        """Render circuit as matplotlib Figure.

        Returns:
            matplotlib.figure.Figure: Figure object with circuit visualization.
        """
        config = DEFAULT_CONFIG
        gate_width = self.options.get("gate_width", config.gate_width)
        gate_height = self.options.get("gate_height", config.gate_height)
        wire_spacing = self.options.get("wire_spacing", config.wire_spacing)
        time_spacing = self.options.get("time_spacing", config.time_spacing)
        font_size = self.options.get("font_size", config.font_size)
        wire_color = self.options.get("wire_color", config.wire_color)
        gate_fill = self.options.get("gate_fill_color", config.gate_fill_color)
        gate_stroke = self.options.get("gate_stroke_color", config.gate_stroke_color)
        control_radius = self.options.get("control_radius", config.control_radius)

        qubit_labels = self._get_qubit_labels()
        gate_positions = self._compute_gate_positions()

        num_qubits = len(qubit_labels)
        circuit_depth = self.circuit.depth if gate_positions else 0

        fig, ax = plt.subplots(figsize=(max(8, circuit_depth * 0.5), max(4, num_qubits * 0.5)))
        ax.set_xlim(-0.5, circuit_depth + 0.5)
        ax.set_ylim(-0.5, num_qubits - 0.5)
        ax.set_aspect("equal")
        ax.axis("off")

        for i, label in enumerate(qubit_labels):
            y = num_qubits - 1 - i  # Invert y-axis for top-to-bottom display
            self._draw_wire(ax, y, -0.5, circuit_depth + 0.5, wire_color)

            ax.text(-0.7, y, label, ha="right", va="center", fontsize=font_size, family="monospace")

        for gate_pos in gate_positions:
            x = gate_pos.time_index

            if gate_pos.is_controlled:
                self._draw_control_line(
                    ax,
                    x,
                    gate_pos.control_qubits,
                    gate_pos.target_qubits,
                    num_qubits,
                    control_radius,
                    wire_color,
                )

            for qubit_idx in gate_pos.target_qubits:
                y = num_qubits - 1 - qubit_idx  # Invert y-axis
                self._draw_gate_box(
                    ax, x, y, gate_pos.symbol, gate_width, gate_height, font_size, gate_fill, gate_stroke
                )

        return fig

    def _draw_gate_box_svg(
        self,
        svg_parts: list[str],
        x: float,
        y: float,
        symbol: str,
        width: float,
        height: float,
        font_size: int,
        fill: str,
        stroke: str,
    ) -> None:
        """Draw a gate box in SVG.

        Args:
            svg_parts: List to append SVG elements to.
            x: X-coordinate of gate center.
            y: Y-coordinate of gate center.
            symbol: Gate symbol text.
            width: Box width in visualization units.
            height: Box height in visualization units.
            font_size: Font size for gate symbol.
            fill: Fill color for box.
            stroke: Stroke color for box border.
        """
        box_width = width * 40
        box_height = height * 40
        box_x = x - box_width / 2
        box_y = y - box_height / 2

        svg_parts.append(
            f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        )

        svg_parts.append(
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" '
            f'font-size="{font_size}" font-family="monospace" fill="{stroke}">'
            f"{symbol}</text>"
        )

    def _draw_control_line_svg(
        self,
        svg_parts: list[str],
        x: float,
        control_qubits: list[int],
        target_qubits: list[int],
        wire_spacing: float,
        margin: float,
        control_radius: float,
        color: str,
    ) -> None:
        """Draw control lines and indicators in SVG.

        Args:
            svg_parts: List to append SVG elements to.
            x: X-coordinate of the gate.
            control_qubits: List of control qubit indices.
            target_qubits: List of target qubit indices.
            wire_spacing: Spacing between wires.
            margin: Top margin.
            control_radius: Radius of control indicators.
            color: Line color.
        """
        all_qubits = control_qubits + target_qubits
        min_qubit = min(all_qubits)
        max_qubit = max(all_qubits)

        y_min = margin + min_qubit * wire_spacing * 50
        y_max = margin + max_qubit * wire_spacing * 50

        svg_parts.append(f'<line x1="{x}" y1="{y_min}" x2="{x}" y2="{y_max}" stroke="{color}" stroke-width="2"/>')

        for ctrl_idx in control_qubits:
            y = margin + ctrl_idx * wire_spacing * 50
            radius = control_radius * 40
            svg_parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')


@dataclass
class GateGroup:
    """Group of adjacent gates for compressed rendering.

    Attributes:
        qubit_index: The qubit index this group operates on.
        start_time: Starting time index of the group.
        end_time: Ending time index of the group.
        gate_count: Number of gates in this group.
        gate_types: Counter of gate types in this group.
    """

    qubit_index: int
    start_time: int
    end_time: int
    gate_count: int
    gate_types: Counter


class CompressedRenderer(BaseRenderer):
    """Renderer for medium circuits with grouped gates.

    This renderer groups adjacent single-qubit gates on the same qubit and shows
    count badges for repeated patterns. It preserves overall circuit structure
    while reducing visual density. Suitable for circuits with ≤200 qubits and ≤500 depth.
    """

    def render_svg(self) -> str:
        """Render circuit as SVG with grouped gate representation.

        Returns:
            str: SVG representation with grouped gates and count badges.
        """
        config = DEFAULT_CONFIG
        gate_width = self.options.get("gate_width", config.gate_width)
        gate_height = self.options.get("gate_height", config.gate_height)
        wire_spacing = self.options.get("wire_spacing", config.wire_spacing)
        time_spacing = self.options.get("time_spacing", config.time_spacing)
        font_size = self.options.get("font_size", config.font_size)
        wire_color = self.options.get("wire_color", config.wire_color)
        gate_fill = self.options.get("gate_fill_color", config.gate_fill_color)
        gate_stroke = self.options.get("gate_stroke_color", config.gate_stroke_color)
        control_radius = self.options.get("control_radius", config.control_radius)

        qubit_labels = self._get_qubit_labels()
        gate_positions = self._compute_gate_positions()
        gate_groups = self._group_adjacent_gates()

        num_qubits = len(qubit_labels)
        circuit_depth = self.circuit.depth if gate_positions else 0

        label_width = 40
        margin = 20
        svg_width = label_width + (circuit_depth + 1) * time_spacing * 50 + 2 * margin
        svg_height = num_qubits * wire_spacing * 50 + 2 * margin

        max_display_width = 1200
        scale = min(1.0, max_display_width / svg_width) if svg_width > max_display_width else 1.0
        display_width = svg_width * scale
        display_height = svg_height * scale

        svg_parts = [
            f'<svg width="{display_width}" height="{display_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="max-width: 100%; height: auto;">'
        ]

        for i, label in enumerate(qubit_labels):
            y = margin + i * wire_spacing * 50
            x_start = label_width + margin
            x_end = svg_width - margin

            svg_parts.append(
                f'<line x1="{x_start}" y1="{y}" x2="{x_end}" y2="{y}" '
                f'stroke="{wire_color}" stroke-width="1"/>'
            )

            svg_parts.append(
                f'<text x="{margin}" y="{y + 5}" '
                f'font-size="{font_size}" font-family="monospace" fill="{wire_color}">'
                f"{label}</text>"
            )

        for group in gate_groups:
            x_center = label_width + margin + (group.start_time + group.end_time) / 2 * time_spacing * 50
            y_center = margin + group.qubit_index * wire_spacing * 50

            group_width = max(gate_width, (group.end_time - group.start_time + 1) * 0.3)
            box_width = group_width * 40
            box_height = gate_height * 40
            box_x = x_center - box_width / 2
            box_y = y_center - box_height / 2

            svg_parts.append(
                f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
                f'fill="{gate_fill}" stroke="{gate_stroke}" stroke-width="2"/>'
            )

            most_common_gate = group.gate_types.most_common(1)[0][0] if group.gate_types else "G"
            svg_parts.append(
                f'<text x="{x_center}" y="{y_center + 5}" text-anchor="middle" '
                f'font-size="{font_size}" font-family="monospace" fill="{gate_stroke}">'
                f"{most_common_gate}</text>"
            )

            if group.gate_count > 1:
                badge_x = box_x + box_width - 8
                badge_y = box_y + 8
                svg_parts.append(
                    f'<circle cx="{badge_x}" cy="{badge_y}" r="8" '
                    f'fill="#FF6B6B" stroke="white" stroke-width="1"/>'
                )
                svg_parts.append(
                    f'<text x="{badge_x}" y="{badge_y + 3}" text-anchor="middle" '
                    f'font-size="8" font-family="monospace" fill="white">'
                    f"{group.gate_count}</text>"
                )

        for gate_pos in gate_positions:
            if len(gate_pos.qubit_indices) > 1:
                x_center = label_width + margin + gate_pos.time_index * time_spacing * 50

                if gate_pos.is_controlled:
                    self._draw_control_line_svg(
                        svg_parts,
                        x_center,
                        gate_pos.control_qubits,
                        gate_pos.target_qubits,
                        wire_spacing,
                        margin,
                        control_radius,
                        wire_color,
                    )

                for qubit_idx in gate_pos.target_qubits:
                    y_center = margin + qubit_idx * wire_spacing * 50
                    self._draw_gate_box_svg(
                        svg_parts,
                        x_center,
                        y_center,
                        gate_pos.symbol,
                        gate_width,
                        gate_height,
                        font_size,
                        gate_fill,
                        gate_stroke,
                    )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    def render_figure(self) -> "Figure":
        """Render circuit as matplotlib Figure with grouped gates.

        Returns:
            matplotlib.figure.Figure: Figure object with compressed visualization.
        """
        config = DEFAULT_CONFIG
        gate_width = self.options.get("gate_width", config.gate_width)
        gate_height = self.options.get("gate_height", config.gate_height)
        wire_spacing = self.options.get("wire_spacing", config.wire_spacing)
        time_spacing = self.options.get("time_spacing", config.time_spacing)
        font_size = self.options.get("font_size", config.font_size)
        wire_color = self.options.get("wire_color", config.wire_color)
        gate_fill = self.options.get("gate_fill_color", config.gate_fill_color)
        gate_stroke = self.options.get("gate_stroke_color", config.gate_stroke_color)
        control_radius = self.options.get("control_radius", config.control_radius)

        qubit_labels = self._get_qubit_labels()
        gate_positions = self._compute_gate_positions()
        gate_groups = self._group_adjacent_gates()
        density_regions = self._compute_density_regions()

        num_qubits = len(qubit_labels)
        circuit_depth = self.circuit.depth if gate_positions else 0

        fig, ax = plt.subplots(figsize=(max(8, circuit_depth * 0.5), max(4, num_qubits * 0.5)))
        ax.set_xlim(-0.5, circuit_depth + 0.5)
        ax.set_ylim(-0.5, num_qubits - 0.5)
        ax.set_aspect("equal")
        ax.axis("off")

        if density_regions.size > 0:
            max_density = density_regions.max() if density_regions.max() > 0 else 1
            for i in range(density_regions.shape[0]):
                for j in range(density_regions.shape[1]):
                    density = density_regions[i, j]
                    if density > 0:
                        opacity = min(0.3 * (density / max_density), 0.3)
                        x = j
                        y = num_qubits - 1 - i  # Invert y-axis
                        rect = patches.Rectangle(
                            (x - 0.5, y - 0.5),
                            1.0,
                            1.0,
                            linewidth=0,
                            facecolor="#0000FF",
                            alpha=opacity,
                            zorder=0,
                        )
                        ax.add_patch(rect)

        for i, label in enumerate(qubit_labels):
            y = num_qubits - 1 - i  # Invert y-axis
            self._draw_wire(ax, y, -0.5, circuit_depth + 0.5, wire_color)

            ax.text(-0.7, y, label, ha="right", va="center", fontsize=font_size, family="monospace")

        for group in gate_groups:
            x = (group.start_time + group.end_time) / 2
            y = num_qubits - 1 - group.qubit_index  # Invert y-axis

            group_width = max(gate_width, (group.end_time - group.start_time + 1) * 0.3)

            rect = patches.Rectangle(
                (x - group_width / 2, y - gate_height / 2),
                group_width,
                gate_height,
                linewidth=2,
                edgecolor=gate_stroke,
                facecolor=gate_fill,
                zorder=2,
            )
            ax.add_patch(rect)

            most_common_gate = group.gate_types.most_common(1)[0][0] if group.gate_types else "G"
            ax.text(x, y, most_common_gate, ha="center", va="center", fontsize=font_size, family="monospace", zorder=3)

            if group.gate_count > 1:
                badge_x = x + group_width / 2 - 0.15
                badge_y = y + gate_height / 2 - 0.15
                badge = patches.Circle((badge_x, badge_y), 0.15, color="#FF6B6B", ec="white", linewidth=1, zorder=4)
                ax.add_patch(badge)
                ax.text(
                    badge_x,
                    badge_y,
                    str(group.gate_count),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white",
                    weight="bold",
                    zorder=5,
                )

        for gate_pos in gate_positions:
            if len(gate_pos.qubit_indices) > 1:
                x = gate_pos.time_index

                if gate_pos.is_controlled:
                    self._draw_control_line(
                        ax,
                        x,
                        gate_pos.control_qubits,
                        gate_pos.target_qubits,
                        num_qubits,
                        control_radius,
                        wire_color,
                    )

                for qubit_idx in gate_pos.target_qubits:
                    y = num_qubits - 1 - qubit_idx  # Invert y-axis
                    self._draw_gate_box(
                        ax, x, y, gate_pos.symbol, gate_width, gate_height, font_size, gate_fill, gate_stroke
                    )

        return fig

    def _group_adjacent_gates(self) -> list[GateGroup]:
        """Group adjacent single-qubit gates on the same qubit.

        This method identifies sequences of single-qubit gates on the same qubit
        and groups them together for compressed visualization.

        Returns:
            list[GateGroup]: List of gate groups for rendering.
        """
        gate_positions = self._compute_gate_positions()

        single_qubit_gates = [gp for gp in gate_positions if len(gp.qubit_indices) == 1 and not gp.is_controlled]

        gates_by_qubit = {}
        for gate_pos in single_qubit_gates:
            qubit_idx = gate_pos.qubit_indices[0]
            if qubit_idx not in gates_by_qubit:
                gates_by_qubit[qubit_idx] = []
            gates_by_qubit[qubit_idx].append(gate_pos)

        for qubit_idx in gates_by_qubit:
            gates_by_qubit[qubit_idx].sort(key=lambda g: g.time_index)

        groups = []
        for qubit_idx, gates in gates_by_qubit.items():
            if not gates:
                continue

            current_group_start = gates[0].time_index
            current_group_gates = [gates[0]]

            for i in range(1, len(gates)):
                if gates[i].time_index == gates[i - 1].time_index + 1:
                    current_group_gates.append(gates[i])
                else:
                    gate_types = Counter(g.symbol for g in current_group_gates)
                    groups.append(
                        GateGroup(
                            qubit_index=qubit_idx,
                            start_time=current_group_start,
                            end_time=current_group_gates[-1].time_index,
                            gate_count=len(current_group_gates),
                            gate_types=gate_types,
                        )
                    )

                    current_group_start = gates[i].time_index
                    current_group_gates = [gates[i]]

            gate_types = Counter(g.symbol for g in current_group_gates)
            groups.append(
                GateGroup(
                    qubit_index=qubit_idx,
                    start_time=current_group_start,
                    end_time=current_group_gates[-1].time_index,
                    gate_count=len(current_group_gates),
                    gate_types=gate_types,
                )
            )

        return groups

    def _compute_density_regions(self, bin_size: int = 1) -> np.ndarray:
        """Compute gate density for regions of the circuit.

        This method creates a 2D grid representing gate density across the circuit,
        which is used for background shading in the compressed view.

        Args:
            bin_size: Size of each bin in time steps (default: 1 for per-step density).

        Returns:
            np.ndarray: 2D array of shape (num_qubits, num_time_bins) with gate counts.
        """
        gate_positions = self._compute_gate_positions()

        if not gate_positions:
            return np.array([])

        qubit_labels = self._get_qubit_labels()
        num_qubits = len(qubit_labels)
        circuit_depth = self.circuit.depth

        num_time_bins = circuit_depth
        density = np.zeros((num_qubits, num_time_bins), dtype=int)

        for gate_pos in gate_positions:
            time_bin = gate_pos.time_index
            if time_bin < num_time_bins:
                for qubit_idx in gate_pos.qubit_indices:
                    if qubit_idx < num_qubits:
                        density[qubit_idx, time_bin] += 1

        return density


class HeatmapRenderer(BaseRenderer):
    """Renderer for large circuits showing density heatmap.

    This renderer displays a 2D grid with qubits on the y-axis and time/depth on the x-axis,
    using color intensity to represent gate density in each region. It includes a statistics
    panel showing circuit metrics. Suitable for circuits with >200 qubits or >500 depth.
    """

    def render_svg(self) -> str:
        """Render circuit as SVG with 2D density heatmap.

        Returns:
            str: SVG representation showing gate density heatmap with statistics panel.
        """
        config = DEFAULT_CONFIG
        font_size = self.options.get("font_size", config.font_size)
        colormap = self.options.get("heatmap_colormap", config.heatmap_colormap)

        bin_size = self.options.get("bin_size", max(1, min(self.circuit.qubit_count // 50, 20)))
        density_matrix = self._compute_density_matrix(bin_size=bin_size)

        num_qubits = self.circuit.qubit_count
        circuit_depth = self.circuit.depth

        cell_size = 8
        margin = 60
        stats_panel_width = 250
        legend_width = 80

        heatmap_width = density_matrix.shape[1] * cell_size if density_matrix.size > 0 else 100
        heatmap_height = density_matrix.shape[0] * cell_size if density_matrix.size > 0 else 100

        max_heatmap_width = 800
        max_heatmap_height = 600
        
        if heatmap_width > max_heatmap_width:
            scale = max_heatmap_width / heatmap_width
            heatmap_width = max_heatmap_width
            heatmap_height = int(heatmap_height * scale)
            cell_size = heatmap_width / density_matrix.shape[1] if density_matrix.size > 0 else cell_size
        
        if heatmap_height > max_heatmap_height:
            scale = max_heatmap_height / heatmap_height
            heatmap_height = max_heatmap_height
            heatmap_width = int(heatmap_width * scale)
            cell_size = heatmap_width / density_matrix.shape[1] if density_matrix.size > 0 else cell_size

        svg_width = margin + heatmap_width + legend_width + stats_panel_width + margin
        svg_height = margin + heatmap_height + margin + 40

        svg_parts = [
            f'<svg width="100%" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="max-width: 100%; height: auto;">'
        ]

        svg_parts.append(
            f'<text x="{svg_width / 2}" y="{margin - 20}" '
            f'font-size="{font_size + 4}" font-family="monospace" font-weight="bold" '
            f'text-anchor="middle">'
            f"Circuit Density Heatmap</text>"
        )

        if density_matrix.size > 0:
            max_density = density_matrix.max() if density_matrix.max() > 0 else 1

            for i in range(density_matrix.shape[0]):
                for j in range(density_matrix.shape[1]):
                    density = density_matrix[i, j]
                    color = self._density_to_color(density, max_density, colormap)

                    x = margin + j * cell_size
                    y = margin + i * cell_size

                    svg_parts.append(
                        f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                        f'fill="{color}" stroke="none"/>'
                    )

        svg_parts.append(
            f'<text x="{margin - 15}" y="{margin + heatmap_height / 2}" '
            f'font-size="{font_size}" font-family="monospace" '
            f'text-anchor="middle" transform="rotate(-90 {margin - 15} {margin + heatmap_height / 2})">'
            f"Qubits (binned)</text>"
        )

        svg_parts.append(
            f'<text x="{margin + heatmap_width / 2}" y="{margin + heatmap_height + 35}" '
            f'font-size="{font_size}" font-family="monospace" text-anchor="middle">'
            f"Circuit Depth (binned)</text>"
        )

        legend_x = margin + heatmap_width + 30
        legend_height = min(heatmap_height, 200)
        legend_steps = 10

        svg_parts.append(
            f'<text x="{legend_x}" y="{margin - 10}" '
            f'font-size="{font_size}" font-family="monospace" font-weight="bold">'
            f"Density</text>"
        )

        for i in range(legend_steps):
            y = margin + (i * legend_height / legend_steps)
            density_value = max_density * (1 - i / legend_steps) if density_matrix.size > 0 else 0
            color = self._density_to_color(density_value, max_density, colormap)

            svg_parts.append(
                f'<rect x="{legend_x}" y="{y}" width="30" height="{legend_height / legend_steps + 1}" '
                f'fill="{color}" stroke="none"/>'
            )

        if density_matrix.size > 0:
            svg_parts.append(
                f'<text x="{legend_x + 35}" y="{margin + 5}" '
                f'font-size="{font_size - 1}" font-family="monospace">'
                f"{int(max_density)}</text>"
            )
            svg_parts.append(
                f'<text x="{legend_x + 35}" y="{margin + legend_height + 5}" '
                f'font-size="{font_size - 1}" font-family="monospace">'
                f"0</text>"
            )

        stats_svg = self._render_statistics_panel()
        stats_x = legend_x + legend_width + 20
        svg_parts.append(f'<g transform="translate({stats_x}, {margin})">{stats_svg}</g>')

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    def render_figure(self) -> "Figure":
        """Render circuit as matplotlib Figure with density heatmap.

        Returns:
            matplotlib.figure.Figure: Figure object with heatmap visualization.
        """
        config = DEFAULT_CONFIG
        font_size = self.options.get("font_size", config.font_size)
        colormap = self.options.get("heatmap_colormap", config.heatmap_colormap)

        bin_size = self.options.get("bin_size", 10)
        density_matrix = self._compute_density_matrix(bin_size=bin_size)

        num_qubits = self.circuit.qubit_count
        circuit_depth = self.circuit.depth
        total_gates = len(self.circuit.instructions)

        fig = plt.figure(figsize=(12, max(6, num_qubits * 0.01)))
        gs = fig.add_gridspec(1, 2, width_ratios=[4, 1], wspace=0.3)

        ax_heatmap = fig.add_subplot(gs[0])

        if density_matrix.size > 0:
            im = ax_heatmap.imshow(
                density_matrix, aspect="auto", cmap=colormap, interpolation="nearest", origin="upper"
            )

            cbar = plt.colorbar(im, ax=ax_heatmap, label="Gate Density")
            cbar.ax.tick_params(labelsize=font_size - 2)

        ax_heatmap.set_xlabel("Circuit Depth (binned)", fontsize=font_size)
        ax_heatmap.set_ylabel("Qubits (binned)", fontsize=font_size)
        ax_heatmap.set_title("Circuit Density Heatmap", fontsize=font_size + 2, weight="bold")
        ax_heatmap.tick_params(labelsize=font_size - 2)

        ax_stats = fig.add_subplot(gs[1])
        ax_stats.axis("off")

        stats_text = (
            f"Circuit Statistics\n"
            f"{'=' * 20}\n\n"
            f"Total Qubits: {num_qubits}\n"
            f"Circuit Depth: {circuit_depth}\n"
            f"Total Gates: {total_gates}\n\n"
            f"Bin Size: {bin_size}\n"
            f"Bins (Qubits): {density_matrix.shape[0] if density_matrix.size > 0 else 0}\n"
            f"Bins (Depth): {density_matrix.shape[1] if density_matrix.size > 0 else 0}"
        )

        ax_stats.text(
            0.1,
            0.9,
            stats_text,
            transform=ax_stats.transAxes,
            fontsize=font_size,
            verticalalignment="top",
            family="monospace",
        )

        return fig

    def _compute_density_matrix(self, bin_size: int = 10) -> np.ndarray:
        """Compute 2D gate density matrix using numpy.

        This method creates a 2D grid where each cell represents the number of gates
        in a specific region of the circuit (qubit range × time range).

        Args:
            bin_size: Number of qubits/time steps per bin (default: 10).

        Returns:
            np.ndarray: 2D array of shape (num_qubit_bins, num_time_bins) with gate counts.
        """
        gate_positions = self._compute_gate_positions()

        if not gate_positions:
            return np.array([])

        num_qubits = self.circuit.qubit_count
        circuit_depth = self.circuit.depth

        num_qubit_bins = max(1, (num_qubits + bin_size - 1) // bin_size)
        num_time_bins = max(1, (circuit_depth + bin_size - 1) // bin_size)

        density = np.zeros((num_qubit_bins, num_time_bins), dtype=int)

        for gate_pos in gate_positions:
            time_bin = gate_pos.time_index // bin_size
            if time_bin < num_time_bins:
                for qubit_idx in gate_pos.qubit_indices:
                    qubit_bin = qubit_idx // bin_size
                    if qubit_bin < num_qubit_bins:
                        density[qubit_bin, time_bin] += 1

        return density

    def _render_statistics_panel(self) -> str:
        """Render circuit statistics panel as SVG.

        Returns:
            str: SVG elements for the statistics panel.
        """
        config = DEFAULT_CONFIG
        font_size = self.options.get("font_size", config.font_size)
        bin_size = self.options.get("bin_size", max(1, min(self.circuit.qubit_count // 50, 20)))

        num_qubits = self.circuit.qubit_count
        circuit_depth = self.circuit.depth
        total_gates = len(self.circuit.instructions)
        density_matrix = self._compute_density_matrix(bin_size=bin_size)

        stats_parts = []
        y_offset = 0

        stats_parts.append(
            f'<text x="0" y="{y_offset}" '
            f'font-size="{font_size + 2}" font-family="monospace" font-weight="bold">'
            f"Statistics</text>"
        )
        y_offset += 25

        stats_parts.append(
            f'<line x1="0" y1="{y_offset}" x2="200" y2="{y_offset}" '
            f'stroke="#000000" stroke-width="1"/>'
        )
        y_offset += 20

        stats = [
            ("Qubits:", num_qubits),
            ("Depth:", circuit_depth),
            ("Gates:", total_gates),
            ("", ""),
            ("Bin Size:", bin_size),
            ("Qubit Bins:", density_matrix.shape[0] if density_matrix.size > 0 else 0),
            ("Depth Bins:", density_matrix.shape[1] if density_matrix.size > 0 else 0),
        ]

        for label, value in stats:
            if label == "":
                y_offset += 10
                continue
                
            stats_parts.append(
                f'<text x="0" y="{y_offset}" '
                f'font-size="{font_size}" font-family="monospace">'
                f"{label}</text>"
            )
            stats_parts.append(
                f'<text x="200" y="{y_offset}" text-anchor="end" '
                f'font-size="{font_size + 1}" font-family="monospace" font-weight="bold">'
                f"{value}</text>"
            )
            y_offset += 22

        return "".join(stats_parts)

    def _density_to_color(self, density: float, max_density: float, colormap: str) -> str:
        """Convert density value to hex color using colormap.

        Args:
            density: Gate density value.
            max_density: Maximum density value for normalization.
            colormap: Colormap name (currently only 'viridis' supported).

        Returns:
            str: Hex color string (e.g., "#440154").
        """
        if max_density == 0:
            return "#440154"  # Viridis minimum

        normalized = density / max_density

        if colormap == "viridis":
            if normalized < 0.25:
                t = normalized / 0.25
                r = int(68 + (31 - 68) * t)
                g = int(1 + (120 - 1) * t)
                b = int(84 + (180 - 84) * t)
            elif normalized < 0.5:
                t = (normalized - 0.25) / 0.25
                r = int(31 + (33 - 31) * t)
                g = int(120 + (145 - 120) * t)
                b = int(180 + (140 - 180) * t)
            elif normalized < 0.75:
                t = (normalized - 0.5) / 0.25
                r = int(33 + (94 - 33) * t)
                g = int(145 + (201 - 145) * t)
                b = int(140 + (98 - 140) * t)
            else:
                t = (normalized - 0.75) / 0.25
                r = int(94 + (253 - 94) * t)
                g = int(201 + (231 - 201) * t)
                b = int(98 + (37 - 98) * t)

            return f"#{r:02x}{g:02x}{b:02x}"
        else:
            gray = int(255 * (1 - normalized))
            return f"#{gray:02x}{gray:02x}{gray:02x}"
