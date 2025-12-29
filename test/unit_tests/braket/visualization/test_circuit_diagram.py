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

"""Tests for CircuitDiagram class."""

import pytest
from hypothesis import given, settings, HealthCheck

from braket.circuits import Circuit
from braket.visualization import CircuitDiagram

from .conftest import (
    large_circuits,
    medium_circuits,
    small_circuits,
)


@pytest.fixture
def simple_circuit():
    """Create a simple test circuit."""
    return Circuit().h(0).cnot(0, 1).h(2)


@given(small_circuits())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_auto_mode_selects_detailed_for_small_circuits(circuit):
    """Feature: circuit-visualization, Property 2: Auto Mode Selection by Size.

    For any circuit with ≤20 qubits AND ≤50 depth, auto mode SHALL select 'detailed'.
    Validates: Requirements 3.1, 3.2, 3.3
    """
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "detailed"


@given(medium_circuits())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_auto_mode_selects_compressed_for_medium_circuits(circuit):
    """Feature: circuit-visualization, Property 2: Auto Mode Selection by Size.

    For any circuit with ≤200 qubits AND ≤500 depth but exceeding detailed thresholds,
    auto mode SHALL select 'compressed'.
    Validates: Requirements 3.1, 3.2, 3.3
    """
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "compressed"


@given(large_circuits())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_auto_mode_selects_heatmap_for_large_circuits(circuit):
    """Feature: circuit-visualization, Property 2: Auto Mode Selection by Size.

    For any circuit exceeding compressed thresholds, auto mode SHALL select 'heatmap'.
    Validates: Requirements 3.1, 3.2, 3.3
    """
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "heatmap"


@pytest.mark.parametrize("mode", ["detailed", "compressed", "heatmap"])
@given(small_circuits())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_explicit_mode_override_small_circuit(mode, circuit):
    """Feature: circuit-visualization, Property 1: Explicit Mode Override.

    For any circuit and any explicit mode, the mode property SHALL equal
    the specified mode regardless of circuit size.
    Validates: Requirements 1.2, 1.3, 1.4, 3.4
    """
    diagram = CircuitDiagram(circuit, mode=mode)
    assert diagram.mode == mode


@pytest.mark.parametrize("mode", ["detailed", "compressed", "heatmap"])
@given(medium_circuits())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_explicit_mode_override_medium_circuit(mode, circuit):
    """Feature: circuit-visualization, Property 1: Explicit Mode Override.

    For any circuit and any explicit mode, the mode property SHALL equal
    the specified mode regardless of circuit size.
    Validates: Requirements 1.2, 1.3, 1.4, 3.4
    """
    diagram = CircuitDiagram(circuit, mode=mode)
    assert diagram.mode == mode


@pytest.mark.parametrize("mode", ["detailed", "compressed", "heatmap"])
@given(large_circuits())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_explicit_mode_override_large_circuit(mode, circuit):
    """Feature: circuit-visualization, Property 1: Explicit Mode Override.

    For any circuit and any explicit mode, the mode property SHALL equal
    the specified mode regardless of circuit size.
    Validates: Requirements 1.2, 1.3, 1.4, 3.4
    """
    diagram = CircuitDiagram(circuit, mode=mode)
    assert diagram.mode == mode


def test_invalid_mode_raises_error():
    """Test that invalid mode raises ValueError."""
    circuit = Circuit().h(0)
    with pytest.raises(ValueError, match="Invalid mode"):
        CircuitDiagram(circuit, mode="invalid")


def test_mode_property_returns_selected_mode(simple_circuit):
    """Test that mode property returns the selected mode."""
    diagram = CircuitDiagram(simple_circuit, mode="detailed")
    assert diagram.mode == "detailed"


def test_boundary_detailed_to_compressed():
    """Test boundary condition at detailed/compressed threshold."""
    circuit = Circuit()
    for i in range(20):
        for _ in range(50):
            circuit.h(i)
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "detailed"

    circuit = Circuit()
    for i in range(21):
        circuit.h(i)
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "compressed"

    circuit = Circuit()
    for _ in range(51):
        circuit.h(0)
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "compressed"


def test_boundary_compressed_to_heatmap():
    """Test boundary condition at compressed/heatmap threshold."""
    circuit = Circuit()
    for i in range(200):
        for _ in range(2):
            circuit.h(i)
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "compressed"

    circuit = Circuit()
    for i in range(201):
        circuit.h(i)
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "heatmap"

    circuit = Circuit()
    for _ in range(501):
        circuit.h(0)
    diagram = CircuitDiagram(circuit, mode="auto")
    assert diagram.mode == "heatmap"
