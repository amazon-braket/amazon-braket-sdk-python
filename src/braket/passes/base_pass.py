from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ProgramType = TypeVar("ProgramType")


class BasePass(ABC, Generic[ProgramType]):
    @abstractmethod
    def run(self, program: ProgramType) -> ProgramType:
        """
        Runs a pass on the provided program.

        Args:
            program (ProgramType): The program to run the pass on.

        Returns:
            ProgramType: The program after the pass has been applied. Same type as the input 
            program.

        Raises:
            NotImplementedError: Method not implemented.
        """
        raise NotImplementedError

    def __call__(self, program: ProgramType) -> ProgramType:
        return self.run(program)
