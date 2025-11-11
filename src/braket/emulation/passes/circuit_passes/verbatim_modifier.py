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
