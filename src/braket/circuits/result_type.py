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

from typing import Any, Dict

from braket.circuits.qubit import QubitInput
from braket.circuits.qubit_set import QubitSetInput


class ResultType:
    """
    Class `ResultType` represents a requested result type for the circuit.
    This class is considered the result type definition containing
    the metadata that defines what a requested result type is and what it does.
    """

    def __init__(self, ascii_symbol: str):
        """
        Args:
            ascii_symbol (str): ASCII string symbol for the result type. This is used when
                printing a diagram of circuits.

        Raises:
            ValueError: `ascii_symbol` is None
        """

        if ascii_symbol is None:
            raise ValueError(f"ascii_symbol must not be None")

        self._ascii_symbol = ascii_symbol

    @property
    def ascii_symbol(self) -> str:
        """str: Returns the ascii symbol for the requested result type."""
        return self._ascii_symbol

    @property
    def name(self) -> str:
        """
        Returns the name of the result type

        Returns:
            The name of the result type as a string
        """
        return self.__class__.__name__

    def to_ir(self, *args, **kwargs) -> Any:
        """Returns IR object of the result type

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            IR object of the result type
        """
        raise NotImplementedError("to_ir has not been implemented yet.")

    def copy(self, target_mapping: Dict[QubitInput, QubitInput] = {}, target: QubitSetInput = None):
        """
        Return a shallow copy of the result type.

        Note:
            If `target_mapping` is specified, then `self.target` is mapped to the specified
            qubits. This is useful apply an instruction to a circuit and change the target qubits.

        Args:
            target_mapping (dictionary[int or Qubit, int or Qubit], optional): A dictionary of
                qubit mappings to apply to the target. Key is the qubit in this `target` and the
                value is what the key is changed to. Default = {}.
            target (int, Qubit, or iterable of int / Qubit, optional): Target qubits for the new
                instruction.

        Returns:
            ResultType: A shallow copy of the result type.

        Raises:
            TypeError: If both `target_mapping` and `target` are supplied.

        Examples:
            >>> result_type = ResultType.Probabilities(targets=[0])
            >>> new_result_type = result_type.copy()
            >>> new_result_type.targets
            QubitSet(Qubit(0))
            >>> new_result = result_type.copy(target_mapping={0: 5})
            >>> new_result_type.target
            QubitSet(Qubit(5))
            >>> new_result = result_type.copy(target=[5])
            >>> new_result_type.target
            QubitSet(Qubit(5))
        """
        copy = self.__copy__()
        if target_mapping and target is not None:
            raise TypeError("Only 'target_mapping' or 'target' can be supplied, but not both.")
        elif target is not None:
            if hasattr(copy, "target"):
                copy.target = target
        else:
            if hasattr(copy, "target"):
                copy.target = self._target.map(target_mapping)
        return copy

    @classmethod
    def register_result_type(cls, result_type: "ResultType"):
        """Register a result type implementation by adding it into the ResultType class.

        Args:
            result_type (ResultType): ResultType instance to register.
        """
        setattr(cls, result_type.__name__, result_type)

    def __repr__(self) -> str:
        return f"{self.name}()"
