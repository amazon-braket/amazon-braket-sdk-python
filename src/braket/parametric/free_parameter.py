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

from sympy import Symbol

from braket.parametric.free_parameter_expression import FreeParameterExpression

PREDEFINED_VARIABLE_NAMES = {"b", "q"}

# The reserved words are picked from below
# https://github.com/openqasm/openqasm/blob/main/source/grammar/qasm3Lexer.g4
# https://github.com/openqasm/openpulse-python/blob/main/source/grammar/openpulseLexer.g4
QASM_RESERVED_WORDS = {
    "OPENQASM",
    "include",
    "defcalgrammar",
    "def",
    "cal",
    "defcal",
    "gate",
    "extern",
    "box",
    "let",
    "break",
    "continue",
    "if",
    "else",
    "end",
    "return",
    "for",
    "while",
    "in",
    "pragma",
    "input",
    "output",
    "const",
    "readonly",
    "mutable",
    "qreg",
    "qubit",
    "creg",
    "bool",
    "bit",
    "int",
    "uint",
    "float",
    "angle",
    "complex",
    "array",
    "void",
    "duration",
    "stretch",
    "gphase",
    "inv",
    "pow",
    "ctrl",
    "negctrl",
    "dim",
    "durationof",
    "delay",
    "reset",
    "measure",
    "barrier",
    "true",
    "false",
    "waveform",
    "port",
    "frame",
}


class FreeParameter(FreeParameterExpression):
    """Class 'FreeParameter'

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
        """Initializes a new :class:'FreeParameter' object.

        Args:
            name (str): Name of the :class:'FreeParameter'. Can be a unicode value.

        Examples:
            >>> param1 = FreeParameter("theta")
            >>> param1 = FreeParameter("\u03b8")
        """
        self._set_name(name)
        super().__init__(expression=self._name)

    @property
    def name(self) -> str:
        """str: Name of this parameter."""
        return self._name.name

    def subs(self, parameter_values: dict[str, Number]) -> FreeParameter | Number:
        """Substitutes a value in if the parameter exists within the mapping.

        Args:
            parameter_values (dict[str, Number]): A mapping of parameter to its
                corresponding value.

        Returns:
            Union[FreeParameter, Number]: The substituted value if this parameter is in
            parameter_values, otherwise returns self
        """
        return parameter_values.get(self.name, self)

    def __str__(self):
        return str(self.name)

    def __hash__(self) -> int:
        return hash(tuple(self.name))

    def __eq__(self, other: FreeParameter):
        if isinstance(other, FreeParameter):
            return self._name == other._name
        return super().__eq__(other)

    def __repr__(self) -> str:
        """The representation of the :class:'FreeParameter'.

        Returns:
            str: The name of the class:'FreeParameter' to represent the class.
        """
        return self.name

    def _set_name(self, name: str) -> None:
        if not name:
            raise ValueError("FreeParameter names must be non empty")
        if not isinstance(name, str):
            raise TypeError("FreeParameter names must be strings")
        if not name[0].isalpha() and name[0] != "_":
            raise ValueError("FreeParameter names must start with a letter or an underscore")
        if name in PREDEFINED_VARIABLE_NAMES:
            raise ValueError(
                f"FreeParameter names must not be one of the Braket reserved variable names: "
                f"{PREDEFINED_VARIABLE_NAMES}."
            )
        if name in QASM_RESERVED_WORDS:
            raise ValueError(
                f"FreeParameter names must not be one of the OpenQASM or OpenPulse keywords: "
                f"{QASM_RESERVED_WORDS}."
            )
        self._name = Symbol(name)

    def to_dict(self) -> dict:
        return {
            "__class__": self.__class__.__name__,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, parameter: dict) -> FreeParameter:
        return FreeParameter(parameter["name"])
