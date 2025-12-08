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

import pytest

from braket.circuits import Circuit
from braket.emulation.passes.circuit_passes import _NotImplementedValidator
from braket.program_sets import ProgramSet


@pytest.fixture
def default_not_implemented_validator():
    return _NotImplementedValidator()


def test_validate_circuit_with_verbatim_box(default_not_implemented_validator):
    """Test that a circuit with a verbatim box passes validation."""
    circuit = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    # Should not raise an exception
    default_not_implemented_validator.validate(circuit)


def test_validate_circuit_without_verbatim_box(default_not_implemented_validator):
    """Test that a circuit without a verbatim box fails validation."""
    circuit = Circuit().h(0).cnot(0, 1)
    with pytest.raises(
        ValueError,
        match="The input circuit must have a verbatim box. Add a verbatim box to the circuit, and try again.",
    ):
        default_not_implemented_validator.validate(circuit)


def test_program_set(default_not_implemented_validator):
    program_set = ProgramSet([Circuit().h(0).cnot(0, 1), Circuit().rx(0, 0)])
    with pytest.raises(TypeError):
        default_not_implemented_validator.validate(program_set)
