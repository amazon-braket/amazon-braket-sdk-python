from __future__ import annotations

from abc import abstractmethod

from braket.circuits import Circuit
from braket.emulators.emulator_passes.emulator_pass import EmulatorPass, ProgramType


class EmulatorCriterion(EmulatorPass):
    @abstractmethod
    def validate(self, circuit: Circuit) -> None:
        """
        An emulator criterion is used to perform some non-modifying validation
        pass on an input program. Implementations of validate should return
        nothing if the input program passes validation and raise an error otherwise.

        Args:
            circuit (Circuit): circuit to be evaluated against this criteria.
        """
        raise NotImplementedError

    def run(self, program: ProgramType) -> ProgramType:
        self.validate(program)
        return program

    @abstractmethod
    def __eq__(self, other: EmulatorCriterion) -> bool:
        raise NotImplementedError
