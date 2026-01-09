# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import pytest

from braket.circuits import Circuit
from braket.circuits.observables import X
from braket.emulation.passes.circuit_passes import MeasurementTransformation
from braket.program_sets import CircuitBinding, ProgramSet


@pytest.fixture
def measurement_transformation():
    return MeasurementTransformation()


def test_circuit_without_measurements_adds_measurements(measurement_transformation):
    """Test that circuits without measurements get measurements added."""
    circuit = Circuit().h(0).cnot(0, 1)
    assert len(circuit.instructions) == 2  # h, cnot, measure(0), measure(1)
    circuit = measurement_transformation.transform(circuit)
    assert len(circuit.instructions) == 4  # h, cnot, measure(0), measure(1)

    # Should add measurements for all qubits
    assert circuit.instructions[-2].operator.ascii_symbols == ("M",)
    assert circuit.instructions[-1].operator.ascii_symbols == ("M",)


def test_circuit_with_measurements_unchanged(measurement_transformation):
    """Test that circuits with measurements are not modified."""
    circuit = Circuit().h(0).measure(0)
    result = measurement_transformation.transform(circuit)
    # Should remain unchanged
    assert result == circuit


def test_circuit_with_result_types_unchanged(measurement_transformation):
    """Test that circuits with result types are not modified."""
    circuit = Circuit().h(0).probability()
    result = measurement_transformation.transform(circuit)
    # Should remain unchanged since it has result types
    assert result == circuit


def test_program_set_modification_circuits(measurement_transformation):
    """Test that ProgramSet circuits are individually modified."""
    circuit1 = Circuit().h(0)
    circuit2 = Circuit().x(1).measure(1)
    program_set = ProgramSet([circuit1, circuit2], shots_per_executable=100)

    result = measurement_transformation.transform(program_set)

    # First circuit should get measurement added, second unchanged
    assert len(result[0].instructions) == 2  # h + measure
    assert result[1] == circuit2
    assert result.shots_per_executable == 100


def test_program_set_modification_bindings(measurement_transformation):
    """Test that ProgramSet circuits are individually modified."""
    circuit1 = Circuit().h(0)
    circuit2 = Circuit().x(1)
    program_set = ProgramSet(
        [CircuitBinding(circuit1, observables=[X(0)]), circuit2], shots_per_executable=100
    )

    result = measurement_transformation.transform(program_set)

    # second circuit should get measurement added, first none
    assert result[0].circuit == circuit1
    assert len(result[1].instructions) == 2  # h + measure
    assert result.shots_per_executable == 100


def test_program_set_modification_binding_inputs_only(measurement_transformation):
    """Test that ProgramSet circuits are individually modified."""
    circuit1 = Circuit().h(0)
    circuit2 = Circuit().h(0).measure(0)
    program_set = ProgramSet(
        [
            CircuitBinding(circuit1, input_sets=[{"a": 0}]),
        ],
        shots_per_executable=100,
    )

    result = measurement_transformation.transform(program_set)
    assert result[0].circuit == circuit2
    assert result.shots_per_executable == 100


def test_incorrect_program_set(measurement_transformation):
    """ """
    program_set = ProgramSet([None, None])
    with pytest.raises(NotImplementedError):
        measurement_transformation.transform(program_set)


def test_empty_circuit(measurement_transformation):
    """Test that empty circuits get measurements for all qubits (none)."""
    circuit = Circuit()
    result = measurement_transformation.transform(circuit)

    # Empty circuit has no qubits, so no measurements added
    assert len(result.instructions) == 0
