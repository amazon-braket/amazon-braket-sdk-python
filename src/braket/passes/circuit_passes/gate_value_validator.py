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

from braket.circuits import Circuit
from braket.circuits.gates import MS, Rx
from braket.passes import ValidationPass


class GateValueValidator(ValidationPass[Circuit]):
    """Base class for validators that check gate parameter values."""

    def __init__(self):
        """Initialize a GateValueValidator."""

    def validate(self, program: Circuit) -> None:
        """Validates a circuit"""

    def __eq__(self, other: ValidationPass) -> bool:
        return isinstance(other, type(self))


class AnkaaRxValidator(GateValueValidator):
    """Validator for Rx gate values on Ankaa-3 device."""

    def validate(self, program: Circuit) -> None:
        """
        Validates that Rx gate values in the circuit comply with Ankaa-3 constraints.
        For Ankaa-3, Rx gate can only take (-π, -π/2, π/2, π).

        Args:
            program (Circuit): The Braket circuit to validate.

        Raises:
            ValueError: If an Rx gate has an invalid angle value.
        """
        for instruction in program.instructions:
            if isinstance(instruction.operator, Rx):
                angle = instruction.operator.angle
                valid_angles = {-math.pi, -math.pi / 2, math.pi / 2, math.pi}

                # Check if the angle is close to any of the valid angles
                if not any(math.isclose(angle, valid_angle) for valid_angle in valid_angles):
                    valid_angles_str = ", ".join([f"{angle}" for angle in valid_angles])
                    raise ValueError(
                        f"Invalid angle value {angle} for Rx gate on Ankaa-3 device. "
                        f"Valid values are: {valid_angles_str}"
                    )


class AriaMSValidator(GateValueValidator):
    """Validator for MS gate values on Aria-1 device."""

    def validate(self, program: Circuit) -> None:
        """
        Validates that MS gate values in the circuit comply with Aria-1 constraints.
        For Aria-1, the last argument of the MS gate can only be between [0.0, π/2].

        Args:
            program (Circuit): The Braket circuit to validate.

        Raises:
            ValueError: If an MS gate has an invalid angle_3 value.
        """
        for instruction in program.instructions:
            if isinstance(instruction.operator, MS):
                angle_3 = instruction.operator.angle_3

                if angle_3 < 0.0 or angle_3 > math.pi / 2:
                    raise ValueError(
                        f"Invalid angle_3 value {angle_3} for MS gate on Aria-1 device. "
                        f"Valid range is [0.0, π/2]"
                    )
