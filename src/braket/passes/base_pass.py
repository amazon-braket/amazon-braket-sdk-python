from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ProgramType = TypeVar("ProgramType")


class BasePass(ABC, Generic[ProgramType]):
    @abstractmethod
    def run(self, program: ProgramType) -> ProgramType:
        """
        Runs the emulator pass on the provided program.

        Args:
            program (ProgramType): The program to run the emulator pass on.

        Returns:
            ProgramType: The program after the emulator pass has been applied.

        Raises:
            NotImplementedError: Method not implemented.
        """
        raise NotImplementedError

    def __call__(self, program: ProgramType) -> ProgramType:
        return self.run(program)
