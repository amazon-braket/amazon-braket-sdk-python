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


"""Operators for control flow constructs (e.g. if, for, while)."""

from typing import Any, Callable, Iterable, Optional, Union

import oqpy.base

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm.types import is_qasm_type


def for_stmt(
    iter: Union[Iterable, oqpy.Range],
    extra_test: Optional[Callable[[], Any]],
    body: Callable[[Any], None],
    get_state: Any,
    set_state: Any,
    symbol_names: Any,
    opts: dict,
) -> None:
    """Implements a for loop.

    Args:
        iter (Union[Iterable, Range]): The iterable to be looped over.
        extra_test (Optional[Callable[[], Any]]): A function to cause the loop to break if true.
        body (Callable[[Any],]): The body of the for loop.
        get_state (Any): Unused.
        set_state (Any): Unused.
        symbol_names (Any): Unused.
        opts (dict): Options of the for loop.
    """
    del get_state, set_state, symbol_names
    if is_qasm_type(iter):
        _oqpy_for_stmt(iter, extra_test, body, opts)
    else:
        _py_for_stmt(iter, extra_test, body)


def _oqpy_for_stmt(
    iter: oqpy.Range,
    extra_test: Callable[[], Any],
    body: Callable[[Any], None],
    opts: dict,
) -> None:
    """Overload of for_stmt that produces an oqpy for loop."""
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    # TODO: Should check extra_test() on each iteration and break if False,
    # but oqpy doesn't currently support break statements at the moment.
    with oqpy.ForIn(oqpy_program, iter, opts["iterate_names"]) as f:
        body(f)


def _py_for_stmt(
    iter: Iterable,
    extra_test: Callable[[], Any],
    body: Callable[[Any], None],
) -> None:
    """Overload of for_stmt that executes a Python for loop."""
    if extra_test is not None:
        raise NotImplementedError("break and return statements are not supported in for loops.")
    else:
        for target in iter:
            body(target)


def while_stmt(
    test: Callable[[], Any],
    body: Callable[[], None],
    get_state: Any,
    set_state: Any,
    symbol_names: Any,
    opts: dict,
) -> None:
    """Implements a while loop.

    Args:
        test (Callable[[], Any]): The condition of the while loop.
        body (Callable[[],]): The body of the while loop.
        get_state (Any): Unused.
        set_state (Any): Unused.
        symbol_names (Any): Unused.
        opts (dict): Options of the while loop.
    """
    del get_state, set_state, symbol_names, opts
    if is_qasm_type(test()):
        _oqpy_while_stmt(test, body)
    else:
        _py_while_stmt(test, body)


def _oqpy_while_stmt(
    test: Callable[[], Any],
    body: Callable[[], None],
) -> None:
    """Overload of while_stmt that produces an oqpy while loop."""
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    with oqpy.While(oqpy_program, test()):
        body()


def _py_while_stmt(
    test: Callable[[], Any],
    body: Callable[[], None],
) -> None:
    """Overload of while_stmt that executes a Python while loop."""
    while test():
        body()


def if_stmt(
    cond: Any,
    body: Callable[[], Any],
    orelse: Callable[[], Any],
    get_state: Any,
    set_state: Any,
    symbol_names: Any,
    nouts: int,
) -> None:
    """Implements an if/else statement.

    Args:
        cond (Any): The condition of the if statement.
        body (Callable[[], Any]): The contents of the if block.
        orelse (Callable[[], Any]): The contents of the else block.
        get_state (Any): Unused.
        set_state (Any): Unused.
        symbol_names (Any): Unused.
        nouts (int): The number of outputs from the if block.
    """
    del get_state, set_state, symbol_names, nouts
    if is_qasm_type(cond):
        _oqpy_if_stmt(cond, body, orelse)
    else:
        _py_if_stmt(cond, body, orelse)


def _oqpy_if_stmt(
    cond: Any,
    body: Callable[[], Any],
    orelse: Callable[[], Any],
) -> None:
    """Overload of if_stmt that stages an oqpy cond."""
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    if isinstance(cond, oqpy.base.Var) and cond.name not in oqpy_program.declared_vars.keys():
        oqpy_program.declare(cond)
    with oqpy.If(oqpy_program, cond):
        body()
    with oqpy.Else(oqpy_program):
        orelse()


def _py_if_stmt(cond: Any, body: Callable[[], Any], orelse: Callable[[], Any]) -> None:
    """Overload of if_stmt that executes a Python if statement."""
    if cond:
        body()
    else:
        orelse()
