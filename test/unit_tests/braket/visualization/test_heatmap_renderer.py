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

"""Tests for HeatmapRenderer class."""

import numpy as np

from braket.circuits import Circuit
from braket.visualization.renderers import HeatmapRenderer


def test_heatmap_renderer_basic_svg():
    """Test that HeatmapRenderer can generate basic SVG output."""
    circuit = Circuit()
    for i in range(50):
        for _ in range(10):
            circuit.h(i)

    renderer = HeatmapRenderer(circuit)
    svg = renderer.render_svg()

    assert isinstance(svg, str)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Circuit Density Heatmap" in svg


def test_heatmap_renderer_basic_figure():
    """Test that HeatmapRenderer can generate matplotlib figure."""
    circuit = Circuit()
    for i in range(50):
        for _ in range(10):
            circuit.h(i)

    renderer = HeatmapRenderer(circuit)
    fig = renderer.render_figure()

    assert fig is not None
    assert hasattr(fig, "axes")


def test_compute_density_matrix_basic():
    """Test density matrix computation."""
    circuit = Circuit()
    for i in range(30):
        circuit.h(i)

    renderer = HeatmapRenderer(circuit)
    density = renderer._compute_density_matrix(bin_size=10)

    assert density.shape[0] == 3
    assert density.shape[1] == 1
    assert density.sum() == 30


def test_compute_density_matrix_empty_circuit():
    """Test density matrix with empty circuit."""
    circuit = Circuit()

    renderer = HeatmapRenderer(circuit)
    density = renderer._compute_density_matrix(bin_size=10)

    assert density.size == 0


def test_render_statistics_panel():
    """Test statistics panel rendering."""
    circuit = Circuit()
    for i in range(100):
        for _ in range(50):
            circuit.h(i)

    renderer = HeatmapRenderer(circuit)
    stats_svg = renderer._render_statistics_panel()

    assert isinstance(stats_svg, str)
    assert "Statistics" in stats_svg
    assert "100" in stats_svg
    assert "50" in stats_svg
    assert "5000" in stats_svg


def test_density_to_color_viridis():
    """Test density to color conversion."""
    circuit = Circuit().h(0)
    renderer = HeatmapRenderer(circuit)

    color_min = renderer._density_to_color(0, 100, "viridis")
    assert color_min.startswith("#")
    assert len(color_min) == 7

    color_max = renderer._density_to_color(100, 100, "viridis")
    assert color_max.startswith("#")
    assert len(color_max) == 7

    color_mid = renderer._density_to_color(50, 100, "viridis")
    assert color_mid.startswith("#")
    assert len(color_mid) == 7


def test_density_matrix_dimensions_proportional():
    """Test that density matrix dimensions are proportional to circuit size."""
    circuit = Circuit()
    for i in range(100):
        for _ in range(200):
            circuit.h(i)

    renderer = HeatmapRenderer(circuit)
    density = renderer._compute_density_matrix(bin_size=10)

    assert density.shape[0] == 10
    assert density.shape[1] == 20


def test_density_matrix_sum_equals_gate_count():
    """Test that sum of density values equals total gate count."""
    circuit = Circuit()
    for i in range(50):
        for _ in range(30):
            circuit.h(i)

    total_gates = len(circuit.instructions)

    renderer = HeatmapRenderer(circuit)
    density = renderer._compute_density_matrix(bin_size=5)

    assert density.sum() == total_gates
