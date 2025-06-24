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

import warnings
from collections.abc import Iterable
from copy import deepcopy
from functools import singledispatch
from typing import Any, Union

import numpy as np
import sympy
from sympy import Symbol

from ..parser.openqasm_ast import (
    AngleType,
    ArrayLiteral,
    ArrayType,
    BitstringLiteral,
    BitType,
    BooleanLiteral,
    BoolType,
    ClassicalType,
    DiscreteSet,
    Expression,
    FloatLiteral,
    FloatType,
    Identifier,
    IndexedIdentifier,
    IntegerLiteral,
    IntType,
    SymbolLiteral,
    UintType,
)

LiteralType = Union[BooleanLiteral, IntegerLiteral, FloatLiteral, ArrayLiteral, BitstringLiteral]


@singledispatch
def cast_to(into: Union[ClassicalType, type[LiteralType]], variable: LiteralType) -> LiteralType:
    """Cast a variable into a given type. Order of parameters is to enable singledispatch"""
    if type(variable) is into:
        return variable
    if into == BooleanLiteral or isinstance(into, BoolType):
        return BooleanLiteral(bool(variable.value))
    if into == IntegerLiteral:
        return IntegerLiteral(int(variable.value))
    if into == FloatLiteral:
        return FloatLiteral(float(variable.value))
    raise TypeError(f"Cannot cast {type(variable).__name__} into {into.__name__}.")


@cast_to.register
def _(
    into: BitType, variable: Union[BooleanLiteral, ArrayLiteral, BitstringLiteral]
) -> ArrayLiteral:
    """
    Bit types can be sized or not, represented as Boolean literals or Array literals.
    Sized bit types can be instantiated with a Bitstring literal or Array literal.
    """
    if not into.size:
        return cast_to(BooleanLiteral, variable)
    size = into.size.value
    if isinstance(variable, BitstringLiteral):
        variable = convert_string_to_bool_array(variable)
    if (
        not all(isinstance(x, BooleanLiteral) for x in variable.values)
        or len(variable.values) != size
    ):
        raise ValueError(f"Invalid array to cast to bit register of size {size}: {variable}.")
    return ArrayLiteral(deepcopy(variable.values))


@cast_to.register
def _(into: IntType, variable: LiteralType) -> IntegerLiteral:
    """Cast to int with overflow warnings"""
    if isinstance(variable, ArrayLiteral):
        value = int("".join("01"[x.value] for x in variable.values[1:]), base=2)
        if variable.values[0].value:
            value -= 2 ** (len(variable.values) - 1)
    else:
        value = variable.value
        if into.size is not None:
            limit = 2**into.size.value
            value = int(value) % limit
            if (value) >= limit / 2:
                value -= limit
            if value != variable.value:
                warnings.warn(
                    f"Integer overflow for value {variable.value} and size {into.size.value}."
                )
    return IntegerLiteral(value)


@cast_to.register
def _(into: UintType, variable: LiteralType) -> IntegerLiteral:
    """Cast to uint with overflow warnings. Bit registers can be cast to uint."""
    if isinstance(variable, ArrayLiteral):
        return IntegerLiteral(int("".join("01"[x.value] for x in variable.values), base=2))
    value = variable.value
    if into.size is not None:
        limit = 2**into.size.value
        value = int(value) % limit
        if value != variable.value:
            warnings.warn(
                f"Unsigned integer overflow for value {variable.value} and size {into.size.value}."
            )
    return IntegerLiteral(value)


@cast_to.register
def _(into: FloatType, variable: LiteralType) -> FloatLiteral:
    """Cast to float"""
    value = variable.value.evalf() if isinstance(variable, SymbolLiteral) else variable.value
    if into.size is None:
        value = float(value)
    else:
        if into.size.value not in (16, 32, 64):
            raise ValueError("Float size must be one of {16, 32, 64}.")
        value = float(np.array(value, dtype=np.dtype(f"float{into.size.value}")))
    return FloatLiteral(value)


@cast_to.register
def _(into: AngleType, variable: LiteralType) -> SymbolLiteral:
    """Cast angle to float"""
    if into.size is None:
        return SymbolLiteral(variable.value % (2 * sympy.pi))
    raise ValueError("Fixed-bit angles are not supported.")


@cast_to.register
def _(into: ArrayType, variable: Union[ArrayLiteral, DiscreteSet]) -> ArrayLiteral:
    """Cast to Array and enforce dimensions"""
    if len(variable.values) != into.dimensions[0].value:
        raise ValueError(
            f"Size mismatch between dimension of size {into.dimensions[0].value} "
            f"and values length {len(variable.values)}"
        )
    subtype = (
        ArrayType(into.base_type, into.dimensions[1:])
        if len(into.dimensions) > 1
        else into.base_type
    )
    return ArrayLiteral([cast_to(subtype, v) for v in variable.values])


def is_literal(expression: Expression) -> bool:
    return isinstance(
        expression,
        (
            BooleanLiteral,
            IntegerLiteral,
            FloatLiteral,
            BitstringLiteral,
            ArrayLiteral,
            SymbolLiteral,
        ),
    )


def convert_string_to_bool_array(bit_string: BitstringLiteral) -> ArrayLiteral:
    """Convert BitstringLiteral to Boolean ArrayLiteral"""
    return ArrayLiteral(
        [BooleanLiteral(x == "1") for x in np.binary_repr(bit_string.value, bit_string.width)]
    )


def convert_bool_array_to_string(bit_string: ArrayLiteral) -> str:
    """Convert Boolean ArrayLiteral into a binary string"""
    return "".join(("1" if x.value else "0") for x in bit_string.values)


def is_none_like(value: Any) -> bool:
    """Returns whether value is None or an Array of Nones"""
    if isinstance(value, ArrayLiteral):
        return all(is_none_like(v) for v in value.values)
    return value is None


@singledispatch
def get_identifier_name(identifier: Union[Identifier, IndexedIdentifier]) -> str:
    """Get name of an identifier"""
    return identifier.name


@get_identifier_name.register
def _(identifier: IndexedIdentifier) -> str:
    """Get name of an indexed identifier"""
    return identifier.name.name


@singledispatch
def wrap_value_into_literal(value: Any) -> LiteralType:
    """Wrap a primitive variable into an AST node"""
    raise TypeError(f"Cannot wrap {value} into literal type")


@wrap_value_into_literal.register
def _(value: int) -> IntegerLiteral:
    return IntegerLiteral(value)


@wrap_value_into_literal.register
def _(value: float) -> FloatLiteral:
    return FloatLiteral(value)


@wrap_value_into_literal.register
def _(value: bool) -> BooleanLiteral:
    return BooleanLiteral(value)


@wrap_value_into_literal.register
def _(value: Symbol) -> SymbolLiteral:
    return SymbolLiteral(value)


@wrap_value_into_literal.register
def _(value: str) -> BitstringLiteral:
    return BitstringLiteral(value=int(value, base=2), width=len(value))


@wrap_value_into_literal.register(list)
def _(value: Iterable[Any]) -> ArrayLiteral:
    return ArrayLiteral([wrap_value_into_literal(v) for v in value])
