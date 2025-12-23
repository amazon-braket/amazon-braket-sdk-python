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

from braket.ir.openqasm import Program as OpenQASMProgram
from braket.ir.openqasm import ProgramSet as OpenQASMProgramSet

from braket.ahs import AnalogHamiltonianSimulation
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.serialization import SerializableProgram
from braket.emulation.passes import ValidationPass
from braket.program_sets import ProgramSet
from braket.pulse import PulseSequence
from braket.tasks.quantum_task import TaskSpecification


class _NotImplementedValidator(ValidationPass):
    def __init__(self):
        self._supported_specifications = tuple(TaskSpecification.__args__)

    """
    A validator that checks for features that are not implemented in the emulator.
    Currently checks for:
    1. Verbatim boxes - raises an error if the circuit does not have a verbatim box
    2. Specifications besides Circuit and ProgramSet
    """

    def validate(self, program: TaskSpecification) -> None:
        """
        Validates that the program does not contain any unsupported features.

        Args:
            program (TaskSpecification): The program to validate.

        Raises:
            ValueError: If the program does not have a verbatim box when required.
            TypeError: If the program is a ProgramSet
        """

        unsupported_specifications = (
            OpenQASMProgram
            | SerializableProgram
            | AnalogHamiltonianSimulation
            | OpenQASMProgramSet
            | PulseSequence
        )

        # Validate out unsupported specifications
        if isinstance(program, unsupported_specifications):
            raise ValueError(f"Specification {type(program)} is not supported yet.")  # noqa: TRY004

        if isinstance(program, ProgramSet):
            for item in program:
                self.validate(item)
            return
        # Check if the program has a verbatim box when required
        has_verbatim_box = any(
            isinstance(instruction.operator, (StartVerbatimBox, EndVerbatimBox))
            for instruction in program.instructions
        )

        if not has_verbatim_box:
            raise ValueError(
                "The input circuit must have a verbatim box. "
                "Add a verbatim box to the circuit, and try again."
            )
