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
from braket.emulation.passes import ModifierPass
from braket.program_sets import ProgramSet


class VerbatimModifier(ModifierPass):
    def __init__(self):
        """ Modifer that removes VerbatimBox from Circuits """
        self._supported_specifications = Circuit | ProgramSet

    def modify(self, circuits: Circuit | ProgramSet) -> Circuit | ProgramSet:
        """ remove VerbatimBox from the system

        Args:
            circuits (Circuit | ProgramSet): specification to remove verbatim from

        Returns:
            (Circuit | ProgramSet): output circuits or ProgramSets
            """
        if isinstance(circuits, ProgramSet):
            return ProgramSet(
                [self.modify(item) for item in circuits],
                shots_per_executable= circuits.shots_per_executable)

        noisy_verbatim_circ = [
            instruction
            for instruction in circuits.instructions
            if not isinstance(instruction.operator, StartVerbatimBox)
            and not isinstance(instruction.operator, EndVerbatimBox)
        ]
        noisy_verbatim_circ_2 = Circuit(noisy_verbatim_circ)
        for result_type in circuits.result_types:
            noisy_verbatim_circ_2.add(result_type)

        return noisy_verbatim_circ_2
