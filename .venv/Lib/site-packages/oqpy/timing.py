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
"""Constructs for manipulating sequence timing."""

from __future__ import annotations

import contextlib
import warnings
from typing import TYPE_CHECKING, Iterator, cast

from openpulse import ast

from oqpy.base import (
    CachedExpressionConvertible,
    ExpressionConvertible,
    HasToAst,
    OQPyExpression,
    optional_ast,
)
from oqpy.classical_types import AstConvertible

if TYPE_CHECKING:
    from oqpy.program import Program


__all__ = ["Box", "convert_float_to_duration", "convert_float_to_duration", "make_duration"]


@contextlib.contextmanager
def Box(program: Program, duration: AstConvertible | None = None) -> Iterator[None]:
    """Creates a section of the program with a specified duration."""
    if duration is not None:
        duration = convert_float_to_duration(duration, require_nonnegative=True)
    program._push()
    yield
    state = program._pop()
    program._add_statement(ast.Box(optional_ast(program, duration), state.body))


def make_duration(time: AstConvertible) -> HasToAst:
    """Make value into an expression representing a duration."""
    warnings.warn(
        "make_duration name is deprecated in favor of convert_float_to_duration",
        DeprecationWarning,
        stacklevel=2,
    )
    return convert_float_to_duration(time)


def convert_float_to_duration(time: AstConvertible, require_nonnegative: bool = False) -> HasToAst:
    """Make value into an expression representing a duration.

    Args:
      time: the time
      require_nonnegative: if True, raise an exception if the time value is known to
        be negative.
    """
    if hasattr(time, "_to_oqpy_expression"):
        time = cast(ExpressionConvertible, time)
        time = time._to_oqpy_expression()
    if hasattr(time, "_to_cached_oqpy_expression"):
        time = cast(CachedExpressionConvertible, time)
        time = time._to_cached_oqpy_expression()
    if isinstance(time, (float, int)):
        if require_nonnegative and time < 0:
            raise ValueError(f"Expected a non-negative duration, but got {time}")
        return OQDurationLiteral(time)
    if isinstance(time, OQPyExpression):
        if isinstance(time.type, (ast.UintType, ast.IntType, ast.FloatType)):
            time = time * OQDurationLiteral(1)
        elif not isinstance(time.type, ast.DurationType):
            raise TypeError(f"Cannot convert expression with type {time.type} to duration")
    if hasattr(time, "to_ast"):
        return time  # type: ignore[return-value]
    raise TypeError(
        f"Expected either float, int, HasToAst or ExpressionConverible: Got {type(time)}"
    )


def convert_duration_to_float(value: AstConvertible) -> AstConvertible:
    if isinstance(value, OQPyExpression) and isinstance(value.type, ast.DurationType):
        value = value / OQDurationLiteral(1)
    return value


class OQDurationLiteral(OQPyExpression):
    """An expression corresponding to a duration literal."""

    def __init__(self, duration_seconds: float) -> None:
        super().__init__()
        self.duration_seconds = duration_seconds
        self.type = ast.DurationType()

    def to_ast(self, program: Program) -> ast.DurationLiteral:
        # Todo (#53): make better units?
        n = program.DURATION_MAX_DIGITS
        if self.duration_seconds >= 1:
            return ast.DurationLiteral(round(self.duration_seconds, n), ast.TimeUnit.s)
        if self.duration_seconds >= 1e-3:
            return ast.DurationLiteral(round(1e3 * self.duration_seconds, n), ast.TimeUnit.ms)
        if self.duration_seconds >= 1e-6:
            return ast.DurationLiteral(round(1e6 * self.duration_seconds, n), ast.TimeUnit.us)
        return ast.DurationLiteral(round(1e9 * self.duration_seconds, n), ast.TimeUnit.ns)
