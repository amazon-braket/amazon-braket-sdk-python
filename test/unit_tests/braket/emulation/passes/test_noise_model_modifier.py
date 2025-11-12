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

from braket.circuits import Circuit, Gate
from braket.circuits.noise_model import GateCriteria, NoiseModel
from braket.circuits.noises import BitFlip, Depolarizing
from braket.emulation.passes.circuit_passes import NoiseModelModifier
from braket.program_sets import ProgramSet


@pytest.fixture
def noise_model():
    model = NoiseModel()
    model.add_noise(BitFlip(0.1), GateCriteria(Gate.H))
    model.add_noise(Depolarizing(0.05), GateCriteria(Gate.X))
    return model


@pytest.fixture
def noise_modifier(noise_model):
    return NoiseModelModifier(noise_model)


def test_noise_model_applied_to_circuit(noise_modifier):
    """Test that noise model is correctly applied to circuit."""
    circuit = Circuit().h(0).x(1)
    result = noise_modifier.modify(circuit)

    # Should have original gates plus noise
    assert len(result.instructions) > 2
    # Check that noise was added after H gate
    h_instruction_found = False
    noise_after_h_found = False
    for instruction in result.instructions:
        if instruction.operator == Gate.H():
            h_instruction_found = True
        elif h_instruction_found and hasattr(instruction.operator, "probability"):
            noise_after_h_found = True
            break
    assert h_instruction_found and noise_after_h_found


def test_none_noise_model_returns_unchanged():
    """Test that None noise model returns circuit unchanged."""
    modifier = NoiseModelModifier(None)
    circuit = Circuit().h(0).x(1)
    result = modifier.modify(circuit)

    assert result == circuit


def test_program_set_noise_application(noise_modifier):
    """Test that noise is applied to all circuits in ProgramSet."""
    circuit1 = Circuit().h(0)
    circuit2 = Circuit().x(1)
    program_set = ProgramSet([circuit1, circuit2], shots_per_executable=50)

    result = noise_modifier.run(program_set)

    # Both circuits should have noise applied
    assert len(result[0].instructions) > 1  # h + noise
    assert len(result[1].instructions) > 1  # x + noise
    assert result.shots_per_executable == 50


def test_empty_circuit_with_noise_model(noise_modifier):
    """Test that empty circuit remains empty even with noise model."""
    circuit = Circuit()
    result = noise_modifier.run(circuit)

    assert len(result.instructions) == 0
