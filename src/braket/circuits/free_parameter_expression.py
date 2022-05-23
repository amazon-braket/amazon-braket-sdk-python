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
from typing import Dict

from sympy import Expr, sympify


class FreeParameterExpression:
    """
    Class 'FreeParameterExpression'

    Objects that can take a parameter all inherit from :class:'Parameterizable'.
    FreeParametersExpressions can hold FreeParameters that can later be
    swapped out for a number. Circuits with FreeParameters present will NOT run. Values must
    be substituted prior to execution.
    """

    def __init__(self, expression):
        """
        Initializes a FreeParameterExpression. Best practice is to initialize using
        FreeParameters and Numbers. Not meant to be initialized directly.

        Below are examples of how FreeParameterExpressions should be made.

        Args:
            expression: The expression to use.

        Examples:
            >>> expression_1 = FreeParameter("theta") * FreeParameter("alpha")
            >>> expression_2 = 1 + FreeParameter("beta") + 2 * FreeParameter("alpha")
        """
        if isinstance(expression, FreeParameterExpression):
            self._expression = expression.expression
        elif isinstance(expression, (Number, Expr)):
            self._expression = expression
        else:
            raise NotImplementedError

    @property
    def expression(self):
        """
        Returns:
            The expression for the FreeParameterExpression.
        """
        return self._expression

    def subs(self, parameter_values: Dict[str, Number]):
        """
        Similar to a substitution in Sympy. Parameters are swapped for corresponding values or
        expressions from the dictionary.

        Args:
            parameter_values (Dict[str, Number]): A mapping of parameters to their corresponding
            values to be assigned.

        Returns: A numerical value if there are no symbols left in the expression otherwise
            returns a new FreeParameterExpression.
        """
        new_parameter_values = dict()
        for key, val in parameter_values.items():
            if issubclass(type(key), FreeParameterExpression):
                new_parameter_values[key.expression] = val
            else:
                new_parameter_values[key] = val

        subbed_expr = self._expression.subs(new_parameter_values)
        if subbed_expr.is_Number:
            return subbed_expr
        else:
            return FreeParameterExpression(subbed_expr)

    def __add__(self, other):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression + other.expression)
        else:
            return FreeParameterExpression(self.expression + other)

    def __radd__(self, other):
        return FreeParameterExpression(other + self.expression)

    def __sub__(self, other):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression - other.expression)
        else:
            return FreeParameterExpression(self.expression - other)

    def __rsub__(self, other):
        return FreeParameterExpression(other - self.expression)

    def __mul__(self, other):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression * other.expression)
        else:
            return FreeParameterExpression(self.expression * other)

    def __rmul__(self, other):
        return FreeParameterExpression(other * self.expression)

    def __pow__(self, other, modulo=None):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression**other.expression)
        else:
            return FreeParameterExpression(self.expression**other)

    def __rpow__(self, other):
        return FreeParameterExpression(other**self.expression)

    def __neg__(self):
        return FreeParameterExpression(-1 * self.expression)

    def __eq__(self, other):
        if isinstance(other, FreeParameterExpression):
            return sympify(self.expression).equals(sympify(other.expression))
        return False

    def __repr__(self) -> str:
        """
        The representation of the :class:'FreeParameterExpression'.

        Returns:
            The expression of the class:'FreeParameterExpression' to represent the class.
        """
        return repr(self.expression)
