"""Configuration for circuit visualization."""

from dataclasses import dataclass


@dataclass
class VisualizationConfig:
    """Configuration for circuit visualization.

    Attributes:
        gate_width: Width of gate boxes in visualization units.
        gate_height: Height of gate boxes in visualization units.
        wire_spacing: Vertical spacing between qubit wires.
        time_spacing: Horizontal spacing between time steps.
        font_size: Font size for gate labels and text.
        font_family: Font family for text rendering.
        wire_color: Color for qubit wire lines.
        gate_fill_color: Fill color for gate boxes.
        gate_stroke_color: Stroke color for gate box borders.
        control_radius: Radius of control qubit indicators.
        heatmap_colormap: Colormap name for heatmap rendering.
    """

    gate_width: float = 0.8
    gate_height: float = 0.6
    wire_spacing: float = 1.0
    time_spacing: float = 1.0
    font_size: int = 10
    font_family: str = "monospace"
    wire_color: str = "#000000"
    gate_fill_color: str = "#FFFFFF"
    gate_stroke_color: str = "#000000"
    control_radius: float = 0.1
    heatmap_colormap: str = "viridis"


DEFAULT_CONFIG = VisualizationConfig()
