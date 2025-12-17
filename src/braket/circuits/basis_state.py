# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
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

import numpy as np


class BasisState:
    def __init__(self, state: BasisStateInput, size: int | None = None):
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


BasisStateInput = int | list[int] | str | BasisState


def _as_tuple(state: BasisStateInput, size: int) -> tuple:
    match state:
        case int():
            if size is not None and state >= 2**size:
                raise ValueError(
                    "State value represents a binary sequence of length greater "
                    "than the specified number of qubits."
                )
            return tuple(int(x) for x in np.binary_repr(state, size))
        case str():
            size = size if size is not None else len(state)
            if len(state) > size:
                raise ValueError(
                    "State value represents a binary sequence of length greater "
                    "than the specified number of qubits."
                )
            # left-pad to match state size
            return (0,) * (size - len(state)) + tuple(int(x) for x in state)
        case _:
            size = size if size is not None else len(state)
            if state and len(state) > size:
                raise ValueError(
                    "State value represents a binary sequence of length greater "
                    "than the specified number of qubits."
                )
            return (0,) * (size - len(state)) + tuple(state)
