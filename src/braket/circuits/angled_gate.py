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
from functools import singledispatch
from typing import List, Optional, Sequence, Union

from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.gate import Gate
from braket.circuits.parameterizable import Parameterizable


class AngledGate(Gate, Parameterizable):
    """
    Class `AngledGate` represents a quantum gate that operates on N qubits and an angle.
    """

    def __init__(
        self,
        angle: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            angle (Union[FreeParameterExpression, float]): The angle of the gate in radians
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
                `ascii_symbols` length != `qubit_count`, or `angle` is `None`
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        if angle is None:
            raise ValueError("angle must not be None")
        if isinstance(angle, FreeParameterExpression):
            self._parameters = [angle]
        else:
            self._parameters = [float(angle)]  # explicit casting in case angle is e.g. np.float32

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, float]]:
        """
        Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            List[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    @property
    def angle(self) -> Union[FreeParameterExpression, float]:
        """
        Returns the angle for the gate

        Returns:
            Union[FreeParameterExpression, float]: The angle of the gate in radians
        """
        return self._parameters[0]

    def bind_values(self, **kwargs) -> AngledGate:
        """Takes in parameters and attempts to assign them to values.

        Returns:
            AngledGate: A new Gate of the same type with the requested parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def adjoint(self) -> List[Gate]:
        """Returns the adjoint of this gate as a singleton list.

        Returns:
            List[Gate]: A list containing the gate with negated angle.
        """
        new = copy.copy(self)
        new._parameters = [-angle for angle in self._parameters]
        return [new]

    def __eq__(self, other):
        if isinstance(other, AngledGate):
            if isinstance(self.angle, FreeParameterExpression):
                return self.name == other.name and self.angle == other.angle
            else:
                return self.name == other.name and math.isclose(self.angle, other.angle)
        return False

    def __repr__(self):
        return f"{self.name}('angle': {self.angle}, 'qubit_count': {self.qubit_count})"


class DoubleAngledGate(Gate, Parameterizable):
    """
    Class `DoubleAngledGate` represents a quantum gate that operates on N qubits and two angles.
    """

    def __init__(
        self,
        angle_1: Union[FreeParameterExpression, float],
        angle_2: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            angle_1 (Union[FreeParameterExpression, float]): The first angle of the gate in
                radians or expression representation.
            angle_2 (Union[FreeParameterExpression, float]): The second angle of the gate in
                radians or expression representation.
            qubit_count (Optional[int]): The number of qubits that this gate interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the gate. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.
                For instance, if a CNOT instruction has the control qubit on the first index and
                target qubit on the second index, the ASCII symbols should have `["C", "X"]` to
                correlate a symbol with that index.

        Raises:
            ValueError: If `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, or `angle_1` or `angle_2` is `None`
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        if angle_1 is None or angle_2 is None:
            raise ValueError("angles must not be None")
        self._parameters = [
            (
                angle
                if isinstance(angle, FreeParameterExpression)
                else float(angle)  # explicit casting in case angle is e.g. np.float32
            )
            for angle in (angle_1, angle_2)
        ]

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, float]]:
        """
        Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            List[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    @property
    def angle_1(self) -> Union[FreeParameterExpression, float]:
        """
        Returns the first angle for the gate

        Returns:
            Union[FreeParameterExpression, float]: The first angle of the gate in radians
        """
        return self._parameters[0]

    @property
    def angle_2(self) -> Union[FreeParameterExpression, float]:
        """
        Returns the second angle for the gate

        Returns:
            Union[FreeParameterExpression, float]: The second angle of the gate in radians
        """
        return self._parameters[1]

    def bind_values(self, **kwargs) -> AngledGate:
        """
        Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs: The parameters that are being assigned.

        Returns:
            AngledGate: A new Gate of the same type with the requested parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def adjoint(self) -> List[Gate]:
        """Returns the adjoint of this gate as a singleton list.

        Returns:
            List[Gate]: A list containing the gate with negated angle.
        """
        raise NotImplementedError

    def __eq__(self, other):
        return (
            isinstance(other, DoubleAngledGate)
            and self.name == other.name
            and _angles_equal(self.angle_1, other.angle_1)
            and _angles_equal(self.angle_2, other.angle_2)
        )

    def __repr__(self):
        return (
            f"{self.name}('angles': ({self.angle_1}, {self.angle_2}), "
            f"'qubit_count': {self.qubit_count})"
        )


@singledispatch
def _angles_equal(
    angle_1: Union[FreeParameterExpression, float], angle_2: Union[FreeParameterExpression, float]
) -> bool:
    return math.isclose(angle_1, angle_2)


@_angles_equal.register
def _(angle_1: FreeParameterExpression, angle_2: FreeParameterExpression):
    return angle_1 == angle_2
