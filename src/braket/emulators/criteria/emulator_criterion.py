from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict
from braket.circuits import Circuit #TODO: abstract to general task_specification type? Possible w.r.t. noise models?


class EmulatorCriterion(ABC):
    
    @abstractmethod
    def validate(self, circuit: Circuit) -> None: 
        """
        Args: 
            circuit (Circuit): circuit to be evaluated against this criteria.

        Returns: 
            returns nothing if the circuit is valid; otherwise, the appropriate error is raised.
        """
        raise NotImplementedError
    

    @abstractmethod
    def __eq__(self, other: EmulatorCriterion) -> bool:
        raise NotImplementedError