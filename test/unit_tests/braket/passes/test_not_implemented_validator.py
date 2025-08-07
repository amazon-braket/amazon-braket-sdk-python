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
from braket.passes.circuit_passes import NotImplementedValidator
from braket.passes.circuit_passes.not_implemented_validator import UNSUPPORTED_GATES


def test_validate_circuit_with_verbatim_box():
    """Test that a circuit with a verbatim box passes validation."""
    circuit = Circuit().add_verbatim_box(Circuit().h(0).cnot(0, 1))
    validator = NotImplementedValidator()
    # Should not raise an exception
    validator.validate(circuit)


def test_validate_circuit_without_verbatim_box():
    """Test that a circuit without a verbatim box fails validation."""
    circuit = Circuit().h(0).cnot(0, 1)
    validator = NotImplementedValidator()
    with pytest.raises(ValueError, match="Input circuit must have a verbatim box"):
        validator.validate(circuit)


def test_validate_circuit_with_custom_unsupported_gates():
    """Test that a circuit with a custom unsupported gate fails validation."""
    # Create a circuit with a verbatim box that includes an H gate
    circuit = Circuit().add_verbatim_box(Circuit().h(0))

    # Create a validator with custom unsupported gates including "h"
    validator = NotImplementedValidator(unsupported_gates=["h"])

    # Create a mock instruction with an H gate
    class MockGate:
        @property
        def name(self):
            return "H"  # Note: uppercase H to match actual gate name

    class MockInstruction:
        def __init__(self, operator):
            self.operator = operator

    # Add our mock H gate to the instructions
    circuit.instructions.append(MockInstruction(MockGate()))

    with pytest.raises(ValueError, match="Gate H is not supported by this emulator"):
        validator.validate(circuit)


def test_validate_circuit_without_requiring_verbatim_box():
    """Test that a circuit without a verbatim box passes validation when not required."""
    circuit = Circuit().h(0).cnot(0, 1)
    validator = NotImplementedValidator(require_verbatim_box=False)
    # Should not raise an exception
    validator.validate(circuit)


def test_validator_equality():
    """Test that validators with the same parameters are equal."""
    validator1 = NotImplementedValidator(
        unsupported_gates=UNSUPPORTED_GATES, require_verbatim_box=True
    )
    validator2 = NotImplementedValidator(
        unsupported_gates=UNSUPPORTED_GATES, require_verbatim_box=True
    )
    validator3 = NotImplementedValidator(unsupported_gates=["xyz"], require_verbatim_box=True)
    validator4 = NotImplementedValidator(
        unsupported_gates=UNSUPPORTED_GATES, require_verbatim_box=False
    )

    assert validator1 == validator2
    assert validator1 != validator3
    assert validator1 != validator4


def test_default_unsupported_gates():
    """Test that the default unsupported gates are used when not specified."""
    validator = NotImplementedValidator()
    assert validator._unsupported_gates == UNSUPPORTED_GATES
