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

from numbers import Number
from typing import Dict, Union
from unicodedata import category

from sympy import Symbol

from braket.parametric.free_parameter_expression import FreeParameterExpression


class FreeParameter(FreeParameterExpression):
    """
    Class 'FreeParameter'

    Free parameters can be used in parameterized circuits. Objects that can take a parameter
    all inherit from :class:'Parameterizable'. The FreeParameter can be swapped in to a circuit
    for a numerical value later on. Circuits with FreeParameters must have all the inputs
    provided at execution or substituted prior to execution.

    Examples:
        >>> alpha, beta = FreeParameter("alpha"), FreeParameter("beta")
        >>> circuit = Circuit().rx(target=0, angle=alpha).ry(target=1, angle=beta)
        >>> circuit = circuit(alpha=0.3)
        >>> device = LocalSimulator()
        >>> device.run(circuit, inputs={'beta': 0.5} shots=10)
    """

    def __init__(self, name: str):
        """
        Initializes a new :class:'FreeParameter' object.

        Args:
            name (str): Name of the :class:'FreeParameter'. Must begin with a letter [A-Za-z],
                an underscore or an element from the Unicode character categories Lu/Ll/Lt/Lm/Lo/Nl.
                Must not begin with two underscores '__'. May contain numbers [0-9] after the
                first characeter.

        Examples:
            >>> param1 = FreeParameter("theta")
            >>> param1 = FreeParameter("\u03B8")
            >>> param1 = FreeParameter("a1")
        """
        FreeParameter._validate_name(name)
        self._name = Symbol(name)
        super().__init__(expression=self._name)

    @property
    def name(self) -> str:
        """
        str: Name of this parameter.
        """
        return self._name.name

    def subs(self, parameter_values: Dict[str, Number]) -> Union[FreeParameter, Number]:
        """
        Substitutes a value in if the parameter exists within the mapping.

        Args:
            parameter_values (Dict[str, Number]): A mapping of parameter to its
                corresponding value.

        Returns:
            Union[FreeParameter, Number]: The substituted value if this parameter is in
            parameter_values, otherwise returns self
        """
        return parameter_values[self.name] if self.name in parameter_values else self

    def __str__(self):
        return str(self.name)

    def __hash__(self) -> int:
        return hash(tuple(self.name))

    def __eq__(self, other):
        if isinstance(other, FreeParameter):
            return self._name == other._name
        return super().__eq__(other)

    def __repr__(self) -> str:
        """
        The representation of the :class:'FreeParameter'.

        Returns:
            str: The name of the class:'FreeParameter' to represent the class.
        """
        return self.name

    def to_dict(self) -> dict:
        return {
            "__class__": self.__class__.__name__,
            "name": self.name,
        }

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name:
            raise ValueError("Symbol names must be non empty")
        if not isinstance(name, str):
            raise TypeError("Symbol name must be a string")
        if name.startswith("_"):
            if name.startswith("__"):
                raise ValueError("Symbol names must not start with two underscores '__'")
        else:
            unicode_category = category(name[0])
            if not unicode_category:
                raise ValueError("Symbol names must start with a valid character")
            if not unicode_category.startswith("L") and unicode_category != "Nl":
                raise ValueError("Symbol names must start with a letter or underscore")

    @classmethod
    def from_dict(cls, parameter: dict) -> FreeParameter:
        return FreeParameter(parameter["name"])
