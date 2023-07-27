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


"""Operators for slices."""

import collections
from typing import Any

import oqpy.base

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm.types import is_qasm_type


class GetItemOpts(collections.namedtuple("GetItemOpts", ("element_dtype",))):
    pass


def get_item(target: Any, i: Any, opts: GetItemOpts) -> Any:
    """The slice read operator (i.e. __getitem__).

    Args:
        target (Any): An entity that supports getitem semantics.
        i (Any): Index to read from.
        opts (GetItemOpts): A GetItemOpts object.

    Returns:
        Any: The read element.
    """
    if is_qasm_type(target) or is_qasm_type(i):
        return _oqpy_get_item(target, i, opts)
    else:
        return _py_get_item(target, i)


def _oqpy_get_item(target: Any, i: Any, opts: GetItemOpts) -> Any:
    """Overload of get_item that produces an oqpy list read."""
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    if isinstance(target, oqpy.ArrayVar):
        base_type = target.base_type
    elif isinstance(target, oqpy.BitVar):
        base_type = type(target)
    else:
        raise TypeError(f"{str(type(target))} object is not subscriptable")

    var = base_type()
    oqpy_program.set(var, target[i])
    return var


def _py_get_item(target: Any, i: Any) -> Any:
    """Overload of get_item that executes a Python list read."""
    return target[i]


def set_item(target: Any, i: Any, x: Any) -> Any:
    """The slice write operator (i.e. __setitem__).

    Note: it is unspecified whether target will be mutated or not. In general,
    if target is mutable (like Python lists), it will be mutated.

    Args:
        target (Any): An entity that supports setitem semantics.
        i (Any): Index to modify.
        x (Any): The new element value.

    Returns:
        Any: Same as target, after the update was performed.
    """
    if is_qasm_type(target) or is_qasm_type(i):
        return _oqpy_set_item(target, i, x)
    else:
        return _py_set_item(target, i, x)


def _oqpy_set_item(target: Any, i: Any, x: Any) -> Any:
    """Overload of set_item that produces an oqpy list modification."""
    if not isinstance(target, oqpy.BitVar):
        raise NotImplementedError("Slice assignment is not supported.")

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    if x.name in oqpy_program.declared_vars.keys() or x.init_expression is None:
        value = x
    else:
        # Set to `x.init_expression` to avoid declaring an unnecessary variable.
        value = x.init_expression
    oqpy_program.set(target[i], value)
    return target


def _py_set_item(target: Any, i: Any, x: Any) -> Any:
    """Overload of set_item that executes a Python list modification."""
    target[i] = x
    return target
