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

"""Tests for CircuitDiagram output methods."""

import pytest

from braket.circuits import Circuit
from braket.visualization import CircuitDiagram


def test_to_svg_returns_valid_svg_string():
    """Test that to_svg() returns a valid SVG string."""
    circuit = Circuit().h(0).cnot(0, 1)
    diagram = CircuitDiagram(circuit, mode="detailed")
    
    svg = diagram.to_svg()
    
    assert isinstance(svg, str)
    assert len(svg) > 0
    assert "<svg" in svg
    assert "</svg>" in svg


def test_to_svg_works_for_all_modes():
    """Test that to_svg() works for all rendering modes."""
    circuit = Circuit().h(0).cnot(0, 1)
    
    for mode in ["detailed", "compressed", "heatmap"]:
        diagram = CircuitDiagram(circuit, mode=mode)
        svg = diagram.to_svg()
        
        assert isinstance(svg, str)
        assert "<svg" in svg
        assert "</svg>" in svg


def test_to_png_returns_valid_png_bytes():
    """Test that to_png() returns valid PNG bytes."""
    circuit = Circuit().h(0).cnot(0, 1)
    diagram = CircuitDiagram(circuit, mode="detailed")
    
    png_bytes = diagram.to_png()
    
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 0
    assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n'


def test_to_figure_returns_matplotlib_figure():
    """Test that to_figure() returns a matplotlib Figure object."""
    import matplotlib.figure
    
    circuit = Circuit().h(0).cnot(0, 1)
    diagram = CircuitDiagram(circuit, mode="detailed")
    
    fig = diagram.to_figure()
    
    assert isinstance(fig, matplotlib.figure.Figure)


def test_to_figure_works_for_all_modes():
    """Test that to_figure() works for all rendering modes."""
    import matplotlib.figure
    
    circuit = Circuit().h(0).cnot(0, 1)
    
    for mode in ["detailed", "compressed", "heatmap"]:
        diagram = CircuitDiagram(circuit, mode=mode)
        fig = diagram.to_figure()
        
        assert isinstance(fig, matplotlib.figure.Figure)


def test_empty_circuit_to_svg():
    """Test that to_svg() handles empty circuits gracefully."""
    circuit = Circuit()
    diagram = CircuitDiagram(circuit, mode="detailed")
    
    svg = diagram.to_svg()
    
    assert isinstance(svg, str)
    assert "<svg" in svg
    assert "</svg>" in svg


def test_empty_circuit_to_png():
    """Test that to_png() handles empty circuits gracefully."""
    circuit = Circuit()
    diagram = CircuitDiagram(circuit, mode="detailed")
    
    png_bytes = diagram.to_png()
    
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 0
    assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n'


def test_empty_circuit_to_figure():
    """Test that to_figure() handles empty circuits gracefully."""
    import matplotlib.figure
    
    circuit = Circuit()
    diagram = CircuitDiagram(circuit, mode="detailed")
    
    fig = diagram.to_figure()
    
    assert isinstance(fig, matplotlib.figure.Figure)
