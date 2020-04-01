# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from __future__ import annotations

from typing import List

import braket.ir.jaqcd as ir
from braket.circuits import circuit
from braket.circuits.qubit_set import QubitSet, QubitSetInput
from braket.circuits.result import Result


"""
To add a new result:
    1. Implement the class and extend `Result`
    2. Add a method with the `@circuit.subroutine(register=True)` decorator. Method name
       will be added into the `Circuit` class. This method is the default way
       clients add this result to a circuit.
    3. Register the class with the `Result` class via `Result.register_result()`.
"""


class StateVector(Result):
    """StateVector as a requested result."""

    def __init__(self):
        super().__init__(ascii_symbol=["StateVector"])

    def to_ir(self) -> ir.StateVector:
        return ir.StateVector()

    @staticmethod
    @circuit.subroutine(register=True)
    def state_vector() -> Result:
        """Registers this function into the circuit class.

        Returns:
            Result: state vector as a requested result

        Examples:
            >>> circ = Circuit().state_vector()
        """
        return Result.StateVector()

    def __eq__(self, other) -> bool:
        if isinstance(other, StateVector):
            return True
        return False

    def __copy__(self) -> StateVector:
        return type(self)()


Result.register_result(StateVector)


class Amplitude(Result):
    """Amplitude as a requested result."""

    def __init__(self, state: List[str]):
        """
        Args:
            state (List[str]): list of quantum states as strings with "0" and "1"

        Raises:
            ValueError: If state is None or an empty list

        Examples:
            >>> Result.Amplitude(state=['01', '10'])
        """
        super().__init__(ascii_symbol=["Amplitude"])
        if not state:
            raise ValueError("A non-empty list of state must be specified e.g. ['01', '10']")
        self._state = state

    @property
    def state(self) -> List[str]:
        return self._state

    def to_ir(self) -> ir.Amplitude:
        return ir.Amplitude(states=self.state)

    @staticmethod
    @circuit.subroutine(register=True)
    def amplitude(state: List[str]) -> Result:
        """Registers this function into the circuit class.

        Args:
            state (List[str]): list of quantum states as strings with "0" and "1"

        Returns:
            Result: state vector as a requested result

        Examples:
            >>> circ = Circuit().amplitude(state=["01", "10"])
        """
        return Result.Amplitude(state=state)

    def __eq__(self, other):
        if isinstance(other, Amplitude):
            return self.state == other.state
        return False

    def __repr__(self):
        return f"Amplitude(state={self.state})"

    def __copy__(self):
        return type(self)(state=self.state)


Result.register_result(Amplitude)


class Probability(Result):
    """Probability as a requested result."""

    def __init__(self, target: QubitSetInput = []):
        """
        Args:
            target (int, Qubit, or iterable of int / Qubit): Target qubits that the result
                is requested for. Default is [], which means all qubits for the circuit.

        Examples:
            >>> Result.Probability(target=[0, 1])
        """
        super().__init__(ascii_symbol=["Prob"])
        self._target = QubitSet(target)

    @property
    def target(self) -> QubitSet:
        return self._target

    @target.setter
    def target(self, target: QubitSetInput = []) -> None:
        self._target = QubitSet(target)

    def to_ir(self) -> ir.Probability:
        return ir.Probability(targets=list(self.target))

    @staticmethod
    @circuit.subroutine(register=True)
    def probability(target: QubitSetInput) -> Result:
        """Registers this function into the circuit class.

        Args:
            target (int, Qubit, or iterable of int / Qubit): Target qubits that the result
                is requested for.

        Returns:
            Result: probability as a requested result

        Examples:
            >>> circ = Circuit().probability(target=[0, 1])
        """
        return Result.Probability(target=target)

    def __eq__(self, other) -> bool:
        if isinstance(other, Probability):
            return self.target == other.target
        return False

    def __repr__(self) -> str:
        return f"Probability(target={self.target})"

    def __copy__(self) -> Probability:
        return type(self)(target=self.target)


Result.register_result(Probability)
