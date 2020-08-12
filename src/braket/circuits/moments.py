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

from typing import (
    Dict,
    ItemsView,
    Iterable,
    KeysView,
    List,
    Mapping,
    NamedTuple,
    OrderedDict,
    ValuesView,
)

from braket.circuits.instruction import Instruction
from braket.circuits.qubit import Qubit
from braket.circuits.qubit_set import QubitSet


class MomentsKey(NamedTuple):
    """Key of the Moments mapping."""

    time: int
    qubits: QubitSet


class Moments(Mapping[MomentsKey, Instruction]):
    """
    An ordered mapping of `MomentsKey` to `Instruction`. The core data structure that
    contains instructions, ordering they are inserted in, and time slices when they
    occur. `Moments` implements `Mapping` and functions the same as a read-only
    dictionary. It is mutable only through the `add()` method.

    This data structure is useful to determine a dependency of instructions, such as
    printing or optimizing circuit structure, before sending it to a quantum
    device. The original insertion order is preserved and can be retrieved via the `values()`
    method.

    Args:
        instructions (Iterable[Instruction], optional): Instructions to initialize self.
            Default = [].

    Examples:
        >>> moments = Moments()
        >>> moments.add([Instruction(Gate.H(), 0), Instruction(Gate.CNot(), [0, 1])])
        >>> moments.add([Instruction(Gate.H(), 0), Instruction(Gate.H(), 1)])
        >>> for i, item in enumerate(moments.items()):
        ...     print(f"Item {i}")
        ...     print(f"\\tKey: {item[0]}")
        ...     print(f"\\tValue: {item[1]}")
        ...
        Item 0
            Key: MomentsKey(time=0, qubits=QubitSet([Qubit(0)]))
            Value: Instruction('operator': H, 'target': QubitSet([Qubit(0)]))
        Item 1
            Key: MomentsKey(time=1, qubits=QubitSet([Qubit(0), Qubit(1)]))
            Value: Instruction('operator': CNOT, 'target': QubitSet([Qubit(0), Qubit(1)]))
        Item 2
            Key: MomentsKey(time=2, qubits=QubitSet([Qubit(0)]))
            Value: Instruction('operator': H, 'target': QubitSet([Qubit(0)]))
        Item 3
            Key: MomentsKey(time=2, qubits=QubitSet([Qubit(1)]))
            Value: Instruction('operator': H, 'target': QubitSet([Qubit(1)]))
    """

    def __init__(self, instructions: Iterable[Instruction] = []):
        self._moments: OrderedDict[MomentsKey, Instruction] = OrderedDict()
        self._max_times: Dict[Qubit, int] = {}
        self._qubits = QubitSet()
        self._depth = 0

        self.add(instructions)

    @property
    def depth(self) -> int:
        """int: Get the depth (number of slices) of self."""
        return self._depth

    @property
    def qubit_count(self) -> int:
        """int: Get the number of qubits used across all of the instructions."""
        return len(self._qubits)

    @property
    def qubits(self) -> QubitSet:
        """
        QubitSet: Get the qubits used across all of the instructions. The order of qubits is based
        on the order in which the instructions were added.

        Note:
            Don't mutate this object, any changes may impact the behavior of this class and / or
            consumers. If you need to mutate this, then copy it via `QubitSet(moments.qubits())`.
        """
        return self._qubits

    def time_slices(self) -> Dict[int, List[Instruction]]:
        """
        Get instructions keyed by time.

        Returns:
            Dict[int, List[Instruction]]: Key is the time and value is a list of instructions that
            occur at that moment in time. The order of instructions is in no particular order.

        Note:
            This is a computed result over self and can be freely mutated. This is re-computed with
            every call, with a computational runtime O(N) where N is the number
            of instructions in self.
        """

        time_slices = {}
        for key, instruction in self._moments.items():
            instructions = time_slices.get(key.time, [])
            instructions.append(instruction)
            time_slices[key.time] = instructions

        return time_slices

    def add(self, instructions: Iterable[Instruction]) -> None:
        """
        Add instructions to self.

        Args:
            instructions (Iterable[Instruction]): Instructions to add to self. The instruction
            is added to the max time slice in which the instruction fits.
        """
        for instruction in instructions:
            self._add(instruction)

    def _add(self, instruction: Instruction) -> None:
        qubit_range = instruction.target
        time = max([self._max_time_for_qubit(qubit) for qubit in qubit_range]) + 1

        # Mark all qubits in qubit_range with max_time
        for qubit in qubit_range:
            self._max_times[qubit] = max(time, self._max_time_for_qubit(qubit))

        self._moments[MomentsKey(time, instruction.target)] = instruction
        self._qubits.update(instruction.target)
        self._depth = max(self._depth, time + 1)

    def _max_time_for_qubit(self, qubit: Qubit) -> int:
        return self._max_times.get(qubit, -1)

    #
    # Implement abstract methods, default to calling selfs underlying dictionary
    #

    def keys(self) -> KeysView[MomentsKey]:
        """Return a view of self's keys."""
        return self._moments.keys()

    def items(self) -> ItemsView[MomentsKey, Instruction]:
        """Return a view of self's (key, instruction)."""
        return self._moments.items()

    def values(self) -> ValuesView[Instruction]:
        """Return a view of self's instructions."""
        return self._moments.values()

    def get(self, key: MomentsKey, default=None) -> Instruction:
        """
        Get the instruction in self by key.

        Args:
            key (MomentsKey): Key of the instruction to fetch.
            default (Any, optional): Value to return if `key` is not in `moments`. Default = `None`.

        Returns:
            Instruction: `moments[key]` if `key` in `moments`, else `default` is returned.
        """
        return self._moments.get(key, default)

    def __getitem__(self, key):
        return self._moments.__getitem__(key)

    def __iter__(self):
        return self._moments.__iter__()

    def __len__(self):
        return self._moments.__len__()

    def __contains__(self, item):
        return self._moments.__contains__(item)

    def __eq__(self, other):
        if isinstance(other, Moments):
            return (self._moments) == (other._moments)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is not NotImplemented:
            return not result
        return NotImplemented

    def __repr__(self):
        return self._moments.__repr__()

    def __str__(self):
        return self._moments.__str__()
