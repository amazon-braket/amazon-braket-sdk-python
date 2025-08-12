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

import math
import pytest

from braket.circuits import Circuit
from braket.circuits.gates import Rx, MS
from braket.emulation.passes.circuit_passes import AnkaaRxValidator, AriaMSValidator, GateValueValidator


def test_ankaa_rx_validator_valid_angles():
    """Test that AnkaaRxValidator accepts valid angles for Rx gates."""
    valid_angles = [-math.pi, -math.pi / 2, math.pi / 2, math.pi]

    for angle in valid_angles:
        circuit = Circuit().rx(0, angle).h(0)
        validator = AnkaaRxValidator()
        # Should not raise an exception
        validator.validate(circuit)


def test_ankaa_rx_validator_invalid_angles():
    """Test that AnkaaRxValidator rejects invalid angles for Rx gates."""
    invalid_angles = [0, math.pi / 4, -math.pi / 4, 3 * math.pi / 4]

    for angle in invalid_angles:
        circuit = Circuit().rx(0, angle)
        validator = AnkaaRxValidator()
        with pytest.raises(ValueError):
            validator.validate(circuit)


def test_aria_ms_validator_valid_angles():
    """Test that AriaMSValidator accepts valid angle_3 values for MS gates."""
    valid_angles = [0.0, math.pi / 4, math.pi / 2]

    for angle in valid_angles:
        circuit = Circuit().ms(0, 1, 0.1, 0.2, angle).h(0)
        validator = AriaMSValidator()
        # Should not raise an exception
        validator.validate(circuit)


def test_aria_ms_validator_invalid_angles():
    """Test that AriaMSValidator rejects invalid angle_3 values for MS gates."""
    invalid_angles = [-0.1, math.pi, 2 * math.pi]

    for angle in invalid_angles:
        circuit = Circuit().ms(0, 1, 0.1, 0.2, angle)
        validator = AriaMSValidator()
        with pytest.raises(ValueError):
            validator.validate(circuit)


def test_validators_equality():
    """Test that validators of the same type are equal."""
    assert AnkaaRxValidator() == AnkaaRxValidator()
    assert AriaMSValidator() == AriaMSValidator()
    assert AnkaaRxValidator() != AriaMSValidator()
    assert GateValueValidator() == GateValueValidator()
    assert GateValueValidator() != AnkaaRxValidator()
    assert GateValueValidator() != AriaMSValidator()


def test_gate_value_validator_validate():
    """Test that the base GateValueValidator's validate method doesn't raise exceptions."""
    circuit = Circuit().h(0).cnot(0, 1)
    validator = GateValueValidator()
    # Should not raise an exception
    validator.validate(circuit)
