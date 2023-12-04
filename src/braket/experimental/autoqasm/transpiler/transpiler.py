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

"""The PyToOqpy transpiler.

TODO @shaffry: this file is mostly copied from the class PyToTF
in the TensorFlow implementation of autograph. Consider refactoring
to reduce duplication if possible.
"""

import functools
import importlib
import inspect
from collections.abc import Callable
from typing import Any, Optional, Union

import gast
from autograph.converters import (
    asserts,
    call_trees,
    conditional_expressions,
    continue_statements,
    control_flow,
    directives,
    functions,
    lists,
    logical_expressions,
    slices,
    variables,
)
from autograph.core import ag_ctx, converter, function_wrappers, unsupported_features_checker
from autograph.impl.api_core import (
    StackTraceMapper,
    _attach_error_metadata,
    _log_callargs,
    is_autograph_artifact,
)
from autograph.logging import ag_logging as logging
from autograph.pyct import anno, cfg, qual_names, transpiler
from autograph.pyct.static_analysis import activity, reaching_definitions
from autograph.tf_utils import tf_stack

from braket.experimental.autoqasm import operators, program, types
from braket.experimental.autoqasm.converters import (
    assignments,
    break_statements,
    comparisons,
    return_statements,
)


class PyToOqpy(transpiler.PyToPy):
    """The AutoQASM transpiler which converts a Python function into an oqpy program."""

    def __init__(self):
        super(PyToOqpy, self).__init__()
        self._extra_locals = None

    def get_transformed_name(self, node: Union[gast.Lambda, gast.FunctionDef]) -> str:
        return "oq__" + super(PyToOqpy, self).get_transformed_name(node)

    def get_extra_locals(self) -> dict:
        """Returns extra static local variables to be made to transformed code.

        Returns:
            dict: Additional variables to make available to the transformed code.
        """
        if self._extra_locals is None:
            module_spec = importlib.machinery.ModuleSpec("autograph", None)
            ag_internal = importlib.util.module_from_spec(module_spec)
            ag_internal.__dict__.update(inspect.getmodule(PyToOqpy).__dict__)
            ag_internal.ConversionOptions = converter.ConversionOptions
            ag_internal.STD = converter.STANDARD_OPTIONS
            ag_internal.Feature = converter.Feature
            ag_internal.program = program
            ag_internal.FunctionScope = function_wrappers.FunctionScope
            ag_internal.with_function_scope = function_wrappers.with_function_scope
            # We don't want to create a submodule because we want the operators to be
            # accessible as ag__.<operator>
            ag_internal.__dict__.update(operators.__dict__)

            self._extra_locals = {"ag__": ag_internal}
        return self._extra_locals

    def get_caching_key(self, ctx: ag_ctx.ControlStatusCtx) -> converter.ConversionOptions:
        return ctx.options

    def _initial_analysis(
        self, node: Union[gast.Lambda, gast.FunctionDef], ctx: ag_ctx.ControlStatusCtx
    ) -> Union[gast.Lambda, gast.FunctionDef]:
        graphs = cfg.build(node)
        node = qual_names.resolve(node)
        node = activity.resolve(node, ctx, None)
        node = reaching_definitions.resolve(node, ctx, graphs)
        anno.dup(
            node,
            {
                anno.Static.DEFINITIONS: anno.Static.ORIG_DEFINITIONS,
            },
        )
        return node

    def transform_ast(
        self, node: Union[gast.Lambda, gast.FunctionDef], ctx: ag_ctx.ControlStatusCtx
    ) -> Union[gast.Lambda, gast.FunctionDef]:
        """Performs an actual transformation of a function's AST.

        Args:
            node (Union[Lambda, FunctionDef]): One or more ast.AST nodes
                representing the AST to be transformed.
            ctx (ControlStatusCtx): transformer context.

        Returns:
            Union[Lambda, FunctionDef]: The root of the transformed AST.
        """
        unsupported_features_checker.verify(node)
        node = self._initial_analysis(node, ctx)

        # autograph converters
        node = functions.transform(node, ctx)
        node = directives.transform(node, ctx)
        node = break_statements.transform(node, ctx)
        node = asserts.transform(node, ctx)
        # Note: sequencing continue canonicalization before for loop one avoids
        # dealing with the extra loop increment operation that the for
        # canonicalization creates.
        node = continue_statements.transform(node, ctx)
        node = return_statements.transform(node, ctx)
        node = assignments.transform(node, ctx)
        node = lists.transform(node, ctx)
        node = slices.transform(node, ctx)
        node = call_trees.transform(node, ctx)
        node = control_flow.transform(node, ctx)
        node = conditional_expressions.transform(node, ctx)
        node = comparisons.transform(node, ctx)
        node = logical_expressions.transform(node, ctx)
        node = variables.transform(node, ctx)

        return node


def _convert_actual(entity: Callable, program_ctx: Optional[ag_ctx.ControlStatusCtx]) -> Callable:
    """Applies AutoGraph to entity."""
    if not hasattr(entity, "__code__"):
        raise ValueError(
            "Cannot apply autograph to a function that doesn't "
            "expose a __code__ object. If this is a @tf.function,"
            " try passing f.python_function instead."
        )

    transformed, module, source_map = _TRANSPILER.transform(entity, program_ctx)

    assert not hasattr(transformed, "ag_module")
    assert not hasattr(transformed, "ag_source_map")
    transformed.ag_module = module
    transformed.ag_source_map = source_map
    return transformed


#
# Generated code support
#


def converted_call(
    f: Callable,
    args: tuple,
    kwargs: Optional[dict],
    caller_fn_scope: Optional[function_wrappers.FunctionScope] = None,
    options: Optional[converter.ConversionOptions] = None,
) -> Any:
    """Converts a function call inline.

    For internal use only.

    Note: The argument list is optimized for readability of generated code, which
    may look like this:

        `ag__.converted_call(f, (arg1, arg2), None, fscope)`
        `ag__.converted_call(f, (), dict(arg1=val1, **kwargs), fscope)`
        `ag__.converted_call(f, (arg1, arg2) + varargs, dict(**kwargs), lscope)`

    Args:
        f (Callable): The function to convert.
        args (tuple): the original positional arguments of f.
        kwargs (Optional[dict]): the original keyword arguments of f.
        caller_fn_scope (Optional[FunctionScope]): the function scope of the converted
            function in which this call was originally made. Defaults to None.
        options (Optional[ConversionOptions]): conversion options. If not
            specified, the value of caller_fn_scope.callopts is used. Either options
            or caller_fn_scope must be present. Defaults to None.

    Returns:
        Any: the result of executing a possibly-converted `f` with the given arguments.
    """
    logging.log(1, "Converted call: %s\n    args: %s\n    kwargs: %s\n", f, args, kwargs)

    assert options is not None or caller_fn_scope is not None
    options = options or caller_fn_scope.callopts

    if ag_ctx.control_status_ctx().status == ag_ctx.Status.DISABLED:
        logging.log(2, "Allowlisted: %s: AutoGraph is disabled in context", f)
        return _call_unconverted(f, args, kwargs, options, False)

    if is_autograph_artifact(f):
        logging.log(2, "Permanently allowed: %s: AutoGraph artifact", f)
        return _call_unconverted(f, args, kwargs, options)

    # If this is a partial, unwrap it and redo all the checks.
    if isinstance(f, functools.partial):
        return _converted_partial(f, args, kwargs, caller_fn_scope, options)

    # internal_convert_user_code is for example turned off when issuing a dynamic
    # call conversion from generated code while in nonrecursive mode. In that
    # case we evidently don't want to recurse, but we still have to convert
    # things like builtins.
    if not options.internal_convert_user_code:
        return _call_unconverted(f, args, kwargs, options)

    target_entity, effective_args = _inspect_callable(f, args)
    converted_f, exc = _try_convert_actual(target_entity, effective_args, kwargs, options)
    if exc:
        raise exc

    with StackTraceMapper(converted_f), tf_stack.CurrentModuleFilter():
        try:
            effective_kwargs = kwargs or {}
            result = converted_f(*effective_args, **effective_kwargs)
        except Exception as e:
            _attach_error_metadata(e, converted_f)
            raise

    return types.wrap_value(result)


def _converted_partial(
    f: Callable,
    args: tuple,
    kwargs: Optional[dict],
    caller_fn_scope: Optional[function_wrappers.FunctionScope] = None,
    options: Optional[converter.ConversionOptions] = None,
) -> Any:
    # Use copy to avoid mutating the underlying keywords.
    new_kwargs = f.keywords.copy()
    new_kwargs.update(kwargs)
    new_args = f.args + args
    logging.log(3, "Forwarding call of partial %s with\n%s\n%s\n", f, new_args, new_kwargs)
    return converted_call(
        f.func, new_args, new_kwargs, caller_fn_scope=caller_fn_scope, options=options
    )


def _inspect_callable(f: Callable, args: tuple) -> tuple[Callable, tuple]:
    target_entity = None
    effective_args = None

    if inspect.ismethod(f) or inspect.isfunction(f):
        target_entity = f
        effective_args = args

        f_self = getattr(f, "__self__", None)
        if f_self is not None:
            effective_args = (f_self,) + effective_args

    return target_entity, effective_args


def _try_convert_actual(
    target_entity: Callable,
    effective_args: tuple,
    kwargs: dict,
    options: converter.ConversionOptions,
) -> tuple[Callable, Optional[Exception]]:
    converted_f = None
    exc = None
    try:
        program_ctx = converter.ProgramContext(options=options)
        converted_f = _convert_actual(target_entity, program_ctx)
        if logging.has_verbosity(2):
            _log_callargs(converted_f, effective_args, kwargs)
    except Exception as e:
        logging.log(1, "Error transforming entity %s", target_entity, exc_info=True)
        exc = e
    return converted_f, exc


def _call_unconverted(
    f: Callable,
    args: tuple,
    kwargs: dict,
    options: converter.ConversionOptions,
    update_cache: bool = True,
) -> Any:
    """Calls the original function without converting with AutoGraph."""
    if kwargs is not None:
        return f(*args, **kwargs)
    return f(*args)


_TRANSPILER = PyToOqpy()
