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


"""Operators for other data structures (e.g. list)."""

import collections
from collections.abc import Iterable
from typing import Any, Optional


class ListPopOpts(collections.namedtuple("ListPopOpts", ("element_dtype", "element_shape"))):
    pass


class ListStackOpts(collections.namedtuple("ListStackOpts", ("element_dtype", "original_call"))):
    pass


def list_append(target: list, element: Any) -> list:
    """The list append function.

    Args:
        target (list): An entity that supports append semantics.
        element (Any): The element to append.

    Returns:
        list: The resulting list after performing the append.
    """
    target.append(element)
    return target


def list_pop(target: list, element: Optional[Any], opts: ListPopOpts) -> tuple:
    """The list pop function.

    Args:
        target (list): An entity that supports append semantics.
        element (Optional[Any]): The element index to pop. If None, pops the last element.
        opts (ListPopOpts): Metadata about the converted pop operation.

    Returns:
        tuple: The resulting list after performing the pop, and the popped item.
    """
    popped = target.pop(element) if element is not None else target.pop()
    return target, popped


def list_stack(target: list, opts: ListStackOpts) -> list:
    """The list stack function.

    Args:
        target (list): An entity that supports stack semantics.
        opts (ListStackOpts): Metadata about the converted stack operation.

    Returns:
        list: The stacked list.
    """
    return opts.original_call(target)


def new_list(iterable: Optional[Iterable] = None) -> list:
    """The list constructor.

    Args:
        iterable (Optional[Iterable]): Optional elements to fill the list with. Defaults to None.

    Returns:
        list: A list-like object. The exact return value depends on the initial elements.
    """
    return list(iterable) if iterable else []
