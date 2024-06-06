from __future__ import annotations
from abc import ABC, abstractmethod
from braket.circuits import Circuit
from braket.ir.openqasm import Program as OpenQasmProgram
from typing import Union, TypeVar

ProgramType = TypeVar("ProgramType")

class EmulatorPass(ABC):
    """
        Base class for all emulator compiler passes.
    """
    @abstractmethod
    def run_pass[ProgramType](self, task_specification: ProgramType) -> ProgramType:
        """

        Args:
            task_specification ProgramType: The program to run the pass on.

        Returns:
            ProgramType: A partial compilation of the input program.
        """
        raise NotImplementedError 
    

    def __call__(self, task_specification: ProgramType) -> ProgramType:
        """Allow the pass to be called like a function."""
        return self.run_pass(task_specification)