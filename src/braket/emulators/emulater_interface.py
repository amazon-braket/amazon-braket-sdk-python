from abc import ABC, abstractmethod
from braket.emulators.emulator_passes import EmulatorPass, ProgramType
from braket.emulators.emulator_passes.criteria import EmulatorCriterion
from collections.abc import Iterator
from typing import Iterable, Union


class EmulatorInterface(ABC):
    def __init__(self, emulator_passes: Iterable[EmulatorPass] = None):
        self._emulator_passes = emulator_passes if emulator_passes is not None else []

    def run_program_passes[ProgramType](self, task_specification: ProgramType) -> ProgramType:
        """
        This method passes the input program through the EmulatorPasses contained within this emulator. An emulator pass may simply validate a program
        or may modify or entirely transform the program (to an equivalent quantum program).  
        Args:
            task_specification (ProgramType): The program to run the emulator passes on. 

        Returns: 
            (ProgramType): A "compiled" program of the same type as the input. 

        """
        for emulator_pass in self._emulator_passes:
            task_specification = emulator_pass(task_specification)
        return task_specification
    
    
    def run_validation_passes[ProgramType](self, task_specification: ProgramType) -> None: 
        """
        This method passes the input program through EmulatorPasses that perform only validation, without modifying the input program. 
        """
        for emulator_pass in self._emulator_passes:
            if isinstance(emulator_pass, EmulatorCriterion):
                emulator_pass(task_specification)
                
                
    def add_pass(self, emulator_pass: Union[Iterable[EmulatorPass], EmulatorPass]) -> None:
        if isinstance(emulator_pass, Iterator):
            self._emulator_passes.extend(emulator_pass)
        elif isinstance(emulator_pass, EmulatorPass):
            self._emulator_passes.append(emulator_pass)
        else:
            print(isinstance(emulator_pass, EmulatorPass))
            print(type(emulator_pass))
            raise TypeError("emulator_pass must be an EmulatorPass or an iterable of EmulatorPass")