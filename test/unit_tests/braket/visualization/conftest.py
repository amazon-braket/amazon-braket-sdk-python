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

"""Shared fixtures and generators for visualization tests."""

import pytest
from hypothesis import strategies as st

from braket.circuits import Circuit


@st.composite
def small_circuits(draw):
    """Generate circuits suitable for detailed mode (≤20 qubits, ≤50 depth)."""
    num_qubits = draw(st.integers(min_value=1, max_value=20))
    num_gates = draw(st.integers(min_value=1, max_value=min(50, num_qubits * 3)))
    circuit = Circuit()
    for _ in range(num_gates):
        qubit = draw(st.integers(min_value=0, max_value=num_qubits - 1))
        circuit.h(qubit)
    return circuit


@st.composite
def medium_circuits(draw):
    """Generate circuits suitable for compressed mode (21-200 qubits, 51-500 depth)."""
    num_qubits = draw(st.integers(min_value=21, max_value=100))
    num_gates = draw(st.integers(min_value=51, max_value=min(200, num_qubits * 3)))
    circuit = Circuit()
    for qubit in range(num_qubits):
        circuit.h(qubit)
    for _ in range(num_gates - num_qubits):
        qubit = draw(st.integers(min_value=0, max_value=num_qubits - 1))
        circuit.h(qubit)
    return circuit


@st.composite
def large_circuits(draw):
    """Generate circuits suitable for heatmap mode (>200 qubits or >500 depth)."""
    num_qubits = draw(st.integers(min_value=201, max_value=300))
    num_gates = draw(st.integers(min_value=201, max_value=min(400, num_qubits * 2)))
    circuit = Circuit()
    for qubit in range(num_qubits):
        circuit.h(qubit)
    for _ in range(num_gates - num_qubits):
        qubit = draw(st.integers(min_value=0, max_value=num_qubits - 1))
        circuit.h(qubit)
    return circuit


@st.composite
def circuits_with_controlled_gates(draw):
    """Generate circuits containing controlled gates."""
    num_qubits = draw(st.integers(min_value=2, max_value=10))
    circuit = Circuit()
    for _ in range(draw(st.integers(min_value=1, max_value=10))):
        control = draw(st.integers(min_value=0, max_value=num_qubits - 2))
        target = draw(st.integers(min_value=control + 1, max_value=num_qubits - 1))
        circuit.cnot(control, target)
    return circuit


@pytest.fixture
def simple_circuit():
    """Create a simple test circuit."""
    return Circuit().h(0).cnot(0, 1).h(2)
