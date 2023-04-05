from functools import singledispatch
from typing import List, Union

import numpy as np

ControlState = Union[int, List[int], str]


@singledispatch
def _as_list(control_state: ControlState, num_control: int):
    if control_state and len(control_state) != num_control:
        raise ValueError("Control state must be the same length as the number of control qubits.")
    return control_state or [1] * num_control


@_as_list.register
def _(control_state: int, num_control: int):
    if control_state >= 2**num_control:
        raise ValueError(
            "Control state value represents a binary sequence of length greater "
            "than the number of control qubits."
        )
    return [int(x) for x in np.binary_repr(control_state, num_control)]


@_as_list.register
def _(control_state: str, num_control: int):
    if len(control_state) != num_control:
        raise ValueError("Control state must be the same length as the number of control qubits.")
    return [int(x) for x in control_state]
