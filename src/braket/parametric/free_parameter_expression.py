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
import operator
from functools import reduce
from numbers import Number
from typing import Any

import sympy
import sympy.printing
from oqpy.base import OQPyExpression
from oqpy.classical_types import FloatVar


class _OpenQASMPrinter(sympy.printing.StrPrinter):
    """A SymPy string printer that emits valid OpenQASM 3 function names.

    SymPy uses its own canonical names for several functions (e.g. ``asin``,
    ``Mod``, ``Abs``) that differ from the names OpenQASM 3 expects
    (``arcsin``, ``mod``, and no equivalent respectively).  This printer
    overrides the rendering of those functions so that
    ``str(FreeParameterExpression(...))`` always produces a string that can
    be embedded verbatim in an OpenQASM 3 program.
    """

    _FN_MAP: dict[type, str] = {
        sympy.sin: "sin",
        sympy.cos: "cos",
        sympy.tan: "tan",
        sympy.asin: "arcsin",
        sympy.acos: "arccos",
        sympy.atan: "arctan",
        sympy.exp: "exp",
        sympy.log: "log",
        sympy.sqrt: "sqrt",
        sympy.Mod: "mod",
        sympy.ceiling: "ceiling",
        sympy.floor: "floor",
    }

    # Functions with no OpenQASM 3 equivalent — raise at stringify time
    # rather than silently emitting invalid QASM.
    _UNSUPPORTED: frozenset[type] = frozenset({
        sympy.Abs,
        sympy.re,
        sympy.im,
        sympy.conjugate,
    })

    def _print_Function(self, expr: sympy.Expr) -> str:
        fn_type = type(expr)
        if fn_type in self._UNSUPPORTED:
            raise ValueError(
                f"{fn_type.__name__} has no OpenQASM 3 equivalent and cannot be "
                "serialized. Use a supported function instead."
            )
        if fn_type in self._FN_MAP:
            name = self._FN_MAP[fn_type]
            args = ", ".join(self._print(a) for a in expr.args)
            return f"{name}({args})"
        # Fall back to SymPy default for any other function
        return super()._print_Function(expr)


# Module-level singleton printer — reused across calls to avoid repeated
# object creation in hot serialization paths.
_OPENQASM_PRINTER = _OpenQASMPrinter()


class FreeParameterExpression:
    """Class 'FreeParameterExpression'

    Objects that can take a parameter all inherit from :class:'Parameterizable'.
    FreeParametersExpressions can hold FreeParameters that can later be
    swapped out for a number. Circuits or PulseSequences with FreeParameters
    present will NOT run. Values must be substituted prior to execution.
    """

    def __init__(self, expression: FreeParameterExpression | Number | sympy.Expr | str):
        """Initializes a FreeParameterExpression. Best practice is to initialize using
        FreeParameters and Numbers. Not meant to be initialized directly.

        Below are examples of how FreeParameterExpressions should be made.

        Args:
            expression (FreeParameterExpression | Number | Expr | str): The expression to use.

        Raises:
            NotImplementedError: Raised if the expression is not of type
                [FreeParameterExpression, Number, Expr, str]

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
            ast.Div: self.__truediv__,
        }
        if isinstance(expression, FreeParameterExpression):
            self._expression = expression.expression
        elif isinstance(expression, Number | sympy.Expr):
            self._expression = expression
        elif isinstance(expression, str):
            self._expression = self._parse_string_expression(expression).expression
        else:
            raise NotImplementedError

    @property
    def expression(self) -> Number | sympy.Expr:
        """Gets the expression.

        Returns:
            Number | Expr: The expression for the FreeParameterExpression.
        """
        return self._expression

    def subs(
        self, parameter_values: dict[str, Number]
    ) -> FreeParameterExpression | Number | sympy.Expr:
        """
        Similar to a substitution in Sympy. Parameters are swapped for corresponding values or
        expressions from the dictionary.

        Args:
            parameter_values (dict[str, Number]): A mapping of parameters to their corresponding
                values to be assigned.

        Returns:
            FreeParameterExpression | Number | Expr: A numerical value if there are no
            symbols left in the expression otherwise returns a new FreeParameterExpression.
        """
        if isinstance(self._expression, Number):
            return self._expression

        new_parameter_values = {}
        for key, val in parameter_values.items():
            if issubclass(type(key), FreeParameterExpression):
                new_parameter_values[key.expression] = val
            else:
                new_parameter_values[key] = val

        subbed_expr = self._expression.subs(new_parameter_values)
        if isinstance(subbed_expr, Number):
            return subbed_expr
        return FreeParameterExpression(subbed_expr)

    def _parse_string_expression(self, expression: str) -> FreeParameterExpression:
        return self._eval_operation(ast.parse(expression, mode="eval").body)

    # Maps string function names (as they appear in a parsed expression) to
    # the corresponding SymPy functions recognised by _OpenQASMPrinter.
    _STRING_FN_MAP: dict[str, Any] = {
        "sin": sympy.sin,
        "cos": sympy.cos,
        "tan": sympy.tan,
        "arcsin": sympy.asin,
        "arccos": sympy.acos,
        "arctan": sympy.atan,
        "asin": sympy.asin,
        "acos": sympy.acos,
        "atan": sympy.atan,
        "exp": sympy.exp,
        "log": sympy.log,
        "sqrt": sympy.sqrt,
        "ceiling": sympy.ceiling,
        "floor": sympy.floor,
    }

    def _eval_operation(self, node: Any) -> FreeParameterExpression:
        if isinstance(node, ast.Constant):
            return FreeParameterExpression(node.value)
        if isinstance(node, ast.Name):
            return FreeParameterExpression(sympy.Symbol(node.id))
        if isinstance(node, ast.BinOp):
            if type(node.op) not in self._operations:
                raise ValueError(f"Unsupported binary operation: {type(node.op)}")
            return self._eval_operation(node.left)._operations[type(node.op)](
                self._eval_operation(node.right)
            )
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in self._operations:
                raise ValueError(f"Unsupported unary operation: {type(node.op)}", type(node.op))
            return self._eval_operation(node.operand)._operations[type(node.op)]()
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError(f"Unsupported callable in expression: {node.func}")
            fn_name = node.func.id
            if fn_name not in self._STRING_FN_MAP:
                raise ValueError(f"Unsupported function in expression: {fn_name!r}")
            sympy_fn = self._STRING_FN_MAP[fn_name]
            args = [self._eval_operation(a).expression for a in node.args]
            return FreeParameterExpression(sympy_fn(*args))
        raise ValueError(f"Unsupported string detected: {node}")

    def __add__(self, other: FreeParameterExpression):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression + other.expression)
        return FreeParameterExpression(self.expression + other)

    def __radd__(self, other: FreeParameterExpression):
        return FreeParameterExpression(other + self.expression)

    def __sub__(self, other: FreeParameterExpression):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression - other.expression)
        return FreeParameterExpression(self.expression - other)

    def __rsub__(self, other: FreeParameterExpression):
        return FreeParameterExpression(other - self.expression)

    def __mul__(self, other: FreeParameterExpression):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression * other.expression)
        return FreeParameterExpression(self.expression * other)

    def __rmul__(self, other: FreeParameterExpression):
        return FreeParameterExpression(other * self.expression)

    def __truediv__(self, other: FreeParameterExpression):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression / other.expression)
        return FreeParameterExpression(self.expression / other)

    def __rtruediv__(self, other: FreeParameterExpression):
        return FreeParameterExpression(other / self.expression)

    def __pow__(self, other: FreeParameterExpression, modulo: float | None = None):
        if issubclass(type(other), FreeParameterExpression):
            return FreeParameterExpression(self.expression**other.expression)
        return FreeParameterExpression(self.expression**other)

    def __rpow__(self, other: FreeParameterExpression):
        return FreeParameterExpression(other**self.expression)

    def __neg__(self):
        return FreeParameterExpression(-1 * self.expression)

    def __eq__(self, other: FreeParameterExpression):
        if isinstance(other, FreeParameterExpression):
            return sympy.sympify(self.expression).equals(sympy.sympify(other.expression))
        return False

    def __str__(self) -> str:
        """Return the OpenQASM 3-compatible string representation.

        Uses :class:`_OpenQASMPrinter` so that function names match what
        OpenQASM 3 devices expect (e.g. ``arcsin`` rather than ``asin``).

        Returns:
            str: OpenQASM 3-compatible serialization of this expression.
        """
        return _OPENQASM_PRINTER.doprint(self.expression)

    def __repr__(self) -> str:
        """The representation of the :class:'FreeParameterExpression'.

        Returns:
            str: The expression of the class:'FreeParameterExpression' to represent the class.
        """
        return _OPENQASM_PRINTER.doprint(self.expression)

    def _to_oqpy_expression(self) -> OQPyExpression:
        """Transforms into an OQPyExpression.

        Returns:
            OQPyExpression: The AST node.
        """
        ops = {sympy.Add: operator.add, sympy.Mul: operator.mul, sympy.Pow: operator.pow}
        if isinstance(self.expression, tuple(ops)):
            return reduce(
                ops[type(self.expression)],
                (FreeParameterExpression(x)._to_oqpy_expression() for x in self.expression.args),
            )
        if isinstance(self.expression, sympy.Number):
            return float(self.expression)
        fvar = FloatVar(name=self.expression.name, init_expression="input", needs_declaration=False)
        fvar.size = None
        fvar.type.size = None
        return fvar


def subs_if_free_parameter(parameter: Any, **kwargs: FreeParameterExpression | str) -> Any:
    """Substitute a free parameter with the given kwargs, if any.

    Args:
        parameter (Any): The parameter.
        **kwargs (FreeParameterExpression | str): The kwargs to use to substitute.

    Returns:
        Any: The substituted parameters.
    """
    if isinstance(parameter, FreeParameterExpression):
        substituted = parameter.subs(kwargs)
        if isinstance(substituted, sympy.Number):
            substituted = float(substituted)
        return substituted
    return parameter


def _is_float(argument: str) -> bool:
    """Checks if a string can be cast into a float.

    Args:
        argument (str): String to check.

    Returns:
        bool: Returns true if the string can be cast as a float. False, otherwise.

    """
    try:
        float(argument)
    except ValueError:
        return False
    else:
        return True
