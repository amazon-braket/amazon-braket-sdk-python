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

from typing import Optional

from braket.circuits import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.gate import Gate
from braket.emulation.passes import ValidationPass

UNSUPPORTED_GATES = ["cc_prx", "measure_ff"]


class NotImplementedValidator(ValidationPass[Circuit]):
    """
    A validator that checks for features that are not implemented in the emulator.
    Currently checks for:
    1. Verbatim boxes - raises an error if the circuit does not have a verbatim box
    2. Unsupported gates - raises an error if the circuit contains any unsupported gates
    """

    def __init__(
        self,
        unsupported_gates: Optional[list[str]] = None,
        require_verbatim_box: bool = True,
    ):
        """
        Args:
            unsupported_gates (Optional[list[str]]): A list of gate names that are not supported.
                Default is UNSUPPORTED_GATES.
            require_verbatim_box (bool): Whether to require a verbatim box in the circuit.
                Default is True.
        """
        self._unsupported_gates = unsupported_gates or UNSUPPORTED_GATES
        self._require_verbatim_box = require_verbatim_box

    def validate(self, program: Circuit) -> None:
        """
        Validates that the circuit does not contain any unsupported features.

        Args:
            program (Circuit): The Braket circuit to validate.

        Raises:
            ValueError: If the circuit does not have a verbatim box when required.
            ValueError: If the circuit contains any unsupported gates.
        """
        # Check if the circuit has a verbatim box when required
        if self._require_verbatim_box:
            has_verbatim_box = any(
                isinstance(instruction.operator, (StartVerbatimBox, EndVerbatimBox))
                for instruction in program.instructions
            )

            if not has_verbatim_box:
                raise ValueError("Input circuit must have a verbatim box")

        # Check if the circuit has any unsupported gates
        for instruction in program.instructions:
            if isinstance(instruction.operator, Gate):
                gate = instruction.operator
                if gate.name.lower() in [g.lower() for g in self._unsupported_gates]:
                    raise ValueError(f"Gate {gate.name} is not supported by this emulator")

    def __eq__(self, other: ValidationPass) -> bool:
        return (
            isinstance(other, NotImplementedValidator)
            and self._unsupported_gates == other._unsupported_gates
            and self._require_verbatim_box == other._require_verbatim_box
        )
