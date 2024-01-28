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

"""AutoQASM Program class, context managers, and related functions."""
from __future__ import annotations

import contextlib
import copy
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union

import oqpy.base
import pygments
from openqasm_pygments import OpenQASM3Lexer
from pygments.formatters.terminal import TerminalFormatter
from sympy import Symbol

import braket.experimental.autoqasm.types as aq_types
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.serialization import IRType, SerializableProgram
from braket.device_schema import DeviceActionType
from braket.devices.device import Device
from braket.experimental.autoqasm import constants, errors
from braket.experimental.autoqasm.instructions.qubits import QubitIdentifierType as Qubit
from braket.experimental.autoqasm.instructions.qubits import _get_physical_qubit_indices, _qubit
from braket.experimental.autoqasm.program.serialization_properties import (
    OpenQASMSerializationProperties,
    SerializationProperties,
)
from braket.pulse.ast.qasm_parser import ast_to_qasm

# Create the thread-local object for the program conversion context.
_local = threading.local()


def _get_local() -> threading.local:
    """Gets the thread-local object which stores the program conversion context.
    Returns:
        local: The thread-local object which stores the program conversion context.
    """
    if not hasattr(_local, "program_conversion_context"):
        setattr(_local, "program_conversion_context", None)
    return _local


@dataclass
class UserConfig:
    """User-specified configurations that influence program building."""

    num_qubits: Optional[int] = None
    """The total number of qubits to declare in the program."""

    device: Optional[Device] = None
    """The target device for the program."""


class ProgramScope(Enum):
    """Values used to specify the desired scope of a program to obtain."""

    CURRENT = 0
    """References the current scope of the program conversion context."""
    MAIN = 1
    """References the top-level (root) scope of the program conversion context."""


class ProgramMode(Enum):
    """Values used to specify the desired mode of a program conversion context."""

    NONE = 0
    """For general program conversion where all operations are allowed."""
    UNITARY = 1
    """For program conversion inside a context where only unitary operations are allowed."""
    PULSE = 2
    """For program conversion inside a context where only pulse operations are allowed."""


class Program(SerializableProgram):
    """The program that has been generated with AutoQASM. This object can
    be passed to the run() method of a Braket Device."""

    def __init__(
        self,
        oqpy_program: oqpy.Program,
        has_pulse_control: bool = False,
    ):
        """Initializes an AutoQASM Program object.

        Args:
            oqpy_program (oqpy.Program): The oqpy program object which
                contains the generated program.
            has_pulse_control (bool): Whether the program contains pulse
                control instructions. Defaults to False.
        """
        self._oqpy_program = oqpy_program
        self._has_pulse_control = has_pulse_control

    def with_calibrations(self, gate_calibrations: Union[Callable, list[Callable]]) -> Program:
        """Add the gate calibrations to the program. The calibration added program is returned
        as a new object. The original program is not modified.

        Args:
            gate_calibrations (Union[Callable, list[Callable]]): The gate calibrations to add to
                the main program. Calibration are passed as callable without evaluation.

        Returns:
            Program: The program with gate calibrations added.
        """
        if isinstance(gate_calibrations, Callable):
            gate_calibrations = [gate_calibrations]
        assert all(isinstance(gc, Callable) for gc in gate_calibrations)

        combined_oqpy_program = oqpy.Program(simplify_constants=False)
        for gc in gate_calibrations:
            combined_oqpy_program += gc().program._oqpy_program
        combined_oqpy_program += self._oqpy_program
        return Program(combined_oqpy_program, has_pulse_control=True)

    def make_bound_program(self, param_values: dict[str, float], strict: bool = False) -> Program:
        """Binds FreeParameters based upon their name and values passed in.

        Args:
            param_values (dict[str, float]): A mapping of FreeParameter names
                to a value to assign to them.
            strict (bool): If True, raises a ParameterNotFoundError if any of the FreeParameters
                in param_values do not appear in the program. False by default.

        Raises:
            ParameterNotFoundError: If a parameter name is given which does not appear in
                the program.

        Returns:
            Program: Returns a program with all present parameters fixed to their respective
            values.
        """
        # Copy the program so that we don't modify the original program
        bound_oqpy_program = copy.deepcopy(self._oqpy_program)
        for name, value in param_values.items():
            if name in bound_oqpy_program.undeclared_vars:
                target = bound_oqpy_program.undeclared_vars[name]
                assert target.init_expression == "input", "Only free parameters can be bound."
                target.init_expression = value
            elif strict:
                raise errors.ParameterNotFoundError(f"No parameter in the program named: {name}")

        return Program(bound_oqpy_program, self._has_pulse_control)

    def to_ir(
        self,
        ir_type: IRType = IRType.OPENQASM,
        serialization_properties: SerializationProperties = OpenQASMSerializationProperties(),
    ) -> str:
        """Serializes the program into an intermediate representation.

        Args:
            ir_type (IRType): The IRType to use for converting the program to its
                IR representation. Defaults to IRType.OPENQASM.
            serialization_properties (SerializationProperties): IR serialization configuration.
                Default to OpenQASMSerializationProperties().

        Raises:
            ValueError: If the supplied `ir_type` is not supported.

        Returns:
            str: A representation of the program in the `ir_type` format.
        """
        if ir_type == IRType.OPENQASM:
            openqasm_ast = self._oqpy_program.to_ast(
                encal_declarations=self._has_pulse_control,
                include_externs=serialization_properties.include_externs,
            )
            openqasm_ir = ast_to_qasm(openqasm_ast)
            if self._has_pulse_control and not serialization_properties.auto_defcalgrammar:
                openqasm_ir = openqasm_ir.replace('defcalgrammar "openpulse";\n', "")
            return openqasm_ir

        raise ValueError(f"Supplied ir_type {ir_type} is not supported.")

    def display(self, ir_type: IRType = IRType.OPENQASM) -> None:
        """
        Print the Program with syntax highlighting. Returns `None` to avoid
        duplicate printing when used with `print(program.display())`.

        Args:
            ir_type (IRType): The IRType to use for displaying the program.
                Defaults to IRType.OPENQASM.
        """
        print(pygments.highlight(self.to_ir(ir_type), OpenQASM3Lexer(), TerminalFormatter()))


class GateArgs:
    """Represents a list of qubit and angle arguments for a gate definition."""

    def __init__(self):
        self._args: list[Union[oqpy.Qubit, oqpy.AngleVar]] = []

    def __len__(self):
        return len(self._args)

    def append_qubit(self, name: str) -> None:
        """Appends a qubit argument to the list of gate arguments.

        Args:
            name (str): The name of the argument.
        """
        self._args.append(oqpy.Qubit(name, needs_declaration=False))

    def append_angle(self, name: str) -> None:
        """Appends a parameter argument to the list of gate arguments.

        Args:
            name (str): The name of the argument.
        """
        self._args.append(oqpy.AngleVar(name=name))

    @property
    def qubits(self) -> list[oqpy.Qubit]:
        return [self._args[i] for i in self.qubit_indices]

    @property
    def angles(self) -> list[oqpy.AngleVar]:
        return [self._args[i] for i in self.angle_indices]

    @property
    def qubit_indices(self) -> list[int]:
        return [i for i, arg in enumerate(self._args) if isinstance(arg, oqpy.Qubit)]

    @property
    def angle_indices(self) -> list[int]:
        return [i for i, arg in enumerate(self._args) if isinstance(arg, oqpy.AngleVar)]


class ProgramConversionContext:
    """The data structure used while converting a program. Intended for internal use."""

    def __init__(self, user_config: Optional[UserConfig] = None):
        self.subroutines_processing = set()  # the set of subroutines queued for processing
        self.user_config = user_config or UserConfig()
        self.return_variable = None
        self.in_verbatim_block = False
        self.at_function_root_scope = True  # whether we are at the root scope of main or subroutine
        self._oqpy_program_stack = [oqpy.Program(simplify_constants=False)]
        self._gate_definitions_processing = []
        self._calibration_definitions_processing = []
        self._gates_defined = set()
        self._gates_used = set()
        self._virtual_qubits_used = set()
        self._var_idx = 0
        self._has_pulse_control = False
        self._free_parameters = {}

    def make_program(self) -> Program:
        """Makes a Program object using the oqpy program from this conversion context.

        Returns:
            Program: The program object.
        """
        # Validate the gates for the target device
        device = self.get_target_device()
        if device:
            device_supported_gates = self._normalize_gate_names(
                device.properties.action[DeviceActionType.OPENQASM].supportedOperations
            )
            valid_gates = self._gates_defined.union(device_supported_gates)
            invalid_gates_used = self._gates_used.difference(valid_gates)
            if invalid_gates_used:
                raise errors.UnsupportedGate(
                    f'The target device "{device.name}" does not support '
                    f"the following gates used in the program: {invalid_gates_used}"
                )
        return Program(self.get_oqpy_program(), has_pulse_control=self._has_pulse_control)

    @property
    def qubits(self) -> list[int]:
        """Return a sorted list of virtual qubits used in this program.

        Returns:
            list[int]: The list of virtual qubits, e.g. [0, 1, 2]
        """
        # Can be memoized or otherwise made more performant
        return sorted(list(self._virtual_qubits_used))

    def register_qubit(self, qubit: int) -> None:
        """Register a virtual qubit that is used in this program."""
        self._virtual_qubits_used.add(qubit)

    def get_declared_qubits(self) -> Optional[int]:
        """Return the number of qubits to declare in the program, as specified by the user.
        Returns None if the user did not specify how many qubits are in the program.
        """
        return self.user_config.num_qubits

    def register_gate(self, gate_name: str) -> None:
        """Register a gate that is used in this program.

        Args:
            gate_name (str): The name of the gate being used.

        Raises:
            errors.UnsupportedNativeGate: If the gate is being used inside a verbatim block
                and the gate is not a native gate of the target device.
        """
        if not self.in_verbatim_block:
            self._gates_used.add(gate_name)
            return

        # If we are in verbatim and there is a target device specified, validate that the
        # provided gate is a native gate on the target device (or is a custom gate definition).
        device = self.get_target_device()
        if device:
            native_gates = self._normalize_gate_names(device.properties.paradigm.nativeGateSet)
            allowed_verbatim_gates = self._gates_defined.union(native_gates)
            if gate_name not in allowed_verbatim_gates:
                raise errors.UnsupportedNativeGate(
                    f'The gate "{gate_name}" is not a native gate of the target '
                    f'device "{device.name}". Only native gates may be used inside a verbatim '
                    f"block. The native gates of the device are: {native_gates}"
                )

    def register_args(self, args: list[Any]) -> None:
        """Register any FreeParameters in the list of arguments.

        Args:
            args (list[Any]): Arguments passed to the main program or a subroutine.
        """
        for arg in args:
            if isinstance(arg, FreeParameterExpression):
                for free_symbol_name in self._free_symbol_names(arg):
                    self.register_parameter(free_symbol_name)

    @staticmethod
    def _free_symbol_names(expr: FreeParameterExpression) -> Iterable[str]:
        """Return the names of any free symbols found in the provided expression
        which are Symbol objects.

        Args:
            expr (FreeParameterExpression): The expression in which to look for free symbols.

        Returns:
            Iterable[str]: The list of free symbol names in sorted order (sorted to ensure
            that the order is deterministic).
        """
        return sorted([str(s) for s in expr._expression.free_symbols if isinstance(s, Symbol)])

    def register_parameter(
        self,
        parameter_name: str,
        parameter_type: Union[float, int, bool] = float,
    ) -> None:
        """Register an input parameter if it has not already been registered.

        Args:
            parameter_name (str): The name of the parameter to register with the program.
            parameter_type (Union[float, int, bool]): The type of the parameter to register
                with the program. Default: float.
        """
        # TODO (#814): add type validation against existing inputs
        if parameter_name not in self._free_parameters:
            if parameter_type == float:
                var_class = oqpy.FloatVar
            elif parameter_type == int:
                var_class = oqpy.IntVar
            elif parameter_type == bool:
                var_class = oqpy.BoolVar
            else:
                raise NotImplementedError(parameter_type)
            self._free_parameters[parameter_name] = var_class("input", name=parameter_name)

    def register_output(
        self,
        parameter_name: str,
        parameter_type: Union[float, int, bool] = float,
    ) -> None:
        """Register a new output parameter.

        Args:
            parameter_name (str): The name of the parameter to register with the program.
            parameter_type (Union[float, int, bool]): The type of the parameter to register
                with the program. Default: float.
        """
        if parameter_name in self._free_parameters:
            # TODO laurecap: name mangle?
            raise errors.AutoQasmError("TODO")

        # TODO laurecap: use wrap value?
        if issubclass(parameter_type, oqpy._ClassicalVar):
            var_class = parameter_type
        elif issubclass(parameter_type, (FreeParameterExpression, oqpy.base.OQPyExpression)):
            # TODO: update with support for typed free parameters
            var_class = oqpy.FloatVar
        elif parameter_type == float:
            var_class = oqpy.FloatVar
        elif parameter_type == int:
            var_class = oqpy.IntVar
        elif parameter_type == bool:
            var_class = oqpy.BoolVar
        elif parameter_type is type(None):
            return  # Don't register a new output
        else:
            raise NotImplementedError(parameter_type)
        self._free_parameters[parameter_name] = var_class("output", name=parameter_name)

    def get_expression_var(self, expression: FreeParameterExpression) -> oqpy.FloatVar:
        """Return an oqpy.FloatVar that represents the provided expression.

        Args:
            expression (FreeParameterExpression): The expression to represent.

        Raises:
            ParameterNotFoundError: If the expression contains any free parameter which has
            not already been registered with the program.

        Returns:
            FloatVar: The variable representing the expression.
        """
        # Validate that all of the free symbols are registered as free parameters.
        for name in self._free_symbol_names(expression):
            if name not in self._free_parameters:
                raise errors.ParameterNotFoundError(f"Free parameter '{name}' was not found.")

        # If the expression is just a standalone parameter, return the registered variable.
        if isinstance(expression, FreeParameter):
            return self._free_parameters[expression.name]

        # Otherwise, create a new variable and declare it here
        var = aq_types.FloatVar(init_expression=expression)
        self.get_oqpy_program().declare(var)
        return var

    def get_free_parameters(self) -> list[oqpy.FloatVar]:
        """Return a list of named oqpy.Vars that are used as free parameters in the program."""
        return list(self._free_parameters.values())

    def add_io_declarations(self) -> None:
        """Add input and output declaration statements to the program."""
        root_oqpy_program = self.get_oqpy_program(scope=ProgramScope.MAIN)
        for parameter_name, parameter in self._free_parameters.items():
            parameter.name = parameter_name
            root_oqpy_program._add_var(parameter)

    def get_target_device(self) -> Optional[Device]:
        """Return the target device for the program, as specified by the user.
        Returns None if the user did not specify a target device.
        """
        return self.user_config.device

    def next_var_name(self, kind: type) -> str:
        """Return the next name for a new classical variable.

        For example, a declared bit will be named __bit_0__ and the next integer
        will be named __int_1__.

        Args:
            kind (type): The type of the new variable.

        Returns:
            str: The name for the variable.
        """
        next = self._var_idx
        self._var_idx += 1
        if kind == oqpy.ArrayVar:
            return constants.ARRAY_NAME_TEMPLATE.format(next)
        elif kind == oqpy.BitVar:
            return constants.BIT_NAME_TEMPLATE.format(next)
        elif kind == oqpy.BoolVar:
            return constants.BOOL_NAME_TEMPLATE.format(next)
        elif kind == oqpy.FloatVar:
            return constants.FLOAT_NAME_TEMPLATE.format(next)
        elif kind == oqpy.IntVar:
            return constants.INT_NAME_TEMPLATE.format(next)

        raise NotImplementedError(f"Program's do not yet support type {kind}.")

    def is_var_name_used(self, var_name: str) -> bool:
        """Check if the variable already exists in the oqpy program.

        Args:
            var_name (str): variable name

        Returns:
            bool: Return True if the variable already exists
        """
        oqpy_program = self.get_oqpy_program()
        return (
            var_name in oqpy_program.declared_vars.keys()
            or var_name in oqpy_program.undeclared_vars.keys()
        )

    def validate_gate_targets(self, qubits: list[Any], angles: list[Any]) -> None:
        """Validate that the specified gate targets are valid at this point in the program.

        Args:
            qubits (list[Any]): The list of target qubits to validate.
            angles (list[Any]): The list of target angles to validate.

        Raises:
            errors.InvalidTargetQubit: Target qubits are invalid in the current context.
            errors.InvalidGateDefinition: Targets are invalid in the current gate definition.
        """
        if self.in_verbatim_block and not self._gate_definitions_processing:
            self._validate_verbatim_target_qubits(qubits)

        if self._gate_definitions_processing:
            gate_name = self._gate_definitions_processing[-1]["name"]
            gate_qubit_args = self._gate_definitions_processing[-1]["gate_args"].qubits
            for qubit in qubits:
                if not isinstance(qubit, oqpy.Qubit) or qubit not in gate_qubit_args:
                    qubit_name = qubit.name if isinstance(qubit, oqpy.Qubit) else str(qubit)
                    raise errors.InvalidGateDefinition(
                        f'Gate definition "{gate_name}" uses qubit "{qubit_name}" which is not '
                        "an argument to the gate. Gates may only operate on qubits which are "
                        "passed as arguments."
                    )
            gate_angle_args = self._gate_definitions_processing[-1]["gate_args"].angles
            gate_angle_arg_names = [arg.name for arg in gate_angle_args]
            for angle in angles:
                if isinstance(angle, oqpy.base.Var) and angle.name not in gate_angle_arg_names:
                    raise errors.InvalidGateDefinition(
                        f'Gate definition "{gate_name}" uses angle "{angle.name}" which is not '
                        "an argument to the gate. Gates may only use constant angles or angles "
                        "passed as arguments."
                    )

    @staticmethod
    def _normalize_gate_names(gate_names: Iterable[str]) -> list[str]:
        return [gate_name.lower() for gate_name in gate_names]

    def _validate_verbatim_target_qubits(self, qubits: list[Any]) -> None:
        # Only physical target qubits are allowed in a verbatim block:
        for qubit in qubits:
            if not isinstance(qubit, str):
                qubit_name = qubit.name if isinstance(qubit, oqpy.Qubit) else str(qubit)
                raise errors.InvalidTargetQubit(
                    f'Qubit "{qubit_name}" is not a physical qubit. Only physical qubits such '
                    'as "$0" can be targeted inside a verbatim block.'
                )
        qubits = _get_physical_qubit_indices(qubits)

        # Validate physical qubit connectivity on the target device:
        device = self.get_target_device()
        if device and not device.properties.paradigm.connectivity.fullyConnected:
            connectivity_graph = device.properties.paradigm.connectivity.connectivityGraph

            # connectivity_graph uses integer qubit indices, but represented as strings.
            start_qubit = qubits[0]
            valid_target_qubits = connectivity_graph[str(start_qubit)]
            for target_qubit in qubits[1:]:
                if str(target_qubit) not in valid_target_qubits:
                    raise errors.InvalidTargetQubit(
                        f'Qubit "{start_qubit}" is not connected to qubit "{target_qubit}" '
                        f'on device "{device.name}". The connectivity graph of the device is: '
                        f"{connectivity_graph}"
                    )

    def get_oqpy_program(
        self, scope: ProgramScope = ProgramScope.CURRENT, mode: ProgramMode = ProgramMode.NONE
    ) -> oqpy.Program:
        """Gets the oqpy.Program object associated with this program conversion context.

        Args:
            scope (ProgramScope): The scope of the oqpy.Program to retrieve.
                Defaults to ProgramScope.CURRENT.
            mode (ProgramMode): The mode for which the oqpy.Program is being retrieved.
                Defaults to ProgramMode.NONE.

        Raises:
            errors.InvalidGateDefinition: If this function is called from within a gate
            definition where only unitary gate operations are allowed, and the
            `mode` parameter is not specified as `ProgramMode.UNITARY`.
            errors.InvalidCalibrationDefinition: If this function is called from within a
            calibration definition where only pulse operations are allowed, and the
            `mode` parameter is not specified as `ProgramMode.PULSE`.

        Returns:
            oqpy.Program: The requested oqpy program.
        """
        if self._gate_definitions_processing and mode != ProgramMode.UNITARY:
            gate_name = self._gate_definitions_processing[-1]["name"]
            raise errors.InvalidGateDefinition(
                f'Gate definition "{gate_name}" contains invalid operations. '
                "A gate definition must only call unitary gate operations."
            )
        if self._calibration_definitions_processing and mode != ProgramMode.PULSE:
            gate_name = self._calibration_definitions_processing[-1]["name"]
            raise errors.InvalidCalibrationDefinition(
                f'Calibration definition "{gate_name}" contains invalid operations. '
                "A calibration definition must only call pulse operations."
            )

        if scope == ProgramScope.CURRENT:
            requested_index = -1
        elif scope == ProgramScope.MAIN:
            requested_index = 0
        else:
            raise NotImplementedError("Unexpected ProgramScope value")

        return self._oqpy_program_stack[requested_index]

    @contextlib.contextmanager
    def push_oqpy_program(self, oqpy_program: oqpy.Program) -> None:
        """Pushes the provided oqpy program onto the stack.

        Args:
            oqpy_program (Program): The oqpy program to push onto the stack.
        """
        try:
            self._oqpy_program_stack.append(oqpy_program)
            yield
        finally:
            self._oqpy_program_stack.pop()

    @contextlib.contextmanager
    def _control_flow_block(
        self, _context_manager: contextlib._GeneratorContextManager
    ) -> contextlib._GeneratorContextManager:
        original = self.at_function_root_scope
        try:
            self.at_function_root_scope = False
            with _context_manager as _cm:
                yield _cm
        finally:
            self.at_function_root_scope = original

    def _add_annotations(self, annotations: Optional[str | Iterable[str]] = None) -> None:
        oqpy_program = self.get_oqpy_program()
        for annotation in aq_types.make_annotations_list(annotations):
            oqpy_program.annotate(annotation)

    def if_block(self, condition: Any) -> contextlib._GeneratorContextManager:
        """Sets the program conversion context into an if block context.

        Args:
            condition (Any): The condition of the if block.

        Yields:
            _GeneratorContextManager: The context manager of the oqpy.If block.
        """
        oqpy_program = self.get_oqpy_program()
        return self._control_flow_block(oqpy.If(oqpy_program, condition))

    def else_block(self) -> contextlib._GeneratorContextManager:
        """Sets the program conversion context into an else block context.
        Must be immediately preceded by an if block.

        Yields:
            _GeneratorContextManager: The context manager of the oqpy.Else block.
        """
        oqpy_program = self.get_oqpy_program()
        return self._control_flow_block(oqpy.Else(oqpy_program))

    def for_in(
        self, iterator: aq_types.Range, iterator_name: Optional[str]
    ) -> contextlib._GeneratorContextManager:
        """Sets the program conversion context into a for loop context.

        Args:
            iterator (Range): The iterator of the for loop.
            iterator_name (Optional[str]): The symbol to use as the name of the iterator.

        Yields:
            _GeneratorContextManager: The context manager of the oqpy.ForIn block.
        """
        oqpy_program = self.get_oqpy_program()
        self._add_annotations(iterator.annotations)
        return self._control_flow_block(oqpy.ForIn(oqpy_program, iterator, iterator_name))

    def while_loop(self, condition: Any) -> contextlib._GeneratorContextManager:
        """Sets the program conversion context into a while loop context.

        Args:
            condition (Any): The condition of the while loop.

        Yields:
            _GeneratorContextManager: The context manager of the oqpy.While block.
        """
        oqpy_program = self.get_oqpy_program()
        return self._control_flow_block(oqpy.While(oqpy_program, condition))

    @contextlib.contextmanager
    def gate_definition(self, gate_name: str, gate_args: GateArgs) -> None:
        """Sets the program conversion context into a gate definition context.

        Args:
            gate_name (str): The name of the gate being defined.
            gate_args (GateArgs): The list of arguments to the gate.
        """
        self._gates_defined.add(gate_name)
        try:
            self._gate_definitions_processing.append({"name": gate_name, "gate_args": gate_args})
            with oqpy.gate(
                self.get_oqpy_program(mode=ProgramMode.UNITARY),
                gate_args.qubits,
                gate_name,
                gate_args.angles,
            ):
                yield
        finally:
            self._gate_definitions_processing.pop()

    @contextlib.contextmanager
    def calibration_definition(
        self, gate_name: str, qubits: Iterable[Qubit], angles: Iterable[float]
    ) -> None:
        """Sets the program conversion context into a calibration definition context.

        Args:
            gate_name (str): The name of the gate being defined.
            qubits (Iterable[Qubit]): The list of qubits to the gate.
            angles (Iterable[float]): The angles at which the gate calibration is defined.
        """
        try:
            qubits = [_qubit(q) for q in qubits]
            self._calibration_definitions_processing.append(
                {"name": gate_name, "qubits": qubits, "angles": angles}
            )
            with oqpy.defcal(
                self.get_oqpy_program(mode=ProgramMode.PULSE),
                qubits,
                gate_name,
                angles,
            ):
                yield
        finally:
            self._calibration_definitions_processing.pop()

    @contextlib.contextmanager
    def box(
        self,
        pragma: Optional[str] = None,
        annotations: Optional[str | Iterable[str]] = None,
    ) -> None:
        """Sets the program conversion context into a box context.

        Args:
            pragma (Optional[str]): Pragma to include before the box. Defaults to None.
            annotations (Optional[str | Iterable[str]]): Annotations for the box.
        """
        oqpy_program = self.get_oqpy_program()
        if pragma:
            oqpy_program.pragma(pragma)
        self._add_annotations(annotations)
        with oqpy.Box(oqpy_program):
            yield


@contextlib.contextmanager
def build_program(user_config: Optional[UserConfig] = None) -> None:
    """Creates a context manager which ensures there is a valid thread-local
    ProgramConversionContext object. If this context manager created the
    ProgramConversionContext object, it removes it from thread-local storage when
    exiting the context manager.

    For example::

        with build_program() as program_conversion_context:
            h(0)
            cnot(0, 1)
        program = program_conversion_context.make_program()

    Args:
        user_config (Optional[UserConfig]): User-supplied program building options.
    """
    try:
        owns_program_conversion_context = False
        if not _get_local().program_conversion_context:
            _get_local().program_conversion_context = ProgramConversionContext(user_config)
            owns_program_conversion_context = True
        yield _get_local().program_conversion_context
    except Exception as e:
        if isinstance(e, errors.AutoQasmError):
            raise
        elif hasattr(e, "ag_error_metadata"):
            raise e.ag_error_metadata.to_exception(e)
        else:
            raise
    finally:
        if owns_program_conversion_context:
            _get_local().program_conversion_context = None


def in_active_program_conversion_context() -> bool:
    """Indicates whether a program conversion context exists in the current scope,
    that is, whether there is an active program conversion context.

    Returns:
        bool: Whether there is a program currently being built.
    """
    return _get_local().program_conversion_context is not None


def get_program_conversion_context() -> ProgramConversionContext:
    """Gets the current thread-local ProgramConversionContext object.

    Must be called inside an active program conversion context (that is, while building a program)
    so that there is a valid thread-local ProgramConversionContext object.

    Returns:
        ProgramConversionContext: The thread-local ProgramConversionContext object.
    """
    assert (
        _get_local().program_conversion_context is not None
    ), "get_program_conversion_context() must be called inside build_program() block"
    return _get_local().program_conversion_context
