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

import copy
import math
from collections.abc import Sequence
from functools import singledispatch
from typing import Optional, Union

from sympy import Float

from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.gate import Gate
from braket.circuits.parameterizable import Parameterizable


class DurationGate(Gate, Parameterizable):
    """Class `DurationGate` represents a quantum gate that operates on N qubits and a duration."""

    def __init__(
        self,
        duration: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """Initializes an `DurationGate`.

        Args:
            duration (Union[FreeParameterExpression, float]): The duration of the gate in seconds
                or expression representation.
            qubit_count (Optional[int]): The number of qubits that this gate interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the gate. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.
                For instance, if a CNOT instruction has the control qubit on the first index and
                target qubit on the second index, the ASCII symbols should have `["C", "X"]` to
                correlate a symbol with that index.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, or `duration` is `None`
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        if duration is None:
            raise ValueError("duration must not be None")
        if isinstance(duration, FreeParameterExpression):
            self._parameters = [duration]
        else:
            self._parameters = [
                float(duration)
            ]  # explicit casting in case duration is e.g. np.float32

    @property
    def parameters(self) -> list[Union[FreeParameterExpression, float]]:
        """Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            list[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    @property
    def skip_parameters_in_qasm(self) -> bool:
        """Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            list[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return True

    @property
    def duration(self) -> Union[FreeParameterExpression, float]:
        """Returns the angle of the gate

        Returns:
            Union[FreeParameterExpression, float]: The angle of the gate in radians
        """
        return self._parameters[0]

    def bind_values(self, **kwargs) -> DurationGate:
        """Takes in parameters and attempts to assign them to values.

        Returns:
            DurationGate: A new Gate of the same type with the requested parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def __eq__(self, other: DurationGate):
        return (
            isinstance(other, DurationGate)
            and self.name == other.name
            and _durations_equal(self.duration, other.duration)
        )

    def __repr__(self):
        return f"{self.name}('duration': {self.duration}, 'qubit_count': {self.qubit_count})"

    def __hash__(self):
        return hash((self.name, self.qubit_count, self.duration))


@singledispatch
def _durations_equal(
    duration_1: Union[FreeParameterExpression, float],
    duration_2: Union[FreeParameterExpression, float],
) -> bool:
    return isinstance(duration_2, float) and math.isclose(duration_1, duration_2)


@_durations_equal.register
def _(duration_1: FreeParameterExpression, duration_2: FreeParameterExpression):
    return duration_1 == duration_2


def duration_ascii_characters(gate: str, duration: Union[FreeParameterExpression, float]) -> str:
    """Generates a formatted ascii representation of an angled gate.

    Args:
        gate (str): The name of the gate.
        angle (Union[FreeParameterExpression, float]): The angle for the gate.

    Returns:
        str: Returns the ascii representation for an angled gate.

    """
    return f'{gate}({duration:{".2f" if isinstance(duration, (float, Float)) else ""}})'


def get_duration(gate: DurationGate, **kwargs: FreeParameterExpression | str) -> DurationGate:
    """Gets the angle with all values substituted in that are requested.

    Args:
        gate (AngledGate): The subclass of AngledGate for which the angle is being obtained.
        **kwargs (FreeParameterExpression | str): The named parameters that are being filled
            for a particular gate.

    Returns:
        AngledGate: A new gate of the type of the AngledGate originally used with all
        angles updated.
    """
    new_duration = (
        gate.duration.subs(kwargs)
        if isinstance(gate.duration, FreeParameterExpression)
        else gate.duration
    )
    return type(gate)(duration=new_duration, qubit_count=gate.qubit_count)
