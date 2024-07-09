from __future__ import annotations

from abc import ABC
from typing import Iterable, Union

from braket.emulators.emulator_passes import EmulatorPass
from braket.emulators.emulator_passes.criteria import EmulatorCriterion


class EmulatorInterface(ABC):
    def __init__(self, emulator_passes: Iterable[EmulatorPass] = None):
        self._emulator_passes = emulator_passes if emulator_passes is not None else []

    def run_program_passes[ProgramType](self, task_specification: ProgramType) -> ProgramType:
        """
        This method passes the input program through the EmulatorPasses contained
        within this emulator. An emulator pass may simply validate a program or may
        modify or entirely transform the program (to an equivalent quantum program).
        Args:
            task_specification (ProgramType): The program to run the emulator passes on.

        Returns:
            ProgramType: A "compiled" program of the same type as the input.

        """
        for emulator_pass in self._emulator_passes:
            task_specification = emulator_pass(task_specification)
        return task_specification

    def run_validation_passes[ProgramType](self, task_specification: ProgramType) -> None:
        """
        This method passes the input program through EmulatorPasses that perform
        only validation, without modifying the input program.

        Args:
            task_specification (ProgramType): The program to validate with this
                emulator's validation passes.
        """
        for emulator_pass in self._emulator_passes:
            if isinstance(emulator_pass, EmulatorCriterion):
                emulator_pass(task_specification)

    def add_pass(self, emulator_pass: Union[Iterable[EmulatorPass], EmulatorPass]) -> EmulatorInterface:
        """
        Append a new EmulatorPass or a list of EmulatorPass objects.

        Args:
            emulator_pass (Union[Iterable[EmulatorPass], EmulatorPass]): Either a
                single EmulatorPass object or a list of EmulatorPass objects that
                will be used in validation and program compilation passes by this
                emulator.
            
        Returns: 
            EmulatorInterface: Returns an updated self. 
            
        """
        if isinstance(emulator_pass, Iterable):
            self._emulator_passes.extend(emulator_pass)
        elif isinstance(emulator_pass, EmulatorPass):
            self._emulator_passes.append(emulator_pass)
        else:
            raise TypeError("emulator_pass must be an EmulatorPass or an iterable of EmulatorPass")
        return self