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

import numbers
from typing import Dict

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
            name: Name of the :class:'FreeParameter'. Can be a unicode value.

        Examples:
            >>> param1 = FreeParameter("theta")
            >>> param1 = FreeParameter("\u03B8")
        """
        parameter_symbol = Symbol(name)
        self._name = name
        self._symbol = parameter_symbol
        self._parameter_expression = parameter_symbol
        self._parameter_values = []

    @property
    def name(self):
        """
        Returns:Name for :class:'FreeParameter'.
        """
        return self._name

    @property
    def parameter_values(self):
        """
        Returns:Parameter values for :class:'FreeParameter'.
        """
        return self._parameter_values

    def fix_values(self, param_values):
        """
        Sets the values for a :class:'FreeParameter'.

        Args:
            param_values: The values to be set for the object.
        """
        self._validate_values(param_values)
        for val in param_values:
            param_val = self._parameter_expression.subs(self._symbol, val)
            self._parameter_values.append(float(param_val))

    @property
    def symbol(self):
        """
        Returns:Symbol for :class:'FreeParameter'.
        """
        return self._symbol

    def _validate_values(self, param_values: Dict):
        """
        Validates that all param_values being passed in are numeric. Raises a ValueError otherwise.

        Args:
            param_values: A list of values to be checked.

        Raises:
            ValueError: If the param_values contains an element that is not a Number.

        """
        invalid_params = list(filter(lambda val: not isinstance(val, numbers.Number), param_values))
        if invalid_params:
            raise ValueError(
                f"Parameters value assignment can only take numeric values. "
                f"Invalid inputs: ({invalid_params})"
            )

    def __str__(self):
        return self.name

    def __hash__(self) -> int:
        return hash(tuple(self._name))

    def __eq__(self, other):
        if isinstance(other, FreeParameter):
            return self.name == other.name
        return NotImplemented

    def __repr__(self):
        """
        The representation of the :class:'FreeParameter'.

        Returns: The name of the class:'FreeParameter' to represent the class.
        """
        return self.name
