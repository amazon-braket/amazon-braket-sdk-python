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
from typing import Optional

from sympy import Float

from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.gate import Gate
from braket.circuits.parameterizable import Parameterizable


class AngledGate(Gate, Parameterizable):
    """Class `AngledGate` represents a quantum gate that operates on N qubits and an angle."""

    def __init__(
        self,
        angle: FreeParameterExpression | float,
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """Initializes an `AngledGate`.

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
    def parameters(self) -> list[FreeParameterExpression | float]:
        """Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            list[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    @property
    def angle(self) -> FreeParameterExpression | float:
        """Returns the angle of the gate

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

    def adjoint(self) -> list[Gate]:
        """Returns the adjoint of this gate as a singleton list.

        Returns:
            list[Gate]: A list containing the gate with negated angle.
        """
        gate_ascii_name_index = self.ascii_symbols[0].find("(")
        gate_ascii_name = self.ascii_symbols[0][:gate_ascii_name_index]
        new_ascii_symbols = [
            angled_ascii_characters(gate_ascii_name, -self.angle)
        ] * self.qubit_count
        new = copy.copy(self)
        new._parameters = [-angle for angle in self._parameters]
        new._ascii_symbols = new_ascii_symbols
        return [new]

    def __eq__(self, other: AngledGate):
        return (
            isinstance(other, AngledGate)
            and self.name == other.name
            and _angles_equal(self.angle, other.angle)
        )

    def __repr__(self):
        return f"{self.name}('angle': {self.angle}, 'qubit_count': {self.qubit_count})"

    def __hash__(self):
        return hash((self.name, self.angle, self.qubit_count))


class DoubleAngledGate(Gate, Parameterizable):
    """Class `DoubleAngledGate` represents a quantum gate that operates on N qubits and
    two angles.
    """

    def __init__(
        self,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """Inits a `DoubleAngledGate`.

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
    def parameters(self) -> list[FreeParameterExpression | float]:
        """Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            list[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    @property
    def angle_1(self) -> FreeParameterExpression | float:
        """Returns the first angle of the gate

        Returns:
            Union[FreeParameterExpression, float]: The first angle of the gate in radians
        """
        return self._parameters[0]

    @property
    def angle_2(self) -> FreeParameterExpression | float:
        """Returns the second angle of the gate

        Returns:
            Union[FreeParameterExpression, float]: The second angle of the gate in radians
        """
        return self._parameters[1]

    def bind_values(self, **kwargs: FreeParameterExpression | str) -> AngledGate:
        """Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs (FreeParameterExpression | str): The parameters that are being assigned.

        Returns:
            AngledGate: A new Gate of the same type with the requested parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def adjoint(self) -> list[Gate]:
        """Returns the adjoint of this gate as a singleton list.

        Returns:
            list[Gate]: A list containing the gate with negated angle.
        """
        raise NotImplementedError

    def __eq__(self, other: DoubleAngledGate):
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

    def __hash__(self):
        return hash((self.name, self.angle_1, self.angle_2, self.qubit_count))


class TripleAngledGate(Gate, Parameterizable):
    """Class `TripleAngledGate` represents a quantum gate that operates on N qubits and
    three angles.
    """

    def __init__(
        self,
        angle_1: FreeParameterExpression | float,
        angle_2: FreeParameterExpression | float,
        angle_3: FreeParameterExpression | float,
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """Inits a `TripleAngledGate`.

        Args:
            angle_1 (Union[FreeParameterExpression, float]): The first angle of the gate in
                radians or expression representation.
            angle_2 (Union[FreeParameterExpression, float]): The second angle of the gate in
                radians or expression representation.
            angle_3 (Union[FreeParameterExpression, float]): The third angle of the gate in
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
                `ascii_symbols` length != `qubit_count`, or `angle_1` or `angle_2` or `angle_3`
                 is `None`
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        if angle_1 is None or angle_2 is None or angle_3 is None:
            raise ValueError("angles must not be None")
        self._parameters = [
            (
                angle
                if isinstance(angle, FreeParameterExpression)
                else float(angle)  # explicit casting in case angle is e.g. np.float32
            )
            for angle in (angle_1, angle_2, angle_3)
        ]

    @property
    def parameters(self) -> list[FreeParameterExpression | float]:
        """Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            list[Union[FreeParameterExpression, float]]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    @property
    def angle_1(self) -> FreeParameterExpression | float:
        """Returns the first angle of the gate

        Returns:
            Union[FreeParameterExpression, float]: The first angle of the gate in radians
        """
        return self._parameters[0]

    @property
    def angle_2(self) -> FreeParameterExpression | float:
        """Returns the second angle of the gate

        Returns:
            Union[FreeParameterExpression, float]: The second angle of the gate in radians
        """
        return self._parameters[1]

    @property
    def angle_3(self) -> FreeParameterExpression | float:
        """Returns the third angle of the gate

        Returns:
            Union[FreeParameterExpression, float]: The third angle of the gate in radians
        """
        return self._parameters[2]

    def bind_values(self, **kwargs: FreeParameterExpression | str) -> AngledGate:
        """Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs (FreeParameterExpression | str): The parameters that are being assigned.

        Returns:
            AngledGate: A new Gate of the same type with the requested parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def adjoint(self) -> list[Gate]:
        """Returns the adjoint of this gate as a singleton list.

        Returns:
            list[Gate]: A list containing the gate with negated angle.
        """
        raise NotImplementedError

    def __eq__(self, other: TripleAngledGate):
        return (
            isinstance(other, TripleAngledGate)
            and self.name == other.name
            and _angles_equal(self.angle_1, other.angle_1)
            and _angles_equal(self.angle_2, other.angle_2)
            and _angles_equal(self.angle_3, other.angle_3)
        )

    def __repr__(self):
        return (
            f"{self.name}('angles': ({self.angle_1}, {self.angle_2}, {self.angle_3}), "
            f"'qubit_count': {self.qubit_count})"
        )

    def __hash__(self):
        return hash((self.name, self.angle_1, self.angle_2, self.angle_3, self.qubit_count))


@singledispatch
def _angles_equal(
    angle_1: FreeParameterExpression | float, angle_2: FreeParameterExpression | float
) -> bool:
    return isinstance(angle_2, float) and math.isclose(angle_1, angle_2)


@_angles_equal.register
def _(angle_1: FreeParameterExpression, angle_2: FreeParameterExpression):  # noqa: FURB118
    return angle_1 == angle_2


def angled_ascii_characters(gate: str, angle: FreeParameterExpression | float) -> str:
    """Generates a formatted ascii representation of an angled gate.

    Args:
        gate (str): The name of the gate.
        angle (Union[FreeParameterExpression, float]): The angle for the gate.

    Returns:
        str: Returns the ascii representation for an angled gate.

    """
    return f"{gate}({angle:{'.2f' if isinstance(angle, (float, Float)) else ''}})"


def _multi_angled_ascii_characters(
    gate: str,
    *angles: FreeParameterExpression | float,
) -> str:
    """Generates a formatted ascii representation of an angled gate.

    Args:
        gate (str): The name of the gate.
        *angles (Union[FreeParameterExpression, float]): angles in radians.

    Returns:
        str: Returns the ascii representation for an angled gate.

    """

    def format_string(angle: FreeParameterExpression | float) -> str:
        """Formats an angle for ASCII representation.

        Args:
            angle (FreeParameterExpression | float): The angle to format.

        Returns:
            str: The ASCII representation of the angle.
        """
        return ".2f" if isinstance(angle, (float, Float)) else ""

    return f"{gate}({', '.join(f'{angle:{format_string(angle)}}' for angle in angles)})"


def get_angle(gate: AngledGate, **kwargs: FreeParameterExpression | str) -> AngledGate:
    """Gets the angle with all values substituted in that are requested.

    Args:
        gate (AngledGate): The subclass of AngledGate for which the angle is being obtained.
        **kwargs (FreeParameterExpression | str): The named parameters that are being filled
            for a particular gate.

    Returns:
        AngledGate: A new gate of the type of the AngledGate originally used with all
        angles updated.
    """
    new_angle = (
        gate.angle.subs(kwargs) if isinstance(gate.angle, FreeParameterExpression) else gate.angle
    )
    return type(gate)(angle=new_angle)


def _get_angles(
    gate: DoubleAngledGate | TripleAngledGate, **kwargs: FreeParameterExpression | str
) -> DoubleAngledGate | TripleAngledGate:
    """Gets the angle with all values substituted in that are requested.

    Args:
        gate (DoubleAngledGate | TripleAngledGate): The subclass of multi angle AngledGate for
            which the angle is being obtained.
        **kwargs (FreeParameterExpression | str): The named parameters that are being filled
            for a particular gate.

    Returns:
        DoubleAngledGate | TripleAngledGate: A new gate of the type of the AngledGate
        originally used with all angles updated.
    """
    angles = [f"angle_{i + 1}" for i in range(len(gate._parameters))]
    new_angles_args = {
        angle: (
            getattr(gate, angle).subs(kwargs)
            if isinstance(getattr(gate, angle), FreeParameterExpression)
            else getattr(gate, angle)
        )
        for angle in angles
    }
    return type(gate)(**new_angles_args)
