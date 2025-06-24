############################################################################
#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
############################################################################
"""Base classes and conversion methods for OQpy.

This class establishes how expressions are represented in oqpy and how
they are converted to AST nodes.
"""

from __future__ import annotations

import math
import uuid
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Hashable,
    Iterable,
    Optional,
    Protocol,
    Sequence,
    Union,
    cast,
    runtime_checkable,
)

import numpy as np
from openpulse import ast

from oqpy import classical_types

if TYPE_CHECKING:
    from oqpy import Program


class OQPyExpression:
    """Base class for OQPy expressions.

    Subclasses must implement ``to_ast`` method and supply the ``type`` attribute

    Expressions can be composed via overloaded arithmetic and boolean comparison operators
    to create new expressions. Note this means you cannot evaluate expression equality via
    ``==`` which produces a new expression instead of producing a python boolean.
    """

    type: Optional[ast.ClassicalType]

    def to_ast(self, program: Program) -> ast.Expression:
        """Converts the oqpy expression into an ast node."""
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def _to_binary(
        op_name: str,
        first: AstConvertible,
        second: AstConvertible,
        result_type: ast.ClassicalType | None = None,
    ) -> OQPyBinaryExpression:
        """Helper method to produce a binary expression."""
        return OQPyBinaryExpression(ast.BinaryOperator[op_name], first, second, result_type)

    @staticmethod
    def _to_unary(op_name: str, exp: AstConvertible) -> OQPyUnaryExpression:
        """Helper method to produce a binary expression."""
        return OQPyUnaryExpression(ast.UnaryOperator[op_name], exp)

    def __pos__(self) -> OQPyExpression:
        return self

    def __neg__(self) -> OQPyUnaryExpression:
        return self._to_unary("-", self)

    def __add__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("+", self, other)

    def __radd__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("+", other, self)

    def __sub__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("-", self, other)

    def __rsub__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("-", other, self)

    def __mod__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("%", self, other)

    def __rmod__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("%", other, self)

    def __mul__(self, other: AstConvertible) -> OQPyBinaryExpression:
        result_type = compute_product_types(self, other)
        return self._to_binary("*", self, other, result_type)

    def __rmul__(self, other: AstConvertible) -> OQPyBinaryExpression:
        result_type = compute_product_types(other, self)
        return self._to_binary("*", other, self, result_type)

    def __truediv__(self, other: AstConvertible) -> OQPyBinaryExpression:
        result_type = compute_quotient_types(self, other)
        return self._to_binary("/", self, other, result_type)

    def __rtruediv__(self, other: AstConvertible) -> OQPyBinaryExpression:
        result_type = compute_quotient_types(other, self)
        return self._to_binary("/", other, self, result_type)

    def __pow__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("**", self, other)

    def __rpow__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("**", other, self)

    def __lshift__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("<<", self, other)

    def __rlshift__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("<<", other, self)

    def __rshift__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary(">>", self, other)

    def __rrshift__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary(">>", other, self)

    def __and__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("&", self, other)

    def __rand__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("&", other, self)

    def __or__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("|", self, other)

    def __ror__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("|", other, self)

    def __xor__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("^", self, other)

    def __rxor__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("^", other, self)

    def __eq__(self, other: AstConvertible) -> OQPyBinaryExpression:  # type: ignore[override]
        return self._to_binary("==", self, other)

    def __ne__(self, other: AstConvertible) -> OQPyBinaryExpression:  # type: ignore[override]
        return self._to_binary("!=", self, other)

    def __gt__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary(">", self, other)

    def __lt__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("<", self, other)

    def __ge__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary(">=", self, other)

    def __le__(self, other: AstConvertible) -> OQPyBinaryExpression:
        return self._to_binary("<=", self, other)

    def __invert__(self) -> OQPyUnaryExpression:
        return self._to_unary("~", self)

    def __bool__(self) -> bool:
        raise RuntimeError(
            "OQPy expressions cannot be converted to bool. This can occur if you try to check "
            "the equality of expressions using == instead of expr_matches."
        )

    def _expr_matches(self, other: Any) -> bool:
        """Called by expr_matches to compare expression instances."""
        if not isinstance(other, type(self)):
            return False
        return expr_matches(self.__dict__, other.__dict__)


def _get_type(val: AstConvertible) -> Optional[ast.ClassicalType]:
    if isinstance(val, OQPyExpression):
        return val.type
    elif isinstance(val, int):
        return ast.IntType()
    elif isinstance(val, float):
        return ast.FloatType()
    elif isinstance(val, complex):
        return ast.ComplexType(ast.FloatType())
    else:
        raise ValueError(f"Cannot multiply/divide oqpy expression with with {type(val)}")


def compute_product_types(left: AstConvertible, right: AstConvertible) -> ast.ClassicalType:
    """Find the result type for a product of two terms."""
    left_type = _get_type(left)
    right_type = _get_type(right)

    types_map = {
        (ast.FloatType, ast.FloatType): left_type,
        (ast.FloatType, ast.IntType): left_type,
        (ast.FloatType, ast.UintType): left_type,
        (ast.FloatType, ast.DurationType): right_type,
        (ast.FloatType, ast.AngleType): right_type,
        (ast.FloatType, ast.ComplexType): right_type,
        (ast.IntType, ast.FloatType): right_type,
        (ast.IntType, ast.IntType): left_type,
        (ast.IntType, ast.UintType): left_type,
        (ast.IntType, ast.DurationType): right_type,
        (ast.IntType, ast.AngleType): right_type,
        (ast.IntType, ast.ComplexType): right_type,
        (ast.UintType, ast.FloatType): right_type,
        (ast.UintType, ast.IntType): right_type,
        (ast.UintType, ast.UintType): left_type,
        (ast.UintType, ast.DurationType): right_type,
        (ast.UintType, ast.AngleType): right_type,
        (ast.UintType, ast.ComplexType): right_type,
        (ast.DurationType, ast.FloatType): left_type,
        (ast.DurationType, ast.IntType): left_type,
        (ast.DurationType, ast.UintType): left_type,
        (ast.DurationType, ast.DurationType): TypeError(
            "Cannot multiply two durations. You may need to re-group computations to eliminate this."
        ),
        (ast.DurationType, ast.AngleType): TypeError("Cannot multiply duration and angle"),
        (ast.DurationType, ast.ComplexType): TypeError("Cannot multiply duration and complex"),
        (ast.AngleType, ast.FloatType): left_type,
        (ast.AngleType, ast.IntType): left_type,
        (ast.AngleType, ast.UintType): left_type,
        (ast.AngleType, ast.DurationType): TypeError("Cannot multiply angle and duration"),
        (ast.AngleType, ast.AngleType): TypeError("Cannot multiply two angles"),
        (ast.AngleType, ast.ComplexType): TypeError("Cannot multiply angle and complex"),
        (ast.ComplexType, ast.FloatType): left_type,
        (ast.ComplexType, ast.IntType): left_type,
        (ast.ComplexType, ast.UintType): left_type,
        (ast.ComplexType, ast.DurationType): TypeError("Cannot multiply complex and duration"),
        (ast.ComplexType, ast.AngleType): TypeError("Cannot multiply complex and angle"),
        (ast.ComplexType, ast.ComplexType): left_type,
    }

    try:
        result_type = types_map[type(left_type), type(right_type)]
    except KeyError as e:
        raise TypeError(f"Could not identify types for product {left} and {right}") from e
    if isinstance(result_type, Exception):
        raise result_type
    return result_type


def compute_quotient_types(left: AstConvertible, right: AstConvertible) -> ast.ClassicalType:
    """Find the result type for a quotient of two terms."""
    left_type = _get_type(left)
    right_type = _get_type(right)
    float_type = ast.FloatType()

    types_map = {
        (ast.FloatType, ast.FloatType): left_type,
        (ast.FloatType, ast.IntType): left_type,
        (ast.FloatType, ast.UintType): left_type,
        (ast.FloatType, ast.DurationType): TypeError("Cannot divide float by duration"),
        (ast.FloatType, ast.AngleType): TypeError("Cannot divide float by angle"),
        (ast.FloatType, ast.ComplexType): right_type,
        (ast.IntType, ast.FloatType): right_type,
        (ast.IntType, ast.IntType): float_type,
        (ast.IntType, ast.UintType): float_type,
        (ast.IntType, ast.DurationType): TypeError("Cannot divide int by duration"),
        (ast.IntType, ast.AngleType): TypeError("Cannot divide int by angle"),
        (ast.IntType, ast.ComplexType): right_type,
        (ast.UintType, ast.FloatType): right_type,
        (ast.UintType, ast.IntType): float_type,
        (ast.UintType, ast.UintType): float_type,
        (ast.UintType, ast.DurationType): TypeError("Cannot divide uint by duration"),
        (ast.UintType, ast.AngleType): TypeError("Cannot divide uint by angle"),
        (ast.UintType, ast.ComplexType): right_type,
        (ast.DurationType, ast.FloatType): left_type,
        (ast.DurationType, ast.IntType): left_type,
        (ast.DurationType, ast.UintType): left_type,
        (ast.DurationType, ast.DurationType): ast.FloatType(),
        (ast.DurationType, ast.AngleType): TypeError("Cannot divide duration by angle"),
        (ast.DurationType, ast.ComplexType): TypeError("Cannot divide duration by complex"),
        (ast.AngleType, ast.FloatType): left_type,
        (ast.AngleType, ast.IntType): left_type,
        (ast.AngleType, ast.UintType): left_type,
        (ast.AngleType, ast.DurationType): TypeError("Cannot divide by duration"),
        (ast.AngleType, ast.AngleType): float_type,
        (ast.AngleType, ast.ComplexType): TypeError("Cannot divide by angle by complex"),
        (ast.ComplexType, ast.FloatType): left_type,
        (ast.ComplexType, ast.IntType): left_type,
        (ast.ComplexType, ast.UintType): left_type,
        (ast.ComplexType, ast.DurationType): TypeError("Cannot divide by duration"),
        (ast.ComplexType, ast.AngleType): TypeError("Cannot divide by angle"),
        (ast.ComplexType, ast.ComplexType): left_type,
    }

    try:
        result_type = types_map[type(left_type), type(right_type)]
    except KeyError as e:
        raise TypeError(f"Could not identify types for quotient {left} and {right}") from e
    if isinstance(result_type, Exception):
        raise result_type
    return result_type


def logical_and(first: AstConvertible, second: AstConvertible) -> OQPyBinaryExpression:
    """Logical AND."""
    return OQPyBinaryExpression(ast.BinaryOperator["&&"], first, second)


def logical_or(first: AstConvertible, second: AstConvertible) -> OQPyBinaryExpression:
    """Logical OR."""
    return OQPyBinaryExpression(ast.BinaryOperator["||"], first, second)


def expr_matches(a: Any, b: Any) -> bool:
    """Check equality of the given objects.

    This bypasses calling ``__eq__`` on expr objects.
    """
    if a is b:
        return True
    if type(a) is not type(b):
        return False
    if isinstance(a, (list, np.ndarray)):
        if len(a) != len(b):
            return False
        return all(expr_matches(ai, bi) for ai, bi in zip(a, b))
    elif isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(expr_matches(va, b[k]) for k, va in a.items())
    if isinstance(a, OQPyExpression):
        # Bypass `__eq__` which is overloaded on OQPyExpressions
        return a._expr_matches(b)
    else:
        return a == b


@runtime_checkable
class ExpressionConvertible(Protocol):
    """This is the protocol an object can implement in order to be usable as an expression."""

    def _to_oqpy_expression(self) -> AstConvertible: ...  # pragma: no cover


@runtime_checkable
class CachedExpressionConvertible(Protocol):
    """This is the protocol an object can implement in order to be usable as an expression.

    The difference between this and `ExpressionConvertible` is that
    this requires that the result of `_to_cached_oqpy_expression` be
    constant across the lifetime of the OQPy Program. OQPy makes an
    effort to minimize the number of calls to the AST constructor, but
    no guarantees are made about this.
    """

    _oqpy_cache_key: Hashable

    def _to_cached_oqpy_expression(self) -> AstConvertible: ...  # pragma: no cover


class OQPyUnaryExpression(OQPyExpression):
    """An expression consisting of one expression preceded by an operator."""

    def __init__(self, op: ast.UnaryOperator, exp: AstConvertible):
        super().__init__()
        self.op = op
        self.exp = exp
        if isinstance(exp, OQPyExpression):
            self.type = exp.type
        else:
            raise TypeError("exp is not an expression")

    def to_ast(self, program: Program) -> ast.UnaryExpression:
        """Converts the OQpy expression into an ast node."""
        return ast.UnaryExpression(self.op, to_ast(program, self.exp))


class OQPyBinaryExpression(OQPyExpression):
    """An expression consisting of two subexpressions joined by an operator."""

    def __init__(
        self,
        op: ast.BinaryOperator | str,
        lhs: AstConvertible,
        rhs: AstConvertible,
        ast_type: ast.ClassicalType | None = None,
    ):
        super().__init__()
        if isinstance(op, str):
            try:
                op = ast.BinaryOperator[op]
            except KeyError as e:
                raise ValueError(f"Invalid binary operator {op}") from e
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        # TODO (#9): More robust type checking which considers both arguments
        #   types, as well as the operator.
        if ast_type is None:
            if isinstance(lhs, OQPyExpression):
                ast_type = lhs.type
            elif isinstance(rhs, OQPyExpression):
                ast_type = rhs.type
            else:
                raise TypeError(
                    "Cannot infer ast_type from lhs or rhs. Please provide it if possible."
                )
        self.type = ast_type

        # Adding floats to durations is not allowed. So we promote types as necessary.
        if isinstance(self.type, ast.DurationType) and self.op in [
            ast.BinaryOperator["+"],
            ast.BinaryOperator["-"],
        ]:
            # Late import to avoid circular imports.
            from oqpy.timing import convert_float_to_duration

            self.lhs = convert_float_to_duration(self.lhs)
            self.rhs = convert_float_to_duration(self.rhs)

    def to_ast(self, program: Program) -> ast.BinaryExpression:
        """Converts the OQpy expression into an ast node."""
        return ast.BinaryExpression(self.op, to_ast(program, self.lhs), to_ast(program, self.rhs))


class Var(ABC):
    """Abstract base class for both classical and quantum variables."""

    def __init__(self, name: str, needs_declaration: bool = True):
        self.name = name
        self._needs_declaration = needs_declaration

    def _var_matches(self, other: Any) -> bool:
        """Return true if this object represents the same variable as other.

        Needed because we overload ``==`` for expressions.
        """
        if isinstance(self, OQPyExpression):
            return expr_matches(self, other)
        else:
            return self == other

    @abstractmethod
    def to_ast(self, program: Program) -> ast.Expression:
        """Converts the OQpy variable into an ast node."""
        ...

    @abstractmethod
    def make_declaration_statement(self, program: Program) -> ast.Statement:
        """Make an ast statement that declares the OQpy variable."""
        ...


@runtime_checkable
class HasToAst(Protocol):
    """Protocol for objects which can be converted into ast nodes."""

    def to_ast(self, program: Program) -> ast.Expression:
        """Converts the OQpy object into an ast node."""
        ...  # pragma: no cover


AstConvertible = Union[
    HasToAst,
    bool,
    int,
    float,
    complex,
    Iterable,
    ExpressionConvertible,
    CachedExpressionConvertible,
    ast.Expression,
]


def to_ast(program: Program, item: AstConvertible) -> ast.Expression:
    """Convert an object to an AST node."""
    if hasattr(item, "_to_oqpy_expression"):
        item = cast(ExpressionConvertible, item)._to_oqpy_expression()
    if hasattr(item, "_to_cached_oqpy_expression"):
        item = cast(CachedExpressionConvertible, item)
        if item._oqpy_cache_key is None:
            item._oqpy_cache_key = uuid.uuid1()
        if item._oqpy_cache_key not in program.expr_cache:
            program.expr_cache[item._oqpy_cache_key] = to_ast(
                program, item._to_cached_oqpy_expression()
            )
        return program.expr_cache[item._oqpy_cache_key]
    if isinstance(item, (complex, np.complexfloating)):
        if item.imag == 0:
            return to_ast(program, item.real)
        if item.real == 0:
            if item.imag < 0:
                return ast.UnaryExpression(ast.UnaryOperator["-"], ast.ImaginaryLiteral(-item.imag))
            else:
                return ast.ImaginaryLiteral(item.imag)
        if item.imag < 0:
            return ast.BinaryExpression(
                ast.BinaryOperator["-"],
                ast.FloatLiteral(item.real),
                ast.ImaginaryLiteral(-item.imag),
            )
        return ast.BinaryExpression(
            ast.BinaryOperator["+"], ast.FloatLiteral(item.real), ast.ImaginaryLiteral(item.imag)
        )
    if isinstance(item, (bool, np.bool_)):
        return ast.BooleanLiteral(item)
    if isinstance(item, (int, np.integer)):
        item = int(item)
        if item < 0:
            return ast.UnaryExpression(ast.UnaryOperator["-"], ast.IntegerLiteral(-item))
        return ast.IntegerLiteral(item)
    if isinstance(item, (float, np.floating)):
        if item < 0:
            if program.simplify_constants:
                neg_ast_term = detect_and_convert_constants(-item, program)
            else:
                neg_ast_term = ast.FloatLiteral(-item)
            return ast.UnaryExpression(ast.UnaryOperator["-"], neg_ast_term)
        if program.simplify_constants:
            return detect_and_convert_constants(item, program)
        return ast.FloatLiteral(item)
    if isinstance(item, slice):
        return ast.RangeDefinition(
            to_ast(program, item.start) if item.start is not None else None,
            to_ast(program, item.stop - 1) if item.stop is not None else None,
            to_ast(program, item.step) if item.step is not None else None,
        )
    if isinstance(item, Iterable):
        return ast.ArrayLiteral([to_ast(program, i) for i in item])
    if isinstance(item, ast.Expression):
        return item
    if hasattr(item, "to_ast"):  # Using isinstance(HasToAst) slowish
        return item.to_ast(program)
    raise TypeError(f"Cannot convert {item} of type {type(item)} to ast")


def optional_ast(program: Program, item: AstConvertible | None) -> ast.Expression | None:
    """Convert item to ast if it is not None."""
    if item is None:
        return None
    return to_ast(program, item)


def map_to_ast(program: Program, items: Iterable[AstConvertible]) -> list[ast.Expression]:
    """Convert a sequence of items into a sequence of ast nodes."""
    return [to_ast(program, item) for item in items]


def make_annotations(vals: Sequence[str | tuple[str, str]]) -> list[ast.Annotation]:
    """Convert strings/tuples of strings into Annotation ast nodes."""
    anns: list[ast.Annotation] = []
    for val in vals:
        if isinstance(val, str):
            anns.append(ast.Annotation(val))
        else:
            keyword, command = val
            anns.append(ast.Annotation(keyword, command))
    return anns


def detect_and_convert_constants(val: float | np.floating[Any], program: Program) -> ast.Expression:
    """Construct a float ast expression which is either a literal or an expression using constants."""
    if val == 0:
        return ast.FloatLiteral(val)
    if val < 0.5 or val > 100:
        return ast.FloatLiteral(val)
    x = val / (math.pi / 4.0)
    rx = round(x)
    if not math.isclose(x, rx, rel_tol=1e-12):
        return ast.FloatLiteral(val)
    term: OQPyExpression
    if rx == 4:
        term = classical_types.pi
    elif rx == 2:
        term = classical_types.pi / 2
    elif rx == 1:
        term = classical_types.pi / 4
    elif rx % 4 == 0:
        term = (rx // 4) * classical_types.pi
    elif rx % 2 == 0:
        term = (rx // 2) * classical_types.pi / 2
    else:
        term = rx * classical_types.pi / 4
    return term.to_ast(program)
