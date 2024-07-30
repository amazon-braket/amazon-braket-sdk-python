from __future__ import annotations

from typing import Iterable, Union

from braket.emulation.emulator_passes import EmulationPass, ProgramType
from braket.emulation.emulator_passes.gate_device_passes import ValidationPass


class BaseEmulator:
    def __init__(self, emulator_passes: Iterable[EmulationPass] = None):
        self._emulator_passes = emulator_passes if emulator_passes is not None else []

    def run_passes(self, task_specification: ProgramType) -> ProgramType:
        """
        This method passes the input program through the EmulationPasses contained
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

    def validate(self, task_specification: ProgramType) -> None:
        """
        This method passes the input program through EmulationPasses that perform
        only validation, without modifying the input program.

        Args:
            task_specification (ProgramType): The program to validate with this
                emulator's validation passes.
        """
        for emulator_pass in self._emulator_passes:
            if isinstance(emulator_pass, ValidationPass):
                emulator_pass(task_specification)

    def add_pass(
        self, emulator_pass: Union[Iterable[EmulationPass], EmulationPass]
    ) -> BaseEmulator:
        """
        Append a new EmulationPass or a list of EmulationPass objects.

        Args:
            emulator_pass (Union[Iterable[EmulationPass], EmulationPass]): Either a
                single EmulationPass object or a list of EmulationPass objects that
                will be used in validation and program compilation passes by this
                emulator.

        Returns:
            BaseEmulator: Returns an updated self.

        Raises:
            TypeError: If the input is not an iterable or an EmulationPass.

        """
        if isinstance(emulator_pass, Iterable):
            self._emulator_passes.extend(emulator_pass)
        elif isinstance(emulator_pass, EmulationPass):
            self._emulator_passes.append(emulator_pass)
        else:
            raise TypeError(
                "emulator_pass must be an EmulationPass or an iterable of EmulationPass"
            )
        return self
