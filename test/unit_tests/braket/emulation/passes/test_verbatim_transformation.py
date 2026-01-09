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
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.emulation.passes.circuit_passes import VerbatimTransformation
from braket.program_sets import ProgramSet


@pytest.fixture
def verbatim_transformation():
    return VerbatimTransformation()


def test_removes_verbatim_boxes(verbatim_transformation):
    """Test that verbatim boxes are removed from circuit."""
    circuit = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1)).x(0)
    result = verbatim_transformation.transform(circuit)

    # Should have h, cnot, x but no verbatim boxes
    assert len(result.instructions) == 3
    for instruction in result.instructions:
        assert not isinstance(instruction.operator, (StartVerbatimBox, EndVerbatimBox))


def test_preserves_result_types(verbatim_transformation):
    """Test that result types are preserved when removing verbatim boxes."""
    circuit = Circuit().add_verbatim_box(Circuit().h(0))
    circuit.probability()

    result = verbatim_transformation.transform(circuit)

    # Should preserve result types
    assert len(result.result_types) == 1
    assert len(result.instructions) == 1  # only h gate


def test_circuit_without_verbatim_unchanged(verbatim_transformation):
    """Test that circuits without verbatim boxes are unchanged."""
    circuit = Circuit().h(0).cnot(0, 1).probability()
    result = verbatim_transformation.transform(circuit)

    assert result == circuit


def test_program_set_verbatim_removal(verbatim_transformation):
    """Test that verbatim boxes are removed from all circuits in ProgramSet."""
    circuit1 = Circuit().add_verbatim_box(Circuit().h(0))

    circuit2 = Circuit().x(1)  # no verbatim

    program_set = ProgramSet([circuit1, circuit2], shots_per_executable=75)
    result = verbatim_transformation.transform(program_set)

    # First circuit should have verbatim removed, second unchanged
    assert len(result[0].instructions) == 1  # only h
    assert result[1] == circuit2
    assert result.shots_per_executable == 75


def test_multiple_verbatim_boxes(verbatim_transformation):
    """Test handling of multiple verbatim box pairs."""
    circuit = Circuit().add_verbatim_box(Circuit().h(0)).x(0)
    circuit += Circuit().add_verbatim_box(Circuit().cnot(0, 1))

    result = verbatim_transformation.transform(circuit)

    # Should have h, x, cnot but no verbatim boxes
    assert len(result.instructions) == 3
    for instruction in result.instructions:
        assert not isinstance(instruction.operator, (StartVerbatimBox, EndVerbatimBox))
