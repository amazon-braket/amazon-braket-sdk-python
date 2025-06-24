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
"""Classes representing oqpy variables with classical types."""

from __future__ import annotations

import functools
import random
import string
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from openpulse import ast

from oqpy.base import (
    AstConvertible,
    OQPyExpression,
    Var,
    make_annotations,
    map_to_ast,
    optional_ast,
    to_ast,
)
from oqpy.timing import convert_float_to_duration

if TYPE_CHECKING:
    from typing import Literal

    from oqpy.program import Program

    if sys.version_info < (3, 10):
        EllipsisType = type(Ellipsis)
    else:
        from types import EllipsisType

__all__ = [
    "pi",
    "ArrayVar",
    "BoolVar",
    "IntVar",
    "UintVar",
    "FloatVar",
    "AngleVar",
    "BitVar",
    "ComplexVar",
    "DurationVar",
    "OQFunctionCall",
    "OQIndexExpression",
    "StretchVar",
    "_ClassicalVar",
    "duration",
    "stretch",
    "bool_",
    "bit_",
    "bit",
    "bit8",
    "convert_range",
    "int_",
    "int32",
    "int64",
    "uint_",
    "uint32",
    "uint64",
    "float_",
    "float32",
    "float64",
    "complex_",
    "complex64",
    "complex128",
    "angle_",
    "angle32",
    "arrayreference_",
]

# The following methods and constants are useful for creating signatures
# for openqasm function calls, as is required when specifying
# waveform generating methods.
# If you wish to create a variable with a particular type, please use the
# subclasses of ``_ClassicalVar`` instead.


def int_(size: int | None = None) -> ast.IntType:
    """Create a sized signed integer type."""
    return ast.IntType(ast.IntegerLiteral(size) if size is not None else None)


def uint_(size: int | None = None) -> ast.UintType:
    """Create a sized unsigned integer type."""
    return ast.UintType(ast.IntegerLiteral(size) if size is not None else None)


def float_(size: int | None = None) -> ast.FloatType:
    """Create a sized floating-point type."""
    return ast.FloatType(ast.IntegerLiteral(size) if size is not None else None)


def angle_(size: int | None = None) -> ast.AngleType:
    """Create a sized angle type."""
    return ast.AngleType(ast.IntegerLiteral(size) if size is not None else None)


def complex_(size: int) -> ast.ComplexType:
    """Create a sized complex type.

    Note the size represents the total size, and thus the components have
    half of the requested size.
    """
    return ast.ComplexType(ast.FloatType(ast.IntegerLiteral(size // 2)))


def bit_(size: int | None = None) -> ast.BitType:
    """Create a sized bit type."""
    return ast.BitType(ast.IntegerLiteral(size) if size is not None else None)


def arrayreference_(
    dtype: Union[
        ast.IntType,
        ast.UintType,
        ast.FloatType,
        ast.AngleType,
        ast.DurationType,
        ast.BitType,
        ast.BoolType,
        ast.ComplexType,
    ],
    dims: int | list[int],
) -> ast.ArrayReferenceType:
    """Create an array reference type."""
    dim = (
        ast.IntegerLiteral(dims) if isinstance(dims, int) else [ast.IntegerLiteral(d) for d in dims]
    )
    return ast.ArrayReferenceType(base_type=dtype, dimensions=dim)


duration = ast.DurationType()
stretch = ast.StretchType()
bool_ = ast.BoolType()
bit = ast.BitType()
bit8 = bit_(8)
int32 = int_(32)
int64 = int_(64)
uint32 = uint_(32)
uint64 = uint_(64)
float32 = float_(32)
float64 = float_(64)
complex64 = complex_(64)
complex128 = complex_(128)
angle32 = angle_(32)


def convert_range(program: Program, item: Union[slice, range]) -> ast.RangeDefinition:
    """Convert a slice or range into an ast node."""
    return ast.RangeDefinition(
        to_ast(program, item.start),
        to_ast(program, item.stop - 1),
        to_ast(program, item.step) if item.step != 1 else None,
    )


class Identifier(OQPyExpression):
    """Base class to specify constant symbols."""

    name: str

    def __init__(self, name: str, ast_type: ast.ClassicalType) -> None:
        self.name = name
        self.type = ast_type

    def to_ast(self, program: Program) -> ast.Expression:
        return ast.Identifier(name=self.name)


pi = Identifier(name="pi", ast_type=ast.FloatType())


class _ClassicalVar(Var, OQPyExpression):
    """Base type for variables with classical type.

    Subclasses should supply the type_cls class variable.
    """

    type_cls: Type[ast.ClassicalType]

    def __init__(
        self,
        init_expression: AstConvertible | Literal["input", "output"] | None = None,
        name: str | None = None,
        needs_declaration: bool = True,
        annotations: Sequence[str | tuple[str, str]] = (),
        **type_kwargs: Any,
    ):
        name = name or "".join([random.choice(string.ascii_letters) for _ in range(10)])
        super().__init__(name, needs_declaration=needs_declaration)
        self.type = self.type_cls(**type_kwargs)
        self.init_expression = init_expression
        self.annotations = annotations

    def to_ast(self, program: Program) -> ast.Identifier:
        """Converts the OQpy variable into an ast node."""
        program._add_var(self)
        return ast.Identifier(self.name)

    def make_declaration_statement(self, program: Program) -> ast.Statement:
        """Make an ast statement that declares the OQpy variable."""
        if isinstance(self.init_expression, str) and self.init_expression in ("input", "output"):
            return ast.IODeclaration(
                ast.IOKeyword[self.init_expression], self.type, self.to_ast(program)
            )
        init_expression_ast = optional_ast(program, self.init_expression)
        stmt = ast.ClassicalDeclaration(self.type, self.to_ast(program), init_expression_ast)
        stmt.annotations = make_annotations(self.annotations)
        return stmt


class BoolVar(_ClassicalVar):
    """An (unsized) oqpy variable with bool type."""

    type_cls = ast.BoolType


class _SizedVar(_ClassicalVar):
    """Base class for variables with a specified size."""

    default_size: int | None = None
    size: int | None

    def __class_getitem__(cls: Type[_SizedVarT], item: int | None) -> Callable[..., _SizedVarT]:
        # Allows IntVar[64]() notation
        return functools.partial(cls, size=item)

    def __init__(self, *args: Any, size: int | None | EllipsisType = ..., **kwargs: Any):
        if size is ...:
            self.size = self.default_size
        elif size is None:
            self.size = size
        else:
            if not isinstance(size, int) or size <= 0:
                raise ValueError(
                    f"The size of '{self.type_cls}' objects must be an positive integer."
                )
            self.size = size
        super().__init__(*args, **kwargs, size=ast.IntegerLiteral(self.size) if self.size else None)

    def _validate_getitem_index(self, index: AstConvertible) -> None:
        """Validate the index and variable for `__getitem__`.

        Args:
            var (_SizedVar): Variable to apply `__getitem__`.
            index (AstConvertible): Index for `__getitem__`.
        """
        if self.size is None:
            raise TypeError(f"'{self.name}' is not subscriptable")

        if isinstance(index, int):
            if not 0 <= index < self.size:
                raise IndexError("list index out of range.")
        elif isinstance(index, OQPyExpression):
            if not isinstance(index.type, (ast.IntType, ast.UintType)):
                raise IndexError("The list index must be an integer.")
        else:
            raise IndexError("The list index must be an integer.")


_SizedVarT = TypeVar("_SizedVarT", bound=_SizedVar)


class IntVar(_SizedVar):
    """An oqpy variable with integer type."""

    type_cls = ast.IntType
    default_size = 32


class UintVar(_SizedVar):
    """An oqpy variable with unsigned integer type."""

    type_cls = ast.UintType
    default_size = 32


class FloatVar(_SizedVar):
    """An oqpy variable with floating type."""

    type_cls = ast.FloatType
    default_size = 64


class AngleVar(_SizedVar):
    """An oqpy variable with angle type."""

    type_cls = ast.AngleType
    default_size = 32


class BitVar(_SizedVar):
    """An oqpy variable with bit type."""

    type_cls = ast.BitType

    def __getitem__(self, index: AstConvertible) -> OQIndexExpression:
        self._validate_getitem_index(index)
        return OQIndexExpression(collection=self, index=index, type_=self.type_cls())


class ComplexVar(_ClassicalVar):
    """An oqpy variable with bit type."""

    type_cls = ast.ComplexType
    base_type: ast.FloatType = float64

    def __class_getitem__(cls, item: ast.FloatType) -> Callable[..., ComplexVar]:
        return functools.partial(cls, base_type=item)

    def __init__(
        self,
        init_expression: AstConvertible | Literal["input", "output"] | None = None,
        *args: Any,
        base_type: ast.FloatType = float64,
        **kwargs: Any,
    ) -> None:
        assert isinstance(base_type, ast.FloatType)
        self.base_type = base_type

        if not isinstance(init_expression, (complex, type(None), str, OQPyExpression)):
            init_expression = complex(init_expression)  # type: ignore[arg-type]
        super().__init__(init_expression, *args, **kwargs, base_type=base_type)


class DurationVar(_ClassicalVar):
    """An oqpy variable with duration type."""

    type_cls = ast.DurationType

    def __init__(
        self,
        init_expression: AstConvertible | Literal["input", "output"] | None = None,
        name: str | None = None,
        *args: Any,
        **type_kwargs: Any,
    ) -> None:
        if init_expression is not None and not isinstance(init_expression, str):
            init_expression = convert_float_to_duration(init_expression)
        super().__init__(init_expression, name, *args, **type_kwargs)


class StretchVar(_ClassicalVar):
    """An oqpy variable with stretch type."""

    type_cls = ast.StretchType


AllowedArrayTypes = Union[_SizedVar, DurationVar, BoolVar, ComplexVar]


class ArrayVar(_ClassicalVar):
    """An oqpy array variable."""

    type_cls = ast.ArrayType
    dimensions: list[int]
    base_type: type[AllowedArrayTypes]

    def __class_getitem__(
        cls, item: tuple[type[AllowedArrayTypes], int] | type[AllowedArrayTypes]
    ) -> Callable[..., ArrayVar]:
        # Allows usage like ArrayVar[FloatVar, 32](...) or ArrayVar[FloatVar]
        if isinstance(item, tuple):
            base_type = item[0]
            dimensions = list(item[1:])
            return functools.partial(cls, dimensions=dimensions, base_type=base_type)
        else:
            return functools.partial(cls, base_type=item)

    def __init__(
        self,
        *args: Any,
        dimensions: list[int],
        base_type: type[AllowedArrayTypes] = IntVar,
        **kwargs: Any,
    ) -> None:
        self.dimensions = dimensions
        self.base_type = base_type

        # Creating a dummy variable supports IntVar[64] etc.
        base_type_instance = base_type()
        if isinstance(base_type_instance, _SizedVar):
            array_base_type = base_type_instance.type_cls(
                size=ast.IntegerLiteral(base_type_instance.size)
            )
        elif isinstance(base_type_instance, ComplexVar):
            array_base_type = base_type_instance.type_cls(base_type=base_type_instance.base_type)
        else:
            array_base_type = base_type_instance.type_cls()

        # Automatically handle Duration array.
        if base_type is DurationVar and kwargs["init_expression"] is not None:
            kwargs["init_expression"] = (
                convert_float_to_duration(i) for i in kwargs["init_expression"]
            )

        super().__init__(
            *args,
            **kwargs,
            dimensions=[ast.IntegerLiteral(dimension) for dimension in dimensions],
            base_type=array_base_type,
        )

    def __getitem__(self, index: AstConvertible) -> OQIndexExpression:
        return OQIndexExpression(collection=self, index=index, type_=self.base_type().type_cls())


class OQIndexExpression(OQPyExpression):
    """An oqpy expression corresponding to an index expression."""

    def __init__(self, collection: AstConvertible, index: AstConvertible, type_: ast.ClassicalType):
        self.collection = collection
        self.index = index
        self.type = type_

    def to_ast(self, program: Program) -> ast.IndexExpression:
        """Converts this oqpy index expression into an ast node."""
        return ast.IndexExpression(
            collection=to_ast(program, self.collection), index=[to_ast(program, self.index)]
        )


class OQFunctionCall(OQPyExpression):
    """An oqpy expression corresponding to a function call."""

    def __init__(
        self,
        identifier: Union[str, ast.Identifier],
        args: Union[Iterable[AstConvertible], dict[Any, AstConvertible]],
        return_type: Optional[ast.ClassicalType],
        extern_decl: ast.ExternDeclaration | None = None,
        subroutine_decl: ast.SubroutineDefinition | None = None,
    ):
        """Create a new OQFunctionCall instance.

        Args:
            identifier: The function name.
            args: The function arguments. If passed as a dict, the values are used when
                creating the FunctionCall ast node.
            return_type: The type returned by the function call. If none, returns nothing.
            extern_decl: An optional extern declaration ast node. If present,
                this extern declaration will be added to the top of the program
                whenever this is converted to ast.
            subroutine_decl: An optional subroutine definition ast node. If present,
                this subroutine definition will be added to the top of the program
                whenever this expression is converted to ast.
        """
        super().__init__()
        if isinstance(identifier, str):
            identifier = ast.Identifier(identifier)
        self.identifier = identifier
        self.args = args
        self.type = return_type
        self.extern_decl = extern_decl
        self.subroutine_decl = subroutine_decl

    def to_ast(self, program: Program) -> ast.Expression:
        """Converts the OQpy expression into an ast node."""
        if self.extern_decl is not None:
            program.externs[self.identifier.name] = self.extern_decl
        if self.subroutine_decl is not None:
            program._add_subroutine(self.identifier.name, self.subroutine_decl)
        args = self.args.values() if isinstance(self.args, dict) else self.args
        return ast.FunctionCall(self.identifier, map_to_ast(program, args))
