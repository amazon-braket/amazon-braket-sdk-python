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

from braket.circuits import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.emulation.passes import TransformationPass
from braket.program_sets import ProgramSet


class VerbatimTransformation(TransformationPass):
    """A transformation pass that removes verbatim boxes from circuits.

    Verbatim boxes are hardware-specific directives that indicate sections of a circuit
    should be executed exactly as specified without any compiler optimizations. This
    modifier removes these directives while preserving the quantum operations within,
    making circuits suitable for emulation on different backends.

    Supported specifications:
        - Circuit: Removes StartVerbatimBox and EndVerbatimBox instructions
        - ProgramSet: Recursively applies to all contained circuits

    Examples:
        >>> modifier = VerbatimModifier()
        >>> circuit = Circuit()
        >>> circuit.add_instruction(StartVerbatimBox())
        >>> circuit.h(0)
        >>> circuit.add_instruction(EndVerbatimBox())
        >>> clean_circuit = modifier.transform(circuit)
        >>> # Now only contains the H gate
    """

    def __init__(self):
        """Initialize the verbatim modifier."""
        self._supported_specifications = Circuit | ProgramSet

    def transform(self, circuits: Circuit | ProgramSet) -> Circuit | ProgramSet:
        """Remove verbatim boxes from circuits.

        Args:
            circuits: Circuit or ProgramSet to remove verbatim boxes from

        Returns:
            Circuit(s) with verbatim box directives removed, preserving all
            quantum operations and result types
        """
        if isinstance(circuits, ProgramSet):
            return ProgramSet(
                [self.transform(item) for item in circuits],
                shots_per_executable=circuits.shots_per_executable,
            )

        # Filter out verbatim box instructions
        filtered_instructions = [
            instruction
            for instruction in circuits.instructions
            if not isinstance(instruction.operator, (StartVerbatimBox, EndVerbatimBox))
        ]

        # Create new circuit with filtered instructions
        modified_circuit = Circuit(filtered_instructions)

        # Preserve all result types
        for result_type in circuits.result_types:
            modified_circuit.add(result_type)

        return modified_circuit
