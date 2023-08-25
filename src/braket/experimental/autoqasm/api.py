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
from typing import Any, Callable, Dict, List, Optional, Tuple

import openqasm3.ast as qasm_ast
import oqpy.base

import braket.experimental.autoqasm.constants as aq_constants
import braket.experimental.autoqasm.instructions as aq_instructions
import braket.experimental.autoqasm.program as aq_program
import braket.experimental.autoqasm.transpiler as aq_transpiler
import braket.experimental.autoqasm.types as aq_types
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.autograph.core import converter
from braket.experimental.autoqasm.autograph.impl.api_core import (
    autograph_artifact,
    is_autograph_artifact,
)
from braket.experimental.autoqasm.autograph.tf_utils import tf_decorator


def main(*args, num_qubits: Optional[int] = None) -> Callable[[Any], aq_program.Program]:
    """Decorator that converts a function into a callable that returns
    a Program object containing the quantum program.

    The decorator re-converts the target function whenever the decorated
    function is called, and a new Program object is returned each time.

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
        #    @aq.main
        #    def my_func(...):
        # Equivalently, `main(my_func, num_qubits=None)`
        return _function_wrapper(args[0], _convert_main, wrapper_args={"user_config": user_config})
    else:
        # In this case, num_qubits was supplied, and we don't know `f` yet.
        # Matches the following syntax:
        #    @aq.main(num_qubits=x)
        #    def my_func(...):
        # Equivalently: `main(num_qubits=x)(my_func)`
        def _function_with_params(f: Callable) -> Callable[[Any], aq_program.Program]:
            return _function_wrapper(f, _convert_main, wrapper_args={"user_config": user_config})

        return _function_with_params


def subroutine(*args) -> Callable[[Any], aq_program.Program]:
    """Decorator that converts a function into a callable that will insert a subroutine into
    the quantum program.

    Returns:
        Callable[[Any], Program]: A callable which returns the converted
        quantum program when called.
    """
    return _function_wrapper(args[0], _convert_subroutine)


def gate(*args) -> Callable[[Any], None]:
    """Decorator that converts a function into a callable gate definition.

    Returns:
        Callable[[Any],]: A callable which can be used as a custom gate inside an
        aq.function or inside another aq.gate.
    """
    return _function_wrapper(args[0], _convert_gate)


def _function_wrapper(
    f: Callable,
    callback: Callable,
    wrapper_args: Optional[Dict[str, Any]] = None,
) -> Callable[[Any], aq_program.Program]:
    """Wrapping and conversion logic around the user function `f`.

    Args:
        f (Callable): The target function to be converted which represents
            the entry point of the quantum program.
        callback (Callable): TODO
        wrapper_args (Optional[Dict[str, Any]]): TODO

    Returns:
        Callable[[Any], Program]: A callable which returns the converted
        quantum program when called.
    """
    if is_autograph_artifact(f):
        return f

    if not wrapper_args:
        wrapper_args = {}

    def _decorator(f: Callable) -> Callable[[Any], None]:
        def _wrapper(*args, **kwargs) -> Callable:
            """Wrapper that calls the converted version of f."""
            options = converter.ConversionOptions(
                user_requested=True,
                optional_features=_autograph_optional_features(),
            )
            # Call the appropriate function converter
            return callback(f, options, args, kwargs, **wrapper_args)

        if inspect.isfunction(f) or inspect.ismethod(f):
            _wrapper = functools.update_wrapper(_wrapper, f)

        decorated_wrapper = tf_decorator.make_decorator(f, _wrapper)
        return autograph_artifact(decorated_wrapper)

    return autograph_artifact(_decorator(f))


def _autograph_optional_features() -> Tuple[converter.Feature]:
    # Exclude autograph features which are TensorFlow-specific
    return converter.Feature.all_but(
        (converter.Feature.NAME_SCOPES, converter.Feature.AUTO_CONTROL_DEPS)
    )


def _convert_main(
    f: Callable,
    options: converter.ConversionOptions,
    args: List[Any],
    kwargs: Dict[str, Any],
    user_config: aq_program.UserConfig,
) -> None:
    """Convert the initial callable `f` into a full AutoQASM program `program`.
    Puts the contents of `f` at the global level of the program, rather than
    putting it into a subroutine as done in `_convert_subroutine`.

    Some program pre- and post-processing occurs here, such as adding a qubit
    declaration and adding the subroutine invocation at the top level.

    Args:
        f (Callable): The function to be converted.
        options (converter.ConversionOptions): Converter options.
        args (List[Any]): Arguments passed to the program when called.
        kwargs (Dict[str, Any]): Keyword arguments passed to the program when called.
        user_config (UserConfig): User-specified settings that influence program building.
    """
    if aq_program.in_active_program_conversion_context():
        raise errors.AutoQasmTypeError(
            f"Cannot call main function '{f.__name__}' from another main function. Did you mean "
            "to use '@aq.subroutine'?"
        )

    with aq_program.build_program(user_config) as program_conversion_context:
        # Process the program
        aq_transpiler.converted_call(f, args, kwargs, options=options)

        # Modify program to add qubit declaration if necessary
        _add_qubit_declaration(program_conversion_context)

    return program_conversion_context.make_program()


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


def _convert_subroutine(
    f: Callable,
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
        options (converter.ConversionOptions): Converter options.
        args (List[Any]): Arguments passed to the program when called.
        kwargs (Dict[str, Any]): Keyword arguments passed to the program when called.
    """
    if not aq_program.in_active_program_conversion_context():
        raise errors.AutoQasmTypeError(
            "Subroutines shouldn't be called directly. Please define an entry point "
            "function, decorate it with '@aq.main', and call your subroutine "
            "from within that function."
        )

    with aq_program.build_program() as program_conversion_context:
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
            root_oqpy_program._add_subroutine(
                subroutine_name, subroutine_function_call.subroutine_decl
            )

    return program_conversion_context.return_variable


def _convert_gate(
    f: Callable,
    options: converter.ConversionOptions,
    args: List[Any],
    kwargs: Dict[str, Any],
) -> Callable:
    # We must be inside an active conversion context in order to invoke a gate
    program_conversion_context = aq_program.get_program_conversion_context()

    # Wrap the function into an oqpy gate definition
    wrapped_f, gate_args = _wrap_for_oqpy_gate(f, options)
    gate_name = f.__name__

    # Validate that the gate definition acts on at least one qubit
    if not gate_args.qubits:
        raise errors.ParameterTypeError(
            f'Gate definition "{gate_name}" has no arguments of type aq.Qubit. '
            "Every gate definition must contain at least one qubit argument."
        )

    # Process the gate definition
    with program_conversion_context.gate_definition(gate_name, gate_args):
        # TODO - enforce that nothing gets added to the program inside here except gates
        wrapped_f(gate_args._args)

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
    qubit_args = [args[i] for i in gate_args.qubit_indices]
    angle_args = [args[i] for i in gate_args.angle_indices]
    aq_instructions.instructions._qubit_instruction(gate_name, qubit_args, *angle_args)


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


def _clone_function(f_source: Callable) -> Callable:
    if not hasattr(f_source, "__code__"):
        raise ValueError(f"AutoQASM encountered a callable that it cannot process: {f_source}.")
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
) -> Tuple[Callable[..., None], aq_program.GateArgs]:
    gate_args = aq_program.GateArgs()
    sig = inspect.signature(f)
    for param in sig.parameters.values():
        if param.annotation is param.empty:
            raise errors.MissingParameterTypeError(
                f'Parameter "{param.name}" for gate "{f.__name__}" '
                "is missing a required type hint."
            )

        if param.annotation == aq_instructions.QubitIdentifierType:
            gate_args.append(param.name, True)
        elif param.annotation in [float, aq_types.FloatVar]:
            gate_args.append(param.name, False)
        else:
            raise errors.ParameterTypeError(
                f'Parameter "{param.name}" for gate "{f.__name__}" '
                "must have a type hint of either aq.Qubit or float."
            )

    def _func(*args: Any) -> None:
        aq_transpiler.converted_call(f, *args, kwargs={}, options=options)

    return _func, gate_args
