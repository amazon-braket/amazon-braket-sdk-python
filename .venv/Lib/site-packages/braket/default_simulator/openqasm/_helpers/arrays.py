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

from functools import singledispatch
from typing import Optional, Union

import numpy as np

from ..parser.openqasm_ast import (
    ArrayLiteral,
    ArrayReferenceType,
    ArrayType,
    BitstringLiteral,
    BitType,
    BooleanLiteral,
    BoolType,
    ClassicalType,
    DiscreteSet,
    Expression,
    FloatLiteral,
    IndexElement,
    IntegerLiteral,
    IntType,
    RangeDefinition,
    UintType,
)
from .casting import LiteralType, cast_to, convert_string_to_bool_array


def convert_range_def_to_slice(range_def: RangeDefinition) -> slice:
    """Convert AST node into Python slice object"""
    buffer = np.sign(range_def.step.value) if range_def.step is not None else 1
    start = range_def.start.value if range_def.start is not None else None
    stop = (
        range_def.end.value + buffer
        if not (range_def.end is None or range_def.end.value == -1)
        else None
    )
    step = range_def.step.value if range_def.step is not None else None
    return slice(start, stop, step)


def convert_range_def_to_range(range_def: RangeDefinition) -> range:
    """Convert AST node into Python range object"""
    buffer = np.sign(range_def.step.value) if range_def.step is not None else 1
    start = range_def.start.value if range_def.start is not None else 0
    stop = range_def.end.value + buffer
    step = range_def.step.value if range_def.step is not None else 1
    return range(start, stop, step)


def convert_discrete_set_to_list(discrete_set: DiscreteSet) -> list:
    """Convert AST node into Python list object"""
    return [x.value for x in discrete_set.values]


def get_type_width(var_type: ClassicalType):
    if isinstance(var_type, ArrayType):
        return var_type.base_type.size
    elif isinstance(var_type, (IntType, UintType, FloatLiteral, BitType)):
        return var_type.size


@singledispatch
def get_elements(
    value: ArrayLiteral, index: IndexElement, type_width: Optional[IntegerLiteral] = None
) -> ArrayLiteral:
    """Get elements of an Array, given an index."""
    if isinstance(index, DiscreteSet):
        return ArrayLiteral([get_elements(value, [i]) for i in index.values])
    first_index = convert_index(index[0])
    if isinstance(first_index, int):
        if not index[1:]:
            return value.values[first_index]
        return get_elements(value.values[first_index], index[1:], type_width)
    # first_index is a slice
    index_as_range = range(len(value.values))[first_index]
    if not index[1:]:
        return ArrayLiteral([value.values[ix] for ix in index_as_range])
    return ArrayLiteral(
        [get_elements(value.values[ix], index[1:], type_width) for ix in index_as_range]
    )


@get_elements.register
def _(value: IntegerLiteral, index: IndexElement, type_width: IntegerLiteral) -> ArrayLiteral:
    """Get elements of an integer's boolean representation, given an index"""
    if type_width is None:
        raise TypeError("Cannot perform bit operations on an unsized integer")
    binary_rep = ArrayLiteral(
        [BooleanLiteral(x == "1") for x in np.binary_repr(value.value, type_width.value)]
    )
    return get_elements(binary_rep, index)


def create_empty_array(dims: list[IntegerLiteral]) -> ArrayLiteral:
    """Create an empty Array of given dimensions"""
    if len(dims) == 1:
        return ArrayLiteral([None] * dims[0].value)
    return ArrayLiteral([create_empty_array(dims[1:])] * dims[0].value)


def convert_index(index: Union[RangeDefinition, IntegerLiteral]) -> Union[int, slice]:
    """Convert unspecified index type to Python object"""
    if isinstance(index, RangeDefinition):
        return convert_range_def_to_slice(index)
    else:  # IntegerLiteral:
        return index.value


def flatten_indices(indices: list[IndexElement]) -> list:
    """Convert a[i][j][k] to the equivalent a[i, j, k]"""
    result = []
    for index in indices:
        if isinstance(index, DiscreteSet):
            result.append(index)
        else:
            result += index
    return result


def unwrap_var_type(var_type: ClassicalType) -> ClassicalType:
    """
    Return the type that comprises the given type. For example,
    the type Array(dims=[2, 3, 4]) has elements of type Array(dims=[3, 4]).
    Sized bit types are Arrays whose elements have type BoolType.
    """
    if isinstance(var_type, (ArrayType, ArrayReferenceType)):
        if isinstance(var_type.dimensions, Expression):
            num_dimensions = var_type.dimensions.value
            new_dimensions = num_dimensions - 1
        else:
            num_dimensions = len(var_type.dimensions)
            new_dimensions = var_type.dimensions[1:]
        if num_dimensions > 1:
            return type(var_type)(var_type.base_type, new_dimensions)
        else:
            return var_type.base_type
    else:  # isinstance(var_type, BitType):
        return BoolType()


@singledispatch
def update_value(
    current_value: Union[ArrayLiteral, BitstringLiteral],
    value: LiteralType,
    update_indices: list[IndexElement],
    var_type: Union[ClassicalType, type[LiteralType]],
) -> LiteralType:
    """Update an Array, for example: a[4, 1:] = {1, 2, 3}"""
    # current value will be an ArrayLiteral or BitstringLiteral
    if isinstance(current_value, ArrayLiteral):
        first_ix = convert_index(update_indices[0])

        if isinstance(first_ix, int):
            current_value.values[first_ix] = update_value(
                current_value.values[first_ix],
                value,
                update_indices[1:],
                unwrap_var_type(var_type),
            )
        else:
            if not isinstance(value, ArrayLiteral):
                raise ValueError("Must assign Array type to slice")
            index_as_range = range(len(current_value.values))[first_ix]
            if len(index_as_range) != len(value.values):
                raise ValueError(
                    f"Dimensions do not match: {len(index_as_range)}, {len(value.values)}"
                )
            for ix, sub_value in zip(index_as_range, value.values):
                current_value.values[ix] = update_value(
                    current_value.values[ix],
                    sub_value,
                    update_indices[1:],
                    unwrap_var_type(var_type),
                )
        return current_value
    else:
        return cast_to(var_type, value)


@update_value.register
def _(
    current_value: IntegerLiteral,
    value: LiteralType,
    update_indices: list[IndexElement],
    var_type: Union[IntType, UintType],
):
    # called recursively, replacing the whole integer
    if not update_indices:
        return value
    if var_type.size is None:
        raise TypeError("Cannot perform bit operations on an unsized integer")
    if isinstance(var_type, UintType):
        bool_array = convert_string_to_bool_array(
            BitstringLiteral(current_value.value, var_type.size.value)
        )
    else:  # IntType
        sign_bit = BooleanLiteral(current_value.value < 0)
        magnitude_bits = convert_string_to_bool_array(
            BitstringLiteral(np.abs(current_value.value), var_type.size.value - 1)
        )
        bool_array = ArrayLiteral([sign_bit, *magnitude_bits.values])
    return cast_to(var_type, update_value(bool_array, value, update_indices, var_type))
