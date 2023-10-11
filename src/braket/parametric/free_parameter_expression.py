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

import ast
from numbers import Number
from typing import Any, Union

from sympy import Expr, Float, Symbol, sympify


class FreeParameterExpression:
    """
    Class 'FreeParameterExpression'

    Objects that can take a parameter all inherit from :class:'Parameterizable'.
    FreeParametersExpressions can hold FreeParameters that can later be
    swapped out for a number. Circuits or PulseSequences with FreeParameters
    present will NOT run. Values must be substituted prior to execution.
    """

    def __init__(self, expression: Union[FreeParameterExpression, Number, Expr, str]):
        """
        Initializes a FreeParameterExpression. Best practice is to initialize using
        FreeParameters and Numbers. Not meant to be initialized directly.

        Below are examples of how FreeParameterExpressions should be made.

        Args:
            expression (Union[FreeParameterExpression, Number, Expr, str]): The expression to use.

        Examples:
            >>> expression_1 = FreeParameter("theta") * FreeParameter("alpha")
            >>> expression_2 = 1 + FreeParameter("beta") + 2 * FreeParameter("alpha")
        """
        self._operations = {
            ast.Add: self.__add__,
            ast.Sub: self.__sub__,
            ast.Mult: self.__mul__,
            ast.Pow: self.__pow__,
            ast.USub: self.__neg__,
        }
        if isinstance(expression, FreeParameterExpression):
            self._expression = expression.expression
        elif isinstance(expression, (Number, Expr)):
            self._expression = expression
        elif isinstance(expression, str):
            self._expression = self._parse_string_expression(expression).expression
        else:
            raise NotImplementedError

    @property
    def expression(self) -> Union[Number, Expr]:
        """Gets the expression.
        Returns:
            Union[Number, Expr]: The expression for the FreeParameterExpression.
        """
        return self._expression

    def subs(
        self, parameter_values: dict[str, Number]
    ) -> Union[FreeParameterExpression, Number, Expr]:
        """
        Similar to a substitution in Sympy. Parameters are swapped for corresponding values or
        expressions from the dictionary.

        Args:
            parameter_values (dict[str, Number]): A mapping of parameters to their corresponding
                values to be assigned.

        Returns:
            Union[FreeParameterExpression, Number, Expr]: A numerical value if there are no
            symbols left in the expression otherwise returns a new FreeParameterExpression.
        """
        new_parameter_values = dict()
        for key, val in parameter_values.items():
            if issubclass(type(key), FreeParameterExpression):
                new_parameter_values[key.expression] = val
            else:
                new_parameter_values[key] = val

        subbed_expr = self._expression.subs(new_parameter_values)
        if isinstance(subbed_expr, Number):
            return subbed_expr
        else:
            return FreeParameterExpression(subbed_expr)

    def _parse_string_expression(self, expression: str) -> FreeParameterExpression:
        return self._eval_operation(ast.parse(expression, mode="eval").body)

    def _eval_operation(self, node: Any) -> FreeParameterExpression:
        if isinstance(node, ast.Num):
            return FreeParameterExpression(node.n)
        elif isinstance(node, ast.Name):
            return FreeParameterExpression(Symbol(node.id))
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self._operations.keys():
                raise ValueError(f"Unsupported binary operation: {type(node.op)}")
            return self._eval_operation(node.left)._operations[type(node.op)](
                self._eval_operation(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self._operations.keys():
                raise ValueError(f"Unsupported unary operation: {type(node.op)}", type(node.op))
            return self._eval_operation(node.operand)._operations[type(node.op)]()
        else:
            raise ValueError(f"Unsupported string detected: {node}")

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
            str: The expression of the class:'FreeParameterExpression' to represent the class.
        """
        return repr(self.expression)


def subs_if_free_parameter(parameter: Any, **kwargs) -> Any:
    """Substitute a free parameter with the given kwargs, if any.
    Args:
        parameter (Any): The parameter.
        ``**kwargs``: The kwargs to use to substitute.

    Returns:
        Any: The substituted parameters.
    """
    if isinstance(parameter, FreeParameterExpression):
        substituted = parameter.subs(kwargs)
        if isinstance(substituted, Float):
            substituted = float(substituted)
        return substituted
    return parameter


def _is_float(argument: str) -> bool:
    """
    Checks if a string can be cast into a float.

    Args:
        argument (str): String to check.

    Returns:
        bool: Returns true if the string can be cast as a float. False, otherwise.

    """
    try:
        float(argument)
        return True
    except ValueError:
        return False
