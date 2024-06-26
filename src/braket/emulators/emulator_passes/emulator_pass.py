from abc import ABC, abstractmethod
from typing import Any, TypeVar

ProgramType = TypeVar("ProgramType")


class EmulatorPass(ABC):
    @abstractmethod
    def run[ProgramType](self, program: ProgramType) -> ProgramType:
        """Runs the emulator pass on the provided program.
        Args:
            program (ProgramType): The program to run the emulator pass on.
        Returns:
            ProgramType: The program after the emulator pass has been applied.
        """
        raise NotImplementedError

    def __call__[ProgramType](self, program: ProgramType) -> ProgramType:
        return self.run(program)
