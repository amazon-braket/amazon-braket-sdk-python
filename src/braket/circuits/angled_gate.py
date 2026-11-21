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
from typing import ClassVar

from sympy import Float

from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.gate import Gate
from braket.circuits.parameterizable import Parameterizable


class _AngledGateBase(Gate, Parameterizable):
    """Shared implementation for gates parameterized by a fixed number of angles.

    Subclasses set `_angle_names` to the constructor keyword of each angle, in order; the
    names are used to rebuild the gate when binding values.
    """

    _angle_names: ClassVar[tuple[str, ...]]

    def __init__(
        self,
        *angles: float | FreeParameterExpression,
        qubit_count: int | None,
        ascii_symbols: Sequence[str],
    ):
        """Initializes the gate, casting numeric angles to `float` so that values such as
        `np.float32` serialize consistently.

        Args:
            *angles (float | FreeParameterExpression): The angles of the gate in
                radians or expression representation.
            qubit_count (int | None): The number of qubits that this gate interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the gate.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, or any angle is `None`
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        if any(angle is None for angle in angles):
            raise ValueError(
                "angle must not be None" if len(angles) == 1 else "angles must not be None"
            )
        self._parameters = [
            angle if isinstance(angle, FreeParameterExpression) else float(angle)
            for angle in angles
        ]

    @property
    def parameters(self) -> list[float | FreeParameterExpression]:
        """Returns the parameters associated with the object, either unbound free parameters or
        bound values.

        Returns:
            list[float | FreeParameterExpression]: The free parameters or fixed value
            associated with the object.
        """
        return self._parameters

    def bind_values(self, **kwargs: FreeParameterExpression | str) -> _AngledGateBase:
        """Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs (FreeParameterExpression | str): The parameters that are being assigned.

        Returns:
            _AngledGateBase: A new Gate of the same type with the requested parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def adjoint(self) -> list[Gate]:
        """Returns the adjoint of this gate as a singleton list.

        Returns:
            list[Gate]: A list containing the adjoint gate.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def __eq__(self, other: _AngledGateBase):
        return (
            isinstance(other, _AngledGateBase)
            and self.name == other.name
            and len(self._parameters) == len(other._parameters)
            and all(map(_angles_equal, self._parameters, other._parameters))
        )

    def __repr__(self):
        return (
            f"{self.name}('angles': ({', '.join(map(str, self._parameters))}), "
            f"'qubit_count': {self.qubit_count})"
        )

    def __hash__(self):
        return hash((self.name, *self._parameters, self.qubit_count))


class AngledGate(_AngledGateBase):
    """Class `AngledGate` represents a quantum gate that operates on N qubits and an angle."""

    _angle_names = ("angle",)

    def __init__(
        self,
        angle: float | FreeParameterExpression,
        qubit_count: int | None,
        ascii_symbols: Sequence[str],
    ):
        """Initializes an `AngledGate`.

        Args:
            angle (float | FreeParameterExpression): The angle of the gate in radians
                or expression representation.
            qubit_count (int | None): The number of qubits that this gate interacts with.
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
        super().__init__(angle, qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    @property
    def angle(self) -> float | FreeParameterExpression:
        """Returns the angle of the gate

        Returns:
            float | FreeParameterExpression: The angle of the gate in radians
        """
        return self._parameters[0]

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

    def __repr__(self):
        return f"{self.name}('angle': {self.angle}, 'qubit_count': {self.qubit_count})"


class DoubleAngledGate(_AngledGateBase):
    """Class `DoubleAngledGate` represents a quantum gate that operates on N qubits and
    two angles.
    """

    _angle_names = ("angle_1", "angle_2")

    def __init__(
        self,
        angle_1: float | FreeParameterExpression,
        angle_2: float | FreeParameterExpression,
        qubit_count: int | None,
        ascii_symbols: Sequence[str],
    ):
        """Inits a `DoubleAngledGate`.

        Args:
            angle_1 (float | FreeParameterExpression): The first angle of the gate in
                radians or expression representation.
            angle_2 (float | FreeParameterExpression): The second angle of the gate in
                radians or expression representation.
            qubit_count (int | None): The number of qubits that this gate interacts with.
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
        super().__init__(angle_1, angle_2, qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    @property
    def angle_1(self) -> float | FreeParameterExpression:
        """Returns the first angle of the gate

        Returns:
            float | FreeParameterExpression: The first angle of the gate in radians
        """
        return self._parameters[0]

    @property
    def angle_2(self) -> float | FreeParameterExpression:
        """Returns the second angle of the gate

        Returns:
            float | FreeParameterExpression: The second angle of the gate in radians
        """
        return self._parameters[1]


class TripleAngledGate(_AngledGateBase):
    """Class `TripleAngledGate` represents a quantum gate that operates on N qubits and
    three angles.
    """

    _angle_names = ("angle_1", "angle_2", "angle_3")

    def __init__(
        self,
        angle_1: float | FreeParameterExpression,
        angle_2: float | FreeParameterExpression,
        angle_3: float | FreeParameterExpression,
        qubit_count: int | None,
        ascii_symbols: Sequence[str],
    ):
        """Inits a `TripleAngledGate`.

        Args:
            angle_1 (float | FreeParameterExpression): The first angle of the gate in
                radians or expression representation.
            angle_2 (float | FreeParameterExpression): The second angle of the gate in
                radians or expression representation.
            angle_3 (float | FreeParameterExpression): The third angle of the gate in
                radians or expression representation.
            qubit_count (int | None): The number of qubits that this gate interacts with.
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
        super().__init__(
            angle_1, angle_2, angle_3, qubit_count=qubit_count, ascii_symbols=ascii_symbols
        )

    @property
    def angle_1(self) -> float | FreeParameterExpression:
        """Returns the first angle of the gate

        Returns:
            float | FreeParameterExpression: The first angle of the gate in radians
        """
        return self._parameters[0]

    @property
    def angle_2(self) -> float | FreeParameterExpression:
        """Returns the second angle of the gate

        Returns:
            float | FreeParameterExpression: The second angle of the gate in radians
        """
        return self._parameters[1]

    @property
    def angle_3(self) -> float | FreeParameterExpression:
        """Returns the third angle of the gate

        Returns:
            float | FreeParameterExpression: The third angle of the gate in radians
        """
        return self._parameters[2]


def _angles_equal(
    angle_1: float | FreeParameterExpression, angle_2: float | FreeParameterExpression
) -> bool:
    if isinstance(angle_1, FreeParameterExpression):
        return angle_1 == angle_2
    return isinstance(angle_2, float) and math.isclose(angle_1, angle_2)


def angled_ascii_characters(gate: str, angle: float | FreeParameterExpression) -> str:
    """Generates a formatted ascii representation of an angled gate.

    Args:
        gate (str): The name of the gate.
        angle (float | FreeParameterExpression): The angle for the gate.

    Returns:
        str: Returns the ascii representation for an angled gate.

    """
    return _multi_angled_ascii_characters(gate, angle)


def _multi_angled_ascii_characters(
    gate: str,
    *angles: float | FreeParameterExpression,
) -> str:
    """Generates a formatted ascii representation of an angled gate.

    Numeric angles are shown to two decimal places; expressions are shown as-is.

    Args:
        gate (str): The name of the gate.
        *angles (float | FreeParameterExpression): angles in radians.

    Returns:
        str: Returns the ascii representation for an angled gate.

    """
    formatted = (f"{angle:{'.2f' if isinstance(angle, float | Float) else ''}}" for angle in angles)
    return f"{gate}({', '.join(formatted)})"


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
    return _get_angles(gate, **kwargs)


def _get_angles(gate: _AngledGateBase, **kwargs: FreeParameterExpression | str) -> _AngledGateBase:
    """Gets the angles with all values substituted in that are requested.

    The new gate is constructed by passing each angle under the keyword named in the gate
    class's `_angle_names`.

    Args:
        gate (_AngledGateBase): The angled gate for which the angles are being obtained.
        **kwargs (FreeParameterExpression | str): The named parameters that are being filled
            for a particular gate.

    Returns:
        _AngledGateBase: A new gate of the same type as `gate` with all angles updated.
    """
    return type(gate)(**{
        name: angle.subs(kwargs) if isinstance(angle, FreeParameterExpression) else angle
        for name, angle in zip(gate._angle_names, gate._parameters, strict=True)
    })
