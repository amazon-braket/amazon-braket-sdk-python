from __future__ import annotations

from functools import singledispatch
from typing import Optional, Union

import numpy as np


class BasisState:
    def __init__(self, state: BasisStateInput, size: Optional[int] = None):
        self.state = _as_tuple(state, size)

    @property
    def size(self) -> int:
        return len(self.state)

    @property
    def as_tuple(self) -> tuple:
        return self.state

    @property
    def as_int(self) -> int:
        return 2 ** np.arange(self.size)[::-1] @ self.state

    @property
    def as_string(self) -> str:
        return "".join(map(str, self.state))

    def __len__(self) -> int:
        return len(self.state)

    def __iter__(self):
        return iter(self.state)

    def __eq__(self, other: BasisState):
        return self.state == other.state

    def __bool__(self):
        return any(self.state)

    def __str__(self):
        return self.as_string

    def __repr__(self):
        return f'BasisState("{self.as_string}")'

    def __getitem__(self, item: int):
        return BasisState(self.state[item])


BasisStateInput = Union[int, list[int], str, BasisState]


@singledispatch
def _as_tuple(state: BasisStateInput, size: int) -> tuple:
    size = size if size is not None else len(state)
    if state and len(state) > size:
        raise ValueError(
            "State value represents a binary sequence of length greater "
            "than the specified number of qubits."
        )
    return (0,) * (size - len(state)) + tuple(state)


@_as_tuple.register
def _(state: int, size: int):
    if size is not None and state >= 2**size:
        raise ValueError(
            "State value represents a binary sequence of length greater "
            "than the specified number of qubits."
        )
    return tuple(int(x) for x in np.binary_repr(state, size))


@_as_tuple.register
def _(state: str, size: int):
    size = size if size is not None else len(state)
    if len(state) > size:
        raise ValueError(
            "State value represents a binary sequence of length greater "
            "than the specified number of qubits."
        )
    # left-pad to match state size
    return (0,) * (size - len(state)) + tuple(int(x) for x in state)
