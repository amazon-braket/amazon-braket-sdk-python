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

from __future__ import annotations

import copy
import functools
import inspect
from collections.abc import Callable
from types import FunctionType
from typing import Any, Optional, Union, get_args

import openqasm3.ast as qasm_ast
import oqpy.base
from autograph.core import converter
from autograph.impl.api import autograph_artifact, is_autograph_artifact

import braket.experimental.autoqasm.constants as aq_constants
import braket.experimental.autoqasm.instructions as aq_instructions
import braket.experimental.autoqasm.program as aq_program
import braket.experimental.autoqasm.transpiler as aq_transpiler
import braket.experimental.autoqasm.types as aq_types
from braket.aws import AwsDevice
from braket.devices.device import Device
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.instructions.qubits import QubitIdentifierType as Qubit
from braket.experimental.autoqasm.instructions.qubits import is_qubit_identifier_type
from braket.experimental.autoqasm.program.gate_calibrations import GateCalibration


def main(
    func: Optional[Callable] = None,
    *,
    num_qubits: Optional[int] = None,
    device: Optional[Union[Device, str]] = None,
) -> Callable[..., aq_program.Program]:
    """Decorator that converts a function into a callable that returns
    a Program object containing the quantum program.

    The decorator re-converts the target function whenever the decorated
    function is called, and a new Program object is returned each time.

    Args:
        func (Optional[Callable]): Decorated function. May be `None` in the case where decorator
            is used with parentheses.
        num_qubits (Optional[int]): Configuration to set the total number of qubits to declare in
            the program.
        device (Optional[Union[Device, str]]): Configuration to set the target device for the
            program. Can be either an Device object or a valid Amazon Braket device ARN.

    Returns:
        Callable[..., Program]: A callable which returns the converted
        quantum program when called.
    """
    if isinstance(device, str):
        device = AwsDevice(device)

    return _function_wrapper(
        func,
        converter_callback=_convert_main,
        converter_args={
            "user_config": aq_program.UserConfig(
                num_qubits=num_qubits,
                device=device,
            )
        },
    )


def subroutine(func: Optional[Callable] = None) -> Callable[..., aq_program.Program]:
    """Decorator that converts a function into a callable that will insert a subroutine into
    the quantum program.

    Args:
        func (Optional[Callable]): Decorated function. May be `None` in the case where decorator
            is used with parentheses.

    Returns:
        Callable[..., Program]: A callable which returns the converted
        quantum program when called.
    """
    return _function_wrapper(func, converter_callback=_convert_subroutine)


def gate(func: Optional[Callable] = None) -> Callable[..., None]:
    """Decorator that converts a function into a callable gate definition.

    Args:
        func (Optional[Callable]): Decorated function. May be `None` in the case where decorator
            is used with parentheses.

    Returns:
        Callable[..., None]: A callable which can be used as a custom gate inside an
        aq.function or inside another aq.gate.
    """
    return _function_wrapper(func, converter_callback=_convert_gate)


def gate_calibration(*, implements: Callable, **kwargs) -> Callable[[], GateCalibration]:
    """A decorator that register the decorated function as a gate calibration definition. The
    decorated function is added to a main program using `with_calibrations` method of the main
    program. The fixed values of qubits or angles that the calibration is implemented against
    are supplied as kwargs. The name of the kwargs must match the args of the gate function it
    implements.

    Args:
        implements (Callable): Gate function.

    Returns:
        Callable[[], GateCalibration]: A callable to be added to a main program using
        `with_calibrations` method of the main program.
    """
    return _function_wrapper(
        None,
        converter_callback=_convert_calibration,
        converter_args={"gate_function": implements, **kwargs},
    )


def _function_wrapper(
    func: Optional[Callable],
    *,
    converter_callback: Callable,
    converter_args: Optional[dict[str, Any]] = None,
) -> Callable[..., Optional[Union[aq_program.Program, GateCalibration]]]:
    """Wrapping and conversion logic around the user function `f`.

    Args:
        func (Optional[Callable]): Decorated function. May be `None` in the case where decorator
            is used with parentheses.
        converter_callback (Callable): The function converter, e.g., _convert_main.
        converter_args (Optional[dict[str, Any]]): Extra arguments for the function converter.

    Returns:
        Callable[..., Optional[Union[Program, GateCalibration]]]: A callable which
        returns the converted construct, if any, when called.
    """
    if not (func and callable(func)):
        # This the case where a decorator is called either without a positional argument,
        # or with a non-callable positional argument, which is as close of an approximation
        # we can get to the case where a decorator is called with parentheses.
        #
        # There is still a false negative case, where we have something like:
        #     @aq.main(callable_pos_arg)
        #     def my_function():
        #
        # but this is known limitation in python (consider the valid non-decorator usage
        # `aq.main(my_function)` for an example of why this ambiguity exists).
        #
        # To make this work, here we simply return a partial application of this function
        # which still expects a Callable as the single positional argument.
        return functools.partial(
            _function_wrapper, converter_callback=converter_callback, converter_args=converter_args
        )

    if is_autograph_artifact(func):
        return func

    if not converter_args:
        converter_args = {}

    def _wrapper(*args, **kwargs) -> Callable:
        """Wrapper that calls the converted version of f."""
        options = converter.ConversionOptions(
            user_requested=True,
            optional_features=_autograph_optional_features(),
        )
        # Call the appropriate function converter
        return converter_callback(func, options, args, kwargs, **converter_args)

    if inspect.isfunction(func) or inspect.ismethod(func):
        _wrapper = functools.update_wrapper(_wrapper, func)

    return autograph_artifact(_wrapper)


def _autograph_optional_features() -> tuple[converter.Feature]:
    # Exclude autograph features which are TensorFlow-specific
    return converter.Feature.all_but(
        (converter.Feature.NAME_SCOPES, converter.Feature.AUTO_CONTROL_DEPS)
    )


def _convert_main(
    f: Callable,
    options: converter.ConversionOptions,
    args: tuple[Any],
    kwargs: dict[str, Any],
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
        args (tuple[Any]): Arguments passed to the program when called.
        kwargs (dict[str, Any]): Keyword arguments passed to the program when called.
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

        # Modify program to add global declarations if necessary
        _add_qubit_declaration(program_conversion_context)
        program_conversion_context.add_io_declarations()

    return program_conversion_context.make_program()


def _add_qubit_declaration(program_conversion_context: aq_program.ProgramConversionContext) -> None:
    """Modify the program to include a global qubit register declaration.

    The number of qubits declared is pulled from either the user config (supplied explicitly
    via kwargs when calling the program) or an attempt is made to dynamically determine the total
    number of qubits used by inspecting the program.

    Args:
        program_conversion_context (ProgramConversionContext): The program conversion context.
    """
    num_qubits = None

    # User-supplied qubit count
    user_specified_num_qubits = program_conversion_context.get_declared_qubits()
    if user_specified_num_qubits is not None:
        num_qubits = user_specified_num_qubits

    # Qubit count from program inspection
    if num_qubits is None:
        qubits = program_conversion_context.qubits
        max_qubit_index = qubits[-1] if len(qubits) else None
        if max_qubit_index is not None:
            num_qubits = max_qubit_index + 1

    # Early return if we are not going to declare any qubits
    if num_qubits is None:
        return

    # Validate that the target device has enough qubits
    device = program_conversion_context.get_target_device()
    if device and num_qubits > device.properties.paradigm.qubitCount:
        raise errors.InsufficientQubitCountError(
            f'Program requires {num_qubits} qubits, but target device "{device.name}" has '
            f"only {device.properties.paradigm.qubitCount} qubits."
        )

    # Declare the global qubit register
    root_oqpy_program = program_conversion_context.get_oqpy_program(
        scope=aq_program.ProgramScope.MAIN
    )
    root_oqpy_program.declare(
        [oqpy.Qubit(aq_constants.QUBIT_REGISTER, num_qubits)],
        to_beginning=True,
    )


def _convert_subroutine(
    f: Callable,
    options: converter.ConversionOptions,
    args: list[Any],
    kwargs: dict[str, Any],
) -> None:
    """Convert the initial callable `f` into a full AutoQASM program `program`.
    The contents of `f` are converted into a subroutine in the program.

    Some program pre- and post-processing occurs here, such as adding a qubit
    declaration and adding the subroutine invocation at the top level.

    Args:
        f (Callable): The function to be converted.
        options (converter.ConversionOptions): Converter options.
        args (list[Any]): Arguments passed to the program when called.
        kwargs (dict[str, Any]): Keyword arguments passed to the program when called.
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
            program_conversion_context.register_args(args)

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
        if return_instance is not None:
            return_variable = aq_types.wrap_value(return_instance)
            oqpy_program.declare(return_variable)
            oqpy_program.set(return_variable, subroutine_function_call)
        else:
            function_call = subroutine_function_call.to_ast(oqpy_program)
            oqpy_program._add_statement(qasm_ast.ExpressionStatement(function_call))

        # Store the return variable in the program conversion context
        program_conversion_context.return_variable = return_variable

        # Add the subroutine definition to the root-level program if necessary
        root_oqpy_program = program_conversion_context.get_oqpy_program(
            scope=aq_program.ProgramScope.MAIN
        )
        subroutine_name = subroutine_function_call.identifier.name
        if (
            subroutine_name not in root_oqpy_program.subroutines
            and subroutine_function_call.subroutine_decl is not None
        ):
            root_oqpy_program._add_subroutine(
                subroutine_name, subroutine_function_call.subroutine_decl
            )

    return program_conversion_context.return_variable


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
            name=param.name,
            kind=param.kind,
            annotation=aq_types.map_parameter_type(param.annotation),
        )
        new_params.append(new_param)
        _func.__annotations__[new_param.name] = new_param.annotation

    _func.__signature__ = sig.replace(parameters=new_params)
    return _func


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


def _make_return_instance_from_f_annotation(f: Callable) -> Any:
    # TODO: Recursive functions should work even if the user's type hint is wrong
    annotations = f.__annotations__
    return_type = annotations["return"] if "return" in annotations else None
    return return_type() if return_type else None


def _make_return_instance_from_oqpy_return_type(return_type: Any) -> Any:
    if not return_type:
        return None

    var_type = aq_types.conversions.var_type_from_ast_type(return_type)
    if var_type == aq_types.BitVar:
        return var_type(size=_get_bitvar_size(return_type))
    return var_type()


def _get_bitvar_size(node: qasm_ast.BitType) -> Optional[int]:
    if not isinstance(node, qasm_ast.BitType) or not node.size:
        return None
    return node.size.value


def _convert_gate(
    f: Callable,
    options: converter.ConversionOptions,
    args: list[Any],
    kwargs: dict[str, Any],
) -> Callable:
    # We must be inside an active conversion context in order to invoke a gate
    program_conversion_context = aq_program.get_program_conversion_context()

    # Wrap the function into an oqpy gate definition
    wrapped_f = _wrap_for_oqpy_gate(f, options)
    gate_name = f.__name__

    # Validate that the gate definition acts on at least one qubit
    gate_args = _get_gate_args(f)
    if not gate_args.qubits:
        raise errors.ParameterTypeError(
            f'Gate definition "{gate_name}" has no arguments of type aq.Qubit. '
            "Every gate definition must contain at least one qubit argument."
        )

    # Process the gate definition
    with program_conversion_context.gate_definition(gate_name, gate_args):
        wrapped_f(gate_args._args)

    # Add the gate definition to the root-level program if necessary
    root_oqpy_program = program_conversion_context.get_oqpy_program(
        scope=aq_program.ProgramScope.MAIN, mode=aq_program.ProgramMode.UNITARY
    )
    if gate_name not in root_oqpy_program.gates:
        gate_stmt = program_conversion_context.get_oqpy_program(
            mode=aq_program.ProgramMode.UNITARY
        ).gates[gate_name]
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


def _wrap_for_oqpy_gate(
    f: Callable,
    options: converter.ConversionOptions,
) -> Callable[..., None]:
    """Wraps the given function into a callable expected by oqpy.gate.

    Args:
        f (Callable): The function to be wrapped.
        options (converter.ConversionOptions): Converter options.

    Returns:
        Callable[..., None]: The modified function for use with oqpy.gate.
    """

    def _func(*args: Any) -> None:
        aq_transpiler.converted_call(f, *args, kwargs={}, options=options)

    return _func


def _get_gate_args(f: Callable) -> aq_program.GateArgs:
    """Build a GateArgs object from the function signature of a gate.

    Args:
        f (Callable): Gate function

    Returns:
        aq_program.GateArgs: Object representing a list of qubit and angle arguments for
        a gate definition.
    """
    gate_args = aq_program.GateArgs()
    sig = inspect.signature(f)
    for param in sig.parameters.values():
        if param.annotation is param.empty:
            raise errors.MissingParameterTypeError(
                f'Parameter "{param.name}" for gate "{f.__name__}" '
                "is missing a required type hint."
            )

        if param.annotation == aq_instructions.QubitIdentifierType:
            gate_args.append_qubit(param.name)
        elif param.annotation == float or any(
            type_ == float for type_ in get_args(param.annotation)
        ):
            gate_args.append_angle(param.name)
        else:
            raise errors.ParameterTypeError(
                f'Parameter "{param.name}" for gate "{f.__name__}" '
                "must have a type hint of either aq.Qubit or float."
            )
    return gate_args


def _convert_calibration(
    f: Callable,
    options: converter.ConversionOptions,
    args: list[Any],
    kwargs: dict[str, Any],
    gate_function: Callable,
    **decorator_kwargs,
) -> GateCalibration:
    """Convert the initial callable `f` into a GateCalibration object that will be added to
    the main program as defcal.

    Args:
        f (Callable): The function to be converted.
        options (converter.ConversionOptions): Converter options.
        args (list[Any]): Arguments passed to the program when called.
        kwargs (dict[str, Any]): Keyword arguments passed to the program when called.
        gate_function (Callable): The gate function which calibration is being defined.

    Returns:
        GateCalibration: Object representing the calibration definition.
    """
    func_args = _get_gate_args(f)
    _validate_calibration_args(gate_function, decorator_kwargs, func_args)

    union_deco_func_args = {**decorator_kwargs, **{var.name: var for var in func_args._args}}

    gate_calibration_qubits = []
    gate_calibration_angles = []
    gate_args = _get_gate_args(gate_function)
    for i, var in enumerate(gate_args._args):
        name = var.name
        value = union_deco_func_args[name]
        is_qubit = i in gate_args.qubit_indices

        if is_qubit and not is_qubit_identifier_type(value):
            raise errors.ParameterTypeError(f'Parameter "{name}" must have a type of aq.Qubit.')

        if not is_qubit and not isinstance(value, (float, oqpy.AngleVar)):
            raise errors.ParameterTypeError(f'Parameter "{name}" must have a type of float.')

        if is_qubit:
            gate_calibration_qubits.append(value)
        else:
            gate_calibration_angles.append(value)

    func_call_kwargs = {
        **{var.name: var for var in func_args.qubits},
        **{
            var.name: oqpy.FloatVar(name=var.name, needs_declaration=False)
            for var in func_args.angles
        },
    }

    with aq_program.build_program() as program_conversion_context:
        with program_conversion_context.calibration_definition(
            gate_function.__name__, gate_calibration_qubits, gate_calibration_angles
        ):
            aq_transpiler.converted_call(f, [], func_call_kwargs, options=options)

    return GateCalibration(
        gate_function=gate_function,
        qubits=gate_calibration_qubits,
        angles=gate_calibration_angles,
        program=program_conversion_context.make_program(),
    )


def _validate_calibration_args(
    gate_function: Callable,
    decorator_args: dict[str, Union[Qubit, float]],
    func_args: aq_program.GateArgs,
) -> None:
    """Validate the arguments passed to the calibration decorator and function.

    Args:
        gate_function (Callable): The gate function which calibration is being defined.
        decorator_args (dict[str, Union[Qubit, float]]): The calibration decorator arguments.
        func_args (aq_program.GateArgs): The gate function arguments.
    """
    gate_args = _get_gate_args(gate_function)
    gate_args_names = [var.name for var in gate_args._args]
    func_args_names = [var.name for var in func_args._args]
    decorator_args_names = decorator_args.keys()

    # validate the name of args
    if not set(gate_args_names) == set(decorator_args_names) | set(func_args_names):
        raise errors.InvalidCalibrationDefinition(
            "The union of calibration decorator arguments and function arguments must match the"
            " gate arguments."
        )

    if any(name in decorator_args_names for name in func_args_names):
        raise errors.InvalidCalibrationDefinition(
            "The function arguments must not duplicate any argument in the calibration decorator."
        )
