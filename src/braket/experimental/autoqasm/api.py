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

"""This module implements the decorator API for generating programs using AutoQASM."""

import copy
import functools
import inspect
from types import FunctionType
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import openqasm3.ast as qasm_ast
import oqpy.base

import braket.experimental.autoqasm.constants as aq_constants
import braket.experimental.autoqasm.instructions as aq_instructions
import braket.experimental.autoqasm.program as aq_program
import braket.experimental.autoqasm.transpiler as aq_transpiler
import braket.experimental.autoqasm.types as aq_types
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.autograph.core import ag_ctx, converter
from braket.experimental.autoqasm.autograph.impl.api_core import (
    autograph_artifact,
    is_autograph_artifact,
)
from braket.experimental.autoqasm.autograph.tf_utils import tf_decorator


def function(*args, num_qubits: Optional[int] = None) -> Callable[[Any], aq_program.Program]:
    """Decorator that converts a function into a callable that returns
    a Program object containing the quantum program.

    The decorator re-converts the target function whenever the decorated
    function is called, and a new Program object is returned.

    Args:
        num_qubits (Optional[int]): Configuration to set the total number of qubits to declare in
            the program.

    Returns:
        Callable[[Any], Program]: A callable which returns the converted
        quantum program when called.
    """
    # First, we just process the arguments to the decorator function
    user_config = aq_program.UserConfig(num_qubits=num_qubits)

    if len(args):
        # In this case, num_qubits wasn't supplied.
        # Matches the following syntax:
        #    @aq.function
        #    def my_func(...):
        # Equivalently, `function(my_func, num_qubits=None)`
        return _function_without_params(args[0], user_config=user_config)
    else:
        # In this case, num_qubits was supplied, and we don't know `f` yet.
        # Matches the following syntax:
        #    @aq.function(num_qubits=x)
        #    def my_func(...):
        # Equivalently: `function(num_qubits=x)(my_func)`
        def _function_with_params(f: Callable) -> Callable[[Any], aq_program.Program]:
            return _function_without_params(f, user_config=user_config)

        return _function_with_params


def gate(*args, declaration_only: bool = False) -> Callable[[Any], None]:
    """Decorator that converts a function into a callable gate definition.

    Args:
        declaration_only (bool): If declaration_only is True, the provided body of the
            gate definition is ignored, and only the gate signature is declared so that it can be
            called from elsewhere in the program. This may be used, for example, if the program
            is being combined with an external list of gate definitions. Defaults to False.

    Returns:
        Callable[[Any],]: A callable which can be used as a custom gate inside an
        aq.function or inside another aq.gate.
    """
    if not args:
        # In this case, declaration_only was supplied, and we don't know `f` yet.
        # Matches the following syntax:
        #    @aq.gate(declaration_only=True)
        #    def my_func(...):
        # Equivalently: `gate(declaration_only=True)(my_func)`
        def _gate_with_params(*args) -> Callable[[Any], None]:
            return gate(*args, declaration_only=declaration_only)

        return _gate_with_params

    f = args[0]
    if is_autograph_artifact(f):
        return f

    wrapper_factory = _convert_gate_wrapper(declaration_only)
    wrapper = wrapper_factory(f)

    return autograph_artifact(wrapper)


def _function_without_params(
    f: Callable, user_config: aq_program.UserConfig
) -> Callable[[Any], aq_program.Program]:
    """Wrapping and conversion logic around the user function `f`.

    Args:
        f (Callable): The target function to be converted which represents
            the entry point of the quantum program.
        user_config (UserConfig): User-specified settings that influence program building

    Returns:
        Callable[[Any], Program]: A callable which returns the converted
        quantum program when called.
    """
    if is_autograph_artifact(f):
        return f

    wrapper_factory = _convert_program_wrapper(
        user_config=user_config,
        recursive=False,
    )
    wrapper = wrapper_factory(f)

    return autograph_artifact(wrapper)


def _convert_program_wrapper(
    user_config: aq_program.UserConfig,
    recursive: bool = False,
    user_requested: bool = True,
    conversion_ctx: Optional[ag_ctx.ControlStatusCtx] = ag_ctx.NullCtx(),
) -> Callable:
    """Generates a factory which does the conversion of a function into a callable
    that returns a Program object containing the quantum program.

    Args:
        user_config (UserConfig): User-specified settings that influence program building
        recursive (bool): whether to recursively convert any functions or classes
            that the converted function may use. Defaults to False.
        user_requested (bool): whether this is a function that the user explicitly
            asked to be converted. See ConversionOptions.user_requested. Defaults to True.
        conversion_ctx (Optional[ControlStatusCtx]): the Autograph context in
            which `f` is used. Defaults to ag_ctx.NullCtx().

    Returns:
        Callable: a decorator that converts the given function into an equivalent
        function that uses AutoQASM operations.
    """

    def _decorator(f: Callable) -> Callable[[Any], aq_program.Program]:
        """aq.function decorator implementation."""

        def _wrapper(*args, **kwargs) -> Union[aq_program.Program, Optional[oqpy.base.Var]]:
            """Wrapper that calls the converted version of f."""
            # This code is executed once the decorated function is called
            if aq_program.in_active_program_conversion_context():
                _validate_subroutine_args(user_config)
            options = converter.ConversionOptions(
                recursive=recursive,
                user_requested=user_requested,
                optional_features=_autograph_optional_features(),
            )
            return _convert_program(f, conversion_ctx, options, user_config, args, kwargs)

        if inspect.isfunction(f) or inspect.ismethod(f):
            _wrapper = functools.update_wrapper(_wrapper, f)

        decorated_wrapper = tf_decorator.make_decorator(f, _wrapper)
        return autograph_artifact(decorated_wrapper)

    return _decorator


def _convert_gate_wrapper(declaration_only: bool) -> Callable:
    def _decorator(f: Callable) -> Callable[[Any], None]:
        """aq.gate decorator implementation."""

        def _wrapper(*args, **kwargs) -> Callable:
            """Wrapper that calls the converted version of f."""
            options = converter.ConversionOptions(
                optional_features=_autograph_optional_features(),
            )
            return _convert_gate(f, declaration_only, options, args, kwargs)

        if inspect.isfunction(f) or inspect.ismethod(f):
            _wrapper = functools.update_wrapper(_wrapper, f)

        decorated_wrapper = tf_decorator.make_decorator(f, _wrapper)
        return autograph_artifact(decorated_wrapper)

    return _decorator


def _validate_subroutine_args(user_config: aq_program.UserConfig) -> None:
    """Validate decorator arguments to subroutines.

    Args:
        user_config (UserConfig): User-specified settings that influence program building

    Raises:
        InconsistentUserConfiguration: If subroutine num_qubits does not match the main
            function's num_qubits argument.
    """
    if user_config.num_qubits is None:
        return
    # Allow num_qubits only if the arg matches the value provided to the main function
    if user_config.num_qubits != aq_program.get_program_conversion_context().get_declared_qubits():
        raise errors.InconsistentNumQubits()


def _autograph_optional_features() -> Tuple[converter.Feature]:
    # Exclude autograph features which are TensorFlow-specific
    return converter.Feature.all_but(
        (converter.Feature.NAME_SCOPES, converter.Feature.AUTO_CONTROL_DEPS)
    )


def _convert_program(
    f: Callable,
    conversion_ctx: ag_ctx.ControlStatusCtx,
    options: converter.ConversionOptions,
    user_config: aq_program.UserConfig,
    args: List[Any],
    kwargs: Dict[str, Any],
) -> Union[aq_program.Program, Optional[oqpy.base.Var]]:
    """Convert the initial callable `f` into a full AutoQASM program `program`.

    This function adds error handling around `_convert_program_as_subroutine`
    and `_convert_program_as_main`, where the conversion logic itself lives.

    Args:
        f (Callable): The function to be converted.
        conversion_ctx (ControlStatusCtx): the Autograph context in which `f` is used.
        options (converter.ConversionOptions): Converter options.
        user_config (UserConfig): User-specified settings that influence program building
        args (List[Any]): Arguments passed to the program when called.
        kwargs (Dict[str, Any]): Keyword arguments passed to the program when called.

    Returns:
        Union[Program, Optional[Var]]: The converted program, if this is a top-level call
        to the conversion process. Or, the oqpy variable returned from the converted function,
        if this is a subroutine conversion.
    """
    # We will convert this function as a subroutine if we are already inside an
    # existing conversion process (i.e., this is a subroutine call).
    convert_as_subroutine = aq_program.in_active_program_conversion_context()

    with aq_program.build_program(user_config) as program_conversion_context:
        try:
            with conversion_ctx:
                if convert_as_subroutine:
                    _convert_program_as_subroutine(
                        f, program_conversion_context, options, args, kwargs
                    )
                else:
                    _convert_program_as_main(f, program_conversion_context, options, args, kwargs)
        except Exception as e:
            if isinstance(e, errors.AutoQasmError):
                raise
            elif hasattr(e, "ag_error_metadata"):
                raise e.ag_error_metadata.to_exception(e)
            else:
                raise

    if convert_as_subroutine:
        return program_conversion_context.return_variable

    return program_conversion_context.make_program()


def _convert_program_as_main(
    f: Callable,
    program_conversion_context: aq_program.ProgramConversionContext,
    options: converter.ConversionOptions,
    args: List[Any],
    kwargs: Dict[str, Any],
) -> None:
    """Convert the initial callable `f` into a full AutoQASM program `program`.
    Puts the contents of `f` at the global level of the program, rather than
    putting it into a subroutine as done in `_convert_program_as_subroutine`.

    Some program pre- and post-processing occurs here, such as adding a qubit
    declaration and adding the subroutine invocation at the top level.

    Args:
        f (Callable): The function to be converted.
        program_conversion_context (ProgramConversionContext): The program being converted.
        options (converter.ConversionOptions): Converter options.
        args (List[Any]): Arguments passed to the program when called.
        kwargs (Dict[str, Any]): Keyword arguments passed to the program when called.
    """
    # Process the program
    aq_transpiler.converted_call(f, args, kwargs, options=options)

    # Modify program to add qubit declaration if necessary
    _add_qubit_declaration(program_conversion_context)


def _convert_program_as_subroutine(
    f: Callable,
    program_conversion_context: aq_program.ProgramConversionContext,
    options: converter.ConversionOptions,
    args: List[Any],
    kwargs: Dict[str, Any],
) -> None:
    """Convert the initial callable `f` into a full AutoQASM program `program`.
    The contents of `f` are converted into a subroutine in the program.

    Some program pre- and post-processing occurs here, such as adding a qubit
    declaration and adding the subroutine invocation at the top level.

    Args:
        f (Callable): The function to be converted.
        program_conversion_context (ProgramConversionContext): The program being converted.
        options (converter.ConversionOptions): Converter options.
        args (List[Any]): Arguments passed to the program when called.
        kwargs (Dict[str, Any]): Keyword arguments passed to the program when called.
    """
    oqpy_program = program_conversion_context.get_oqpy_program()

    if f not in program_conversion_context.subroutines_processing:
        # Mark that we are starting to process this function to short-circuit recursion
        program_conversion_context.subroutines_processing.add(f)

        # Convert the function via autograph into an oqpy subroutine
        # NOTE: Process a clone of the function so that we don't modify the original object
        oqpy_sub = oqpy.subroutine(_wrap_for_oqpy_subroutine(_clone_function(f), options))

        # Process the program
        subroutine_function_call = oqpy_sub(oqpy_program, *args, **kwargs)

        # Mark that we are finished processing this function
        program_conversion_context.subroutines_processing.remove(f)
    else:
        # Convert the function via autograph into an oqpy subroutine
        # NOTE: Recursive call; process a dummy version of the function instead
        oqpy_sub = oqpy.subroutine(_wrap_for_oqpy_subroutine(_dummy_function(f), options))

        # Process the program
        subroutine_function_call = oqpy_sub(oqpy_program, *args, **kwargs)

    # Add the subroutine invocation to the program
    ret_type = subroutine_function_call.subroutine_decl.return_type
    return_instance = _make_return_instance_from_oqpy_return_type(ret_type)
    return_variable = None
    if isinstance(return_instance, list):
        return_variable = aq_types.ArrayVar(
            return_instance,
            dimensions=[d.value for d in ret_type.dimensions],
        )
        oqpy_program.set(return_variable, subroutine_function_call)
    elif return_instance is not None:
        return_variable = aq_types.wrap_value(return_instance)
        oqpy_program.declare(return_variable)
        oqpy_program.set(return_variable, subroutine_function_call)
    else:
        function_call = subroutine_function_call.to_ast(oqpy_program)
        oqpy_program._add_statement(qasm_ast.ExpressionStatement(function_call))

    # Store the return variable in the program conversion context
    program_conversion_context.return_variable = return_variable

    # Add the subroutine definition to the root-level program if necessary
    root_oqpy_program = program_conversion_context.oqpy_program_stack[0]
    subroutine_name = subroutine_function_call.identifier.name
    if (
        subroutine_name not in root_oqpy_program.subroutines
        and subroutine_function_call.subroutine_decl is not None
    ):
        root_oqpy_program._add_subroutine(subroutine_name, subroutine_function_call.subroutine_decl)


def _convert_gate(
    f: Callable,
    declaration_only: bool,
    options: converter.ConversionOptions,
    args: List[Any],
    kwargs: Dict[str, Any],
) -> Callable:
    try:
        # We must be inside an active conversion context in order to invoke a gate
        program_conversion_context = aq_program.get_program_conversion_context()

        # Wrap the function into an oqpy gate definition
        wrapped_f, gate_args = _wrap_for_oqpy_gate(f, options)
        gate_name = f.__name__

        # Validate that the gate definition acts on at least one qubit
        qubits = [
            oqpy.Qubit(name, needs_declaration=False) for name, is_qubit in gate_args if is_qubit
        ]
        if not qubits:
            raise errors.ParameterTypeError(
                f'Gate definition "{gate_name}" has no arguments of type aq.Qubit. '
                "Every gate definition must contain at least one qubit argument."
            )

        if not declaration_only:
            # Process the gate definition
            angles = [oqpy.AngleVar(name=name) for name, is_qubit in gate_args if not is_qubit]
            with program_conversion_context.gate_definition(gate_name, qubits, angles):
                # TODO - enforce that nothing gets added to the program inside here except gates
                wrapped_f(qubits, *angles)

            # Add the gate definition to the root-level program if necessary
            root_oqpy_program = program_conversion_context.oqpy_program_stack[0]
            if gate_name not in root_oqpy_program.gates:
                gate_stmt = program_conversion_context.get_oqpy_program().gates[gate_name]
                root_oqpy_program._add_gate(gate_name, gate_stmt)

        # Add the gate invocation to the program
        if len(args) != len(gate_args):
            raise errors.ParameterTypeError(
                f'Incorrect number of arguments passed to gate "{gate_name}". '
                f"Expected {len(gate_args)}, got {len(args)}."
            )
        qubit_args = [args[i] for i, (_, is_qubit) in enumerate(gate_args) if is_qubit]
        angle_args = [args[i] for i, (_, is_qubit) in enumerate(gate_args) if not is_qubit]
        aq_instructions.instructions._qubit_instruction(gate_name, qubit_args, *angle_args)
    except Exception as e:
        if isinstance(e, errors.AutoQasmError):
            raise
        elif hasattr(e, "ag_error_metadata"):
            raise e.ag_error_metadata.to_exception(e)
        else:
            raise


def _make_return_instance_from_oqpy_return_type(return_type: Any) -> Any:
    if not return_type:
        return None

    return_type = aq_types.conversions.var_type_from_ast_type(return_type)
    if return_type == aq_types.ArrayVar:
        return []
    return return_type()


def _make_return_instance_from_f_annotation(f: Callable) -> Any:
    # TODO: Recursive functions should work even if the user's type hint is wrong
    annotations = f.__annotations__
    return_type = annotations["return"] if "return" in annotations else None

    return_instance = None
    if return_type and aq_types.is_qasm_type(return_type):
        return_instance = return_type()
    elif return_type:
        if hasattr(return_type, "__origin__"):
            # Types from python's typing module, such as `List`. origin gives us `list``
            return_instance = return_type.__origin__()
        else:
            return_instance = return_type()

    return return_instance


def _add_qubit_declaration(program_conversion_context: aq_program.ProgramConversionContext) -> None:
    """Modify the program to include a global qubit register declaration.

    The number of qubits declared is pulled from either the user config (supplied explicitly
    via kwargs when calling the program) or an attempt is made to dynamically determine the total
    number of qubits used by inspecting the program.

    Args:
        program_conversion_context (ProgramConversionContext): The program conversion context.
    """
    root_oqpy_program = program_conversion_context.oqpy_program_stack[0]

    # Declare the global qubit register if necessary
    user_specified_num_qubits = program_conversion_context.get_declared_qubits()

    if user_specified_num_qubits is not None:
        # User-supplied qubit count
        root_oqpy_program.declare(
            [oqpy.QubitArray(aq_constants.QUBIT_REGISTER, user_specified_num_qubits)],
            to_beginning=True,
        )

    else:
        # Qubit count from program inspection
        qubits = program_conversion_context.qubits
        max_qubit_index = qubits[-1] if len(qubits) else None
        if max_qubit_index is not None:
            root_oqpy_program.declare(
                [oqpy.QubitArray(aq_constants.QUBIT_REGISTER, max_qubit_index + 1)],
                to_beginning=True,
            )


def _clone_function(f_source: Callable) -> Callable:
    f_clone = FunctionType(
        copy.deepcopy(f_source.__code__),
        copy.copy(f_source.__globals__),
        copy.deepcopy(f_source.__name__),
        copy.deepcopy(f_source.__defaults__),
        copy.copy(f_source.__closure__),
    )
    setattr(f_clone, "__signature__", copy.deepcopy(inspect.signature(f_source)))
    setattr(f_clone, "__annotations__", copy.deepcopy(f_source.__annotations__))
    return f_clone


def _dummy_function(f_source: Callable) -> Callable:
    return_instance = _make_return_instance_from_f_annotation(f_source)

    def f_dummy(*args, **kwargs) -> Any:
        return return_instance  # pragma: no cover

    f_dummy.__name__ = copy.deepcopy(f_source.__name__)
    f_dummy.__defaults__ = copy.deepcopy(f_source.__defaults__)
    setattr(f_dummy, "__signature__", copy.deepcopy(inspect.signature(f_source)))
    setattr(f_dummy, "__annotations__", copy.deepcopy(f_source.__annotations__))
    return f_dummy


def _wrap_for_oqpy_subroutine(f: Callable, options: converter.ConversionOptions) -> Callable:
    """Wraps the given function into a callable expected by oqpy.subroutine.

    oqpy.subroutine requires that the first argument be of type `oqpy.Program`,
    which represents the nested Program object which will be built up while
    executing the subroutine.

    Args:
        f (Callable): The function to be wrapped.
        options (converter.ConversionOptions): Converter options.

    Returns:
        Callable: The modified function for use with oqpy.subroutine.
    """

    @functools.wraps(f)
    def _func(*args, **kwargs) -> Any:
        inner_program: oqpy.Program = args[0]
        with aq_program.get_program_conversion_context().push_oqpy_program(inner_program):
            result = aq_transpiler.converted_call(f, args[1:], kwargs, options=options)
        inner_program.autodeclare()
        return result

    # Replace the function signature with a new signature where the first
    # argument is of type `oqpy.Program`.
    sig = inspect.signature(_func)
    first_param = inspect.Parameter(
        name="inner_program",
        kind=inspect._ParameterKind.POSITIONAL_OR_KEYWORD,
        annotation=oqpy.Program,
    )
    _func.__annotations__[first_param.name] = first_param.annotation

    new_params = [first_param]
    for param in sig.parameters.values():
        if param.annotation is param.empty:
            raise errors.MissingParameterTypeError(
                f'Parameter "{param.name}" for subroutine "{_func.__name__}" '
                "is missing a required type hint."
            )

        new_param = inspect.Parameter(
            name=param.name, kind=param.kind, annotation=aq_types.map_type(param.annotation)
        )
        new_params.append(new_param)
        _func.__annotations__[new_param.name] = new_param.annotation

    _func.__signature__ = sig.replace(parameters=new_params)
    return _func


def _wrap_for_oqpy_gate(
    f: Callable,
    options: converter.ConversionOptions,
) -> Tuple[Callable[[List[oqpy.Qubit], Any], None], List[Tuple[str, bool]]]:
    gate_args = []
    sig = inspect.signature(f)
    for param in sig.parameters.values():
        if param.annotation is param.empty:
            raise errors.MissingParameterTypeError(
                f'Parameter "{param.name}" for gate "{f.__name__}" '
                "is missing a required type hint."
            )

        if param.annotation == aq_instructions.QubitIdentifierType:
            gate_args.append((param.name, True))
        elif param.annotation in [float, aq_types.FloatVar]:
            gate_args.append((param.name, False))
        else:
            raise errors.ParameterTypeError(
                f'Parameter "{param.name}" for gate "{f.__name__}" '
                "must have a type hint of either aq.Qubit or float."
            )

    def _func(qubits: List[oqpy.Qubit], *args: Any) -> None:
        qubits = qubits.copy()
        angles = list(args).copy() if args else []
        f_args = []
        for _, is_qubit in gate_args:
            f_args.append(qubits.pop(0) if is_qubit else angles.pop(0))
        aq_transpiler.converted_call(f, f_args, kwargs={}, options=options)

    return _func, gate_args
