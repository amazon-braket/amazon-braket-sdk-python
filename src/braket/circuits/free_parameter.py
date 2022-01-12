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

from numbers import Number

from sympy import Symbol


class FreeParameter:
    """
    Class 'FreeParameter'
    """

    def __init__(self, name: str):
        """
        Initializes a new :class:'FreeParameter' object.
        Free parameters can be used in parameterized circuits.

        Args:
            name (str): Name of the :class:'FreeParameter'. Can be a unicode value.

        Examples:
            >>> param1 = FreeParameter("theta")
            >>> param1 = FreeParameter("\u03B8")
        """
        self._name = Symbol(name)
        self._parameter_value = Number

    @property
    def name(self) -> str:
        """
        Returns:
            str: Name of this parameter.
        """
        return self._name.name

    @property
    def parameter_value(self) -> Number:
        """
        This is set to None until a value is assigned.

        Returns:
            Number: The value assigned to a parameter.
        """
        return self._parameter_value

    def fix_value(self, param_value: Number) -> None:
        """
        Sets the value for a :class:'FreeParameter'.

        Args:
            param_value: The value to be set for the object.
        """
        self._validate_values(param_value)
        self._parameter_value = float(param_value)

    def _validate_values(self, param_value):
        """
        Validates that the param_value being passed in is numeric. Raises a ValueError otherwise.

        Args:
            param_values: A value to be checked.

        Raises:
            ValueError: If the param_value is not a Number.

        """
        if not isinstance(param_value, Number):
            raise ValueError(
                f"Parameters value assignment can only take numeric values. "
                f"Invalid inputs: {param_value}"
            )

    def __str__(self):
        return str(self.name)

    def __hash__(self) -> int:
        return hash(tuple(self.name))

    def __eq__(self, other):
        if isinstance(other, FreeParameter):
            return self.name == other.name
        return False

    def __repr__(self):
        """
        The representation of the :class:'FreeParameter'.

        Returns:
            The name of the class:'FreeParameter' to represent the class.
        """
        return self.name
