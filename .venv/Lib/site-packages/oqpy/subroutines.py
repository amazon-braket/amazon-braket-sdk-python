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
"""Contains methods for producing subroutines and extern function calls."""

from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, Sequence, TypeVar, get_type_hints

from mypy_extensions import VarArg
from openpulse import ast

import oqpy.program
from oqpy.base import AstConvertible, OQPyExpression, make_annotations, to_ast
from oqpy.classical_types import OQFunctionCall, _ClassicalVar
from oqpy.quantum_types import Qubit
from oqpy.timing import convert_float_to_duration

__all__ = ["subroutine", "declare_extern", "declare_waveform_generator", "OQPyArgument"]

SubroutineParams = [oqpy.Program, VarArg(AstConvertible)]

FnType = TypeVar("FnType", bound=Callable[..., Any])


@dataclass
class OQPyArgument:
    """An oqpy argument to extern declaration.."""

    name: str
    dtype: ast.ClassicalType
    access: Literal["readonly", "mutable"] | None = None

    def unzip(self) -> tuple[str, ast.ClassicalType, ast.AccessControl | None]:
        """Returns the three values, name, dtype and access as a tuple."""
        return self.name, self.dtype, ast.AccessControl[self.access] if self.access else None


def enable_decorator_arguments(f: FnType) -> Callable[..., FnType]:
    @functools.wraps(f)
    def decorator(*args, **kwargs):  # type: ignore[no-untyped-def]
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return f(args[0])
        else:
            return lambda realf: f(realf, *args, **kwargs)

    return decorator


@enable_decorator_arguments
def subroutine(
    func: Callable[[oqpy.Program, VarArg(AstConvertible)], AstConvertible | None],
    annotations: Sequence[str | tuple[str, str]] = (),
) -> Callable[[oqpy.Program, VarArg(AstConvertible)], OQFunctionCall]:
    """Decorator to declare a subroutine.

    The function should take a program as well as any other arguments required.
    Note that the decorated function must include type hints for all arguments,
    and (other than the initial program) all of these type hints must be oqpy
    Variable types.

    .. code-block:: python

        @subroutine(annotations=("optimize", "-O3"))
        def increment_variable(program: Program, i: IntVar):
            program.increment(i, 1)

        j = IntVar(0)
        increment_variable(j)

    This should generate the following OpenQASM:

    .. code-block:: qasm3

        @optimize -O3
        def increment_variable(int[32] i) {
            i += 1;
        }

        int[32] j = 0;
        increment_variable(j);

    Args:
        func (Callable[[oqpy.Program, VarArg(AstConvertible)], AstConvertible | None]):
            function to decorate. Its first argument must be an OQpy program.
        annotations (Sequence[str | tuple[str, str]]): a collection of strings or
            tuples of string that annotate the subroutine.

    Returns:
        Callable[[oqpy.Program, VarArg(AstConvertible)], AstConvertible | None]:
            decorated function with added subroutine_declaration attribute.
    """
    name = func.__name__
    identifier = ast.Identifier(func.__name__)
    argnames = list(inspect.signature(func).parameters.keys())
    type_hints = get_type_hints(func)
    inputs = {}  # used as inputs when calling the actual python function
    arguments = []  # used in the ast definition of the subroutine
    for argname in argnames[1:]:  # arg 0 should be program
        if argname not in type_hints:
            raise ValueError(f"No type hint provided for {argname} on subroutine {name}.")

        # ArrayVar[] returns a partial function instead of a type.
        # The underlying function of that partial should be ArrayVar itself.
        type_hint = (
            type_hints[argname].func
            if isinstance(type_hints[argname], functools.partial)
            else type_hints[argname]
        )

        if not issubclass(type_hint, (_ClassicalVar, Qubit)):
            raise ValueError(
                f"Type hint for {argname} on subroutine {name} is not an oqpy variable type."
            )

        input_ = inputs[argname] = type_hints[argname](name=argname)

        if isinstance(input_, _ClassicalVar):
            arguments.append(ast.ClassicalArgument(input_.type, ast.Identifier(argname)))
        elif isinstance(input_, Qubit):
            arguments.append(ast.QuantumArgument(ast.Identifier(input_.name), None))

    inner_prog = oqpy.Program()
    for input_val in inputs.values():
        inner_prog._mark_var_declared(input_val)
    output = func(inner_prog, **inputs)
    inner_prog.autodeclare()
    inner_prog._state.finalize_if_clause()
    body = inner_prog._state.body
    if isinstance(output, OQPyExpression):
        return_type = output.type
        body.append(ast.ReturnStatement(to_ast(inner_prog, output)))
    elif output is None:
        return_type = None
        if type_hints.get("return", False):
            return_hint = type_hints["return"]()
            if isinstance(return_hint, _ClassicalVar):
                return_type = return_hint.type
            elif return_hint is not None:
                raise ValueError(
                    f"Type hint for return variable on subroutine {name} is not an oqpy classical type."
                )
    else:
        raise ValueError("Output type of subroutine {name} was neither oqpy expression nor None.")
    stmt = ast.SubroutineDefinition(
        identifier,
        arguments=arguments,
        return_type=return_type,
        body=body,
    )
    stmt.annotations = make_annotations(annotations)

    @functools.wraps(func)
    def wrapper(
        program: oqpy.Program,
        *args: AstConvertible,
    ) -> OQFunctionCall:
        program.defcals.update(inner_prog.defcals)
        for name, subroutine_stmt in inner_prog.subroutines.items():
            program._add_subroutine(name, subroutine_stmt)
        program.externs.update(inner_prog.externs)
        return OQFunctionCall(
            identifier,
            {k: v for k, v in zip(argnames[1:], args)},
            return_type,
            subroutine_decl=stmt,
        )

    setattr(wrapper, "subroutine_declaration", (name, stmt))
    return wrapper


def declare_extern(
    name: str,
    args: list[tuple[str, ast.ClassicalType] | OQPyArgument],
    return_type: Optional[ast.ClassicalType] = None,
    annotations: Sequence[str | tuple[str, str]] = (),
) -> Callable[..., OQFunctionCall]:
    """Declare an extern and return a callable which adds the extern.

    .. code-block:: python

        sqrt = declare_extern(
            "sqrt",
            [("x", classical_types.float32)],
            classical_types.float32,
        )
        var = FloatVar[32]()
        program.set(var, sqrt(0.5))

    """
    arg_names: list[str] = []
    arg_types: list[ast.ClassicalType] = []
    arg_access: list[ast.AccessControl | None] = []

    for arg in args:
        if isinstance(arg, tuple):
            arg_name, arg_type = arg
            access = None
        elif isinstance(arg, OQPyArgument):
            arg_name, arg_type, access = arg.unzip()
        else:
            raise Exception(f"Argument {arg} should have a proper type")
        arg_names.append(arg_name)
        arg_types.append(arg_type)
        arg_access.append(access)

    extern_decl = ast.ExternDeclaration(
        ast.Identifier(name),
        [
            ast.ExternArgument(type=ctype, access=access)
            for ctype, access in zip(arg_types, arg_access)
        ],
        return_type,
    )
    extern_decl.annotations = make_annotations(annotations)

    def call_extern(*call_args: AstConvertible, **call_kwargs: AstConvertible) -> OQFunctionCall:
        new_args = list(call_args) + [None] * len(call_kwargs)

        # Testing that the number of arguments is equal to what's defined by the prototype
        if len(new_args) != len(args):
            raise TypeError(
                f"{name}() takes {len(args)} positional arguments but {len(new_args)} were given."
            )

        # Adding keyword arguments to the list of arguments
        for k in call_kwargs:
            try:
                k_idx = arg_names.index(k)
            except ValueError:
                raise TypeError(f"{name}() got an unexpected keyword argument '{k}'.")

            if k_idx < len(call_args):
                raise TypeError(f"{name}() got multiple values for argument '{k}'.")

            if type(arg_types[k_idx]) == ast.DurationType:
                new_args[k_idx] = convert_float_to_duration(call_kwargs[k])
            else:
                new_args[k_idx] = call_kwargs[k]

        # Casting floats into durations for the non-keyword arguments
        for i, a in enumerate(call_args):
            if type(arg_types[i]) == ast.DurationType:
                new_args[i] = convert_float_to_duration(a)
        return OQFunctionCall(
            name, {k: v for k, v in zip(arg_names, new_args)}, return_type, extern_decl=extern_decl
        )

    return call_extern


def declare_waveform_generator(
    name: str,
    argtypes: list[tuple[str, ast.ClassicalType] | OQPyArgument],
    annotations: Sequence[str | tuple[str, str]] = (),
) -> Callable[..., OQFunctionCall]:
    """Create a function which generates waveforms using a specified name and argument signature."""
    func = declare_extern(name, argtypes, ast.WaveformType(), annotations=annotations)
    return func
