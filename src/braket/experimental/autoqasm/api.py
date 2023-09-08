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
from braket.aws import AwsDevice
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.autograph.core import converter
from braket.experimental.autoqasm.autograph.impl.api_core import (
    autograph_artifact,
    is_autograph_artifact,
)
from braket.experimental.autoqasm.autograph.tf_utils import tf_decorator
from braket.experimental.autoqasm.instructions.qubits import QubitIdentifierType as Qubit
from braket.experimental.autoqasm.instructions.qubits import is_qubit_identifier_type
from braket.experimental.autoqasm.program.gate_calibrations import GateCalibration


def main(
    *args, num_qubits: Optional[int] = None, device: Optional[Union[AwsDevice, str]] = None
) -> Callable[[Any], aq_program.Program]:
    """Decorator that converts a function into a callable that returns
    a Program object containing the quantum program.

    The decorator re-converts the target function whenever the decorated
    function is called, and a new Program object is returned each time.

    Args:
        num_qubits (Optional[int]): Configuration to set the total number of qubits to declare in
            the program.
        device (Optional[Union[AwsDevice, str]]): Configuration to set the target device for the
            program. Can be either an AwsDevice object or a valid Amazon Braket device ARN.

    Returns:
        Callable[[Any], Program]: A callable which returns the converted
        quantum program when called.
    """
    if isinstance(device, str):
        device = AwsDevice(device)

    return _function_wrapper(
        args,
        _convert_main,
        converter_args={"user_config": aq_program.UserConfig(num_qubits=num_qubits, device=device)},
    )


def subroutine(*args) -> Callable[[Any], aq_program.Program]:
    """Decorator that converts a function into a callable that will insert a subroutine into
    the quantum program.

    Returns:
        Callable[[Any], Program]: A callable which returns the converted
        quantum program when called.
    """
    return _function_wrapper(args, _convert_subroutine)


def gate(*args) -> Callable[[Any], None]:
    """Decorator that converts a function into a callable gate definition.

    Returns:
        Callable[[Any],]: A callable which can be used as a custom gate inside an
        aq.function or inside another aq.gate.
    """
    return _function_wrapper(args, _convert_gate)


def pulse_sequence(*args, **kwargs):
    if "implements" in kwargs:
        assert len(args) == 0, "Cannot specify both `implements` and positional arguments."
        return _calibration(**kwargs)
    else:
        return main(*args, **kwargs)


def _calibration(*args, implements: Callable, **kwargs):
    """A decorator that register the decorated function as a calibration definition of a gate
    in this `GateCalibrations` object.

    Args:
        gate_name (str): Name of the gate
        qubits (Union[Qubit,Iterable[Qubit]]): The qubits on which the gate calibration is
            defined.
        angles (Union[float, Iterable[float]]): The angles at which the gate calibration is
                defined. Defaults to [].
    """
    converter_args = {"gate_function": implements, **kwargs}

    return _function_wrapper(args, _convert_calibration, converter_args)


def _function_wrapper(
    args: Tuple[Any],
    converter_callback: Callable,
    converter_args: Optional[Dict[str, Any]] = None,
) -> Callable[[Any], aq_program.Program]:
    """Wrapping and conversion logic around the user function `f`.

    Args:
        args (Tuple[Any]): The arguments to the decorated function.
        converter_callback (Callable): The function converter, e.g., _convert_main.
        converter_args (Optional[Dict[str, Any]]): Extra arguments for the function converter.

    Returns:
        Callable[[Any], Program]: A callable which returns the converted
        quantum program when called.
    """
    if not args:
        # This the case where a decorator is called with only keyword args, for example:
        #     @aq.main(num_qubits=4)
        #     def my_function():
        # To make this work, here we simply return another wrapper function which expects
        # a Callable as the first argument.
        def _function_wrapper_with_params(*args) -> Callable[[Any], aq_program.Program]:
            return _function_wrapper(args, converter_callback, converter_args=converter_args)

        return _function_wrapper_with_params

    f = args[0]
    if is_autograph_artifact(f):
        return f

    if not converter_args:
        converter_args = {}

    def _wrapper(*args, **kwargs) -> Callable:
        """Wrapper that calls the converted version of f."""
        options = converter.ConversionOptions(
            user_requested=True,
            optional_features=_autograph_optional_features(),
        )
        # Call the appropriate function converter
        return converter_callback(f, options, args, kwargs, **converter_args)

    if inspect.isfunction(f) or inspect.ismethod(f):
        _wrapper = functools.update_wrapper(_wrapper, f)

    decorated_wrapper = tf_decorator.make_decorator(f, _wrapper)
    return autograph_artifact(decorated_wrapper)


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
        [oqpy.QubitArray(aq_constants.QUBIT_REGISTER, num_qubits)],
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
            name=param.name, kind=param.kind, annotation=aq_types.map_type(param.annotation)
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


def _make_return_instance_from_oqpy_return_type(return_type: Any) -> Any:
    if not return_type:
        return None

    return_type = aq_types.conversions.var_type_from_ast_type(return_type)
    if return_type == aq_types.ArrayVar:
        return []
    return return_type()


def _convert_gate(
    f: Callable,
    options: converter.ConversionOptions,
    args: List[Any],
    kwargs: Dict[str, Any],
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
        Callable: The modified function for use with oqpy.gate.
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
            gate_args.append(param.name, True)
        elif param.annotation in [float, aq_types.FloatVar]:
            gate_args.append(param.name, False)
        else:
            raise errors.ParameterTypeError(
                f'Parameter "{param.name}" for gate "{f.__name__}" '
                "must have a type hint of either aq.Qubit or float."
            )
    return gate_args


def _convert_calibration(
    f: Callable,
    options: converter.ConversionOptions,
    args: List[Any],
    kwargs: Dict[str, Any],
    gate_function: Callable,
    **decorator_kwargs,
) -> GateCalibration:
    """Convert the initial callable `f` into a GateCalibration object that will be added to
    the main program as defcal.

    Args:
        f (Callable): The function to be converted.
        options (converter.ConversionOptions): Converter options.
        args (List[Any]): Arguments passed to the program when called.
        kwargs (Dict[str, Any]): Keyword arguments passed to the program when called.
        gate_function (Callable): The gate function which calibration is being defined.
        decorator_kwargs: Keyword arguments passed to the calibration decorator.

    Returns:
        GateCalibration: Object representing the calibration definition.
    """
    decorator_qubit_names, decorator_angle_names = _categorize_calibration_decorator_args(
        decorator_kwargs
    )
    func_args = _get_gate_args(f)
    _validate_calibration_args(gate_function, decorator_kwargs, func_args)

    fixed_valued_qubits = [decorator_kwargs[name] for name in decorator_qubit_names]
    fixed_valued_angles = [decorator_kwargs[name] for name in decorator_angle_names]
    variable_qubits = [oqpy.Qubit(name=q.name) for q in func_args.qubits]
    variable_angles = [oqpy.FloatVar(name=a.name) for a in func_args.angles]
    qubits = fixed_valued_qubits + variable_qubits
    angles = fixed_valued_angles + variable_angles

    func_call_kwargs = {var.name: var for var in variable_qubits + variable_angles}

    with aq_program.build_program() as program_conversion_context:
        with program_conversion_context.calibration_definition(
            gate_function.__name__, qubits, angles
        ):
            aq_transpiler.converted_call(f, [], func_call_kwargs, options=options)

    return GateCalibration(
        gate_function=gate_function,
        qubits=qubits,
        angles=angles,
        oqpy_program=program_conversion_context.get_oqpy_program(),
    )


def _validate_calibration_args(
    gate_function: Callable,
    decorator_args: Dict[str, Union[Qubit, float]],
    func_args: aq_program.GateArgs,
) -> None:
    """Validate the arguments passed to the calibration decorator and function.

    Args:
        gate_function (Callable): The gate function which calibration is being defined.
        decorator_args (Dict[str, Union[Qubit, float]]): The calibration decorator arguments.
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

    # validate the type of args
    for qubit_arg in gate_args.qubits:
        if qubit_arg.name in decorator_args_names and not is_qubit_identifier_type(
            decorator_args[qubit_arg.name]
        ):
            raise errors.ParameterTypeError(
                f'Parameter "{qubit_arg.name}" must have a type of aq.Qubit.'
            )
        if qubit_arg.name in func_args_names and qubit_arg.name not in [
            var.name for var in func_args.qubits
        ]:
            raise errors.ParameterTypeError(
                f'Parameter "{qubit_arg.name}" must have a type hint of aq.Qubit.'
            )

    for angle_arg in gate_args.angles:
        if angle_arg.name in decorator_args_names and not isinstance(
            decorator_args[angle_arg.name], float
        ):
            raise errors.ParameterTypeError(
                f'Parameter "{angle_arg.name}" must have a type of float.'
            )
        if angle_arg.name in func_args_names and angle_arg.name not in [
            var.name for var in func_args.angles
        ]:
            raise errors.ParameterTypeError(
                f'Parameter "{angle_arg.name}" must have a type hint of float.'
            )


def _categorize_calibration_decorator_args(decorator_kwargs) -> Tuple[List[str], List[str]]:
    """Categorize the calibration decorator arguments into qubit and angle.

    Args:
        decorator_kwargs (Dict[str, Any]): The calibration decorator arguments.

    Returns:
        Tuple[List[str], List[str]]: The qubit and angle names.
    """
    decorator_qubit_names = []
    decorator_angle_names = []

    for k, v in decorator_kwargs.items():
        if is_qubit_identifier_type(v):
            decorator_qubit_names.append(k)
        elif isinstance(v, float):
            decorator_angle_names.append(k)
        else:
            raise errors.ParameterTypeError(
                f"Argument {k} does not have a valid type of qubits (aq.Qubit) or angles (float). "
            )

    return decorator_qubit_names, decorator_angle_names
