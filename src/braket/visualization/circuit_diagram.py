"""CircuitDiagram class for circuit visualization."""

import io

import matplotlib.pyplot as plt
from IPython.display import display
from matplotlib.figure import Figure

from braket.circuits.text_diagram_builders.ascii_circuit_diagram import AsciiCircuitDiagram

from .renderers import CompressedRenderer, DetailedRenderer, HeatmapRenderer


class CircuitDiagram:
    """Visualization wrapper for quantum circuits with automatic mode selection.

    This class provides a unified interface for visualizing quantum circuits with
    three rendering modes: detailed (individual gates), compressed (grouped gates),
    and heatmap (density plot). The mode is automatically selected based on circuit
    size unless explicitly overridden.

    Attributes:
        DETAILED_QUBIT_THRESHOLD: Maximum qubits for detailed mode (20).
        DETAILED_DEPTH_THRESHOLD: Maximum depth for detailed mode (50).
        COMPRESSED_QUBIT_THRESHOLD: Maximum qubits for compressed mode (200).
        COMPRESSED_DEPTH_THRESHOLD: Maximum depth for compressed mode (500).
    """

    DETAILED_QUBIT_THRESHOLD: int = 20
    DETAILED_DEPTH_THRESHOLD: int = 50
    COMPRESSED_QUBIT_THRESHOLD: int = 200
    COMPRESSED_DEPTH_THRESHOLD: int = 500

    def __init__(self, circuit, mode: str = "auto", **options):
        """Initialize CircuitDiagram.

        Args:
            circuit: The Circuit to visualize.
            mode: Rendering mode - "auto", "detailed", "compressed", or "heatmap".
                  If "auto", the mode is selected based on circuit size.
            **options: Additional rendering options.
        """
        self.circuit = circuit
        self._selected_mode = self._select_mode(mode)
        self.options = options

    @property
    def mode(self) -> str:
        """Return the selected rendering mode.

        Returns:
            str: The rendering mode ("detailed", "compressed", or "heatmap").
        """
        return self._selected_mode

    def _select_mode(self, mode: str) -> str:
        """Select rendering mode based on circuit size or explicit override.

        Args:
            mode: The requested mode ("auto", "detailed", "compressed", or "heatmap").

        Returns:
            str: The selected mode ("detailed", "compressed", or "heatmap").

        Raises:
            ValueError: If mode is not a valid option.
        """
        valid_modes = {"auto", "detailed", "compressed", "heatmap"}
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of: {', '.join(sorted(valid_modes))}"
            )

        if mode != "auto":
            return mode

        qubit_count = self.circuit.qubit_count
        depth = self.circuit.depth

        if (
            qubit_count <= self.DETAILED_QUBIT_THRESHOLD
            and depth <= self.DETAILED_DEPTH_THRESHOLD
        ):
            return "detailed"

        if (
            qubit_count <= self.COMPRESSED_QUBIT_THRESHOLD
            and depth <= self.COMPRESSED_DEPTH_THRESHOLD
        ):
            return "compressed"

        return "heatmap"

    def _get_renderer(self):
        """Get the appropriate renderer based on selected mode.

        Returns:
            BaseRenderer: The renderer instance for the selected mode.

        Raises:
            ValueError: If the selected mode is unknown.
        """
        if self._selected_mode == "detailed":
            return DetailedRenderer(self.circuit, **self.options)
        elif self._selected_mode == "compressed":
            return CompressedRenderer(self.circuit, **self.options)
        elif self._selected_mode == "heatmap":
            return HeatmapRenderer(self.circuit, **self.options)
        else:
            raise ValueError(f"Unknown mode: {self._selected_mode}")

    def to_svg(self) -> str:
        """Generate SVG string representation of the circuit.

        Returns:
            str: SVG representation of the circuit.
        """
        renderer = self._get_renderer()
        return renderer.render_svg()

    def to_png(self) -> bytes:
        """Generate PNG bytes representation of the circuit.

        Returns:
            bytes: PNG representation of the circuit.
        """
        fig = self.to_figure()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def to_figure(self) -> Figure:
        """Generate matplotlib Figure object of the circuit.

        Returns:
            matplotlib.figure.Figure: Figure object containing the circuit visualization.
        """
        renderer = self._get_renderer()
        return renderer.render_figure()

    def show(self) -> None:
        """Display the circuit visualization using matplotlib."""
        fig = self.to_figure()
        plt.show()

    def _repr_html_(self) -> str:
        """Return HTML representation for Jupyter display.

        This method is automatically called by Jupyter when a CircuitDiagram
        is the last expression in a cell. It returns an SVG visualization
        wrapped in HTML, or falls back to ASCII diagram in a <pre> tag if
        matplotlib is unavailable.

        Returns:
            str: HTML representation of the circuit.
        """
        if self._selected_mode == "heatmap":
            from IPython.display import display
            
            renderer = self._get_renderer()
            widget = renderer.render_interactive()
            display(widget)
            return ""
        
        svg = self.to_svg()
        return svg

    def _repr_png_(self) -> bytes:
        """Return PNG representation for Jupyter display.

        This method is automatically called by Jupyter when PNG representation
        is requested. It returns PNG bytes of the circuit visualization.

        Returns:
            bytes: PNG representation of the circuit.
        """
        return self.to_png()
