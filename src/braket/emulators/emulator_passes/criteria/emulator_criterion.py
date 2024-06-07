from __future__ import annotations
from abc import abstractmethod
from typing import Dict
from braket.circuits import Circuit #TODO: abstract to general task_specification type? Possible w.r.t. noise models?
from braket.emulators.emulator_passes import EmulatorPass, ProgramType


class EmulatorCriterion(EmulatorPass):
    
    @abstractmethod
    def validate(self, circuit: Circuit) -> None: 
        """
        Args: 
            circuit (Circuit): circuit to be evaluated against this criteria.

        Returns: 
            returns nothing if the circuit is valid; otherwise, the appropriate error is raised.
        """
        raise NotImplementedError
    
    
    def run[ProgramType](self, program: ProgramType) -> ProgramType:
        self.validate(program)
        return program
    
    @abstractmethod
    def __eq__(self, other: EmulatorCriterion) -> bool:
        raise NotImplementedError