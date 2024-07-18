from __future__ import annotations

from abc import abstractmethod

from braket.emulators.emulator_passes.emulator_pass import EmulatorPass, ProgramType


class EmulatorCriterion(EmulatorPass):
    @abstractmethod
    def validate(self, program: ProgramType) -> None:
        """
        An emulator criterion is used to perform some non-modifying validation
        pass on an input program. Implementations of validate should return
        nothing if the input program passes validation and raise an error otherwise.

        Args:
            program (ProgramType): The program to be evaluated against this criteria.
        """
        raise NotImplementedError

    def run(self, program: ProgramType) -> ProgramType:
        """
        Validate the input program and return the program, unmodified.

        Args:
            program (ProgramType): The program to validate.

        Returns:
            ProgramType: The unmodified progam passed in as input.
        """
        self.validate(program)
        return program

    @abstractmethod
    def __eq__(self, other: EmulatorCriterion) -> bool:
        raise NotImplementedError
