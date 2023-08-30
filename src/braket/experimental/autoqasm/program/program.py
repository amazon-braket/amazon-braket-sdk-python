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
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, List, Optional, Union

import oqpy.base

from braket.circuits.serialization import IRType
from braket.experimental.autoqasm import constants, errors
from braket.experimental.autoqasm.instructions.qubits import QubitIdentifierType as Qubit
from braket.experimental.autoqasm.instructions.qubits import _qubit
from braket.experimental.autoqasm.program.gate_calibrations import GateCalibration

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


class Program:
    """The program that has been generated with AutoQASM. This object can
    be passed to the run() method of a Braket Device."""

    def __init__(self, oqpy_program: oqpy.Program, has_pulse_control: bool = False):
        """Initializes an AutoQASM Program object.

        Args:
            oqpy_program (oqpy.Program): The oqpy program object which
                contains the generated program.
            has_pulse_control (bool): Whether the program contains pulse
                control instructions. Defaults to False.
        """
        self._oqpy_program = oqpy_program
        self._has_pulse_control = has_pulse_control

    def bind_calibrations(
        self, gate_calibrations: Union[GateCalibration, List[GateCalibration]]
    ) -> Program:
        """Binds the gate calibrations to the program.

        Args:
            gate_calibrations (Union[GateCalibration, List[GateCalibration]]): The gate
                calibrations to bind.
        """
        if isinstance(gate_calibrations, GateCalibration):
            gate_calibrations = [gate_calibrations]

        combined_oqpy_program = oqpy.Program()
        for gc in gate_calibrations:
            combined_oqpy_program += gc.oqpy_program
        self._oqpy_program = combined_oqpy_program + self._oqpy_program
        return self

    def to_ir(
        self,
        ir_type: IRType = IRType.OPENQASM,
    ) -> str:
        """Serializes the program into an intermediate representation.

        Args:
            ir_type (IRType): The IRType to use for converting the program to its
                IR representation. Defaults to IRType.OPENQASM.

        Raises:
            ValueError: If the supplied `ir_type` is not supported.

        Returns:
            str: A representation of the program in the `ir_type` format.
        """
        if ir_type == IRType.OPENQASM:
            return self._oqpy_program.to_qasm(encal_declarations=self._has_pulse_control)

        raise ValueError(f"Supplied ir_type {ir_type} is not supported.")


class GateArgs:
    """Represents a list of qubit and angle arguments for a gate definition."""

    def __init__(self):
        self._args: List[Union[oqpy.Qubit, oqpy.AngleVar]] = []

    def __len__(self):
        return len(self._args)

    def append(self, name: str, is_qubit: bool) -> None:
        """Appends an argument to the list of gate arguments.

        Args:
            name (str): The name of the argument.
            is_qubit (bool): Whether the argument represents a qubit.
        """
        if is_qubit:
            self._args.append(oqpy.Qubit(name, needs_declaration=False))
        else:
            self._args.append(oqpy.AngleVar(name=name))

    @property
    def qubits(self) -> List[oqpy.Qubit]:
        return [self._args[i] for i in self.qubit_indices]

    @property
    def angles(self) -> List[oqpy.AngleVar]:
        return [self._args[i] for i in self.angle_indices]

    @property
    def qubit_indices(self) -> List[int]:
        return [i for i, arg in enumerate(self._args) if isinstance(arg, oqpy.Qubit)]

    @property
    def angle_indices(self) -> List[int]:
        return [i for i, arg in enumerate(self._args) if isinstance(arg, oqpy.AngleVar)]


class ProgramConversionContext:
    """The data structure used while converting a program. Intended for internal use."""

    def __init__(self, user_config: Optional[UserConfig] = None):
        self.subroutines_processing = set()  # the set of subroutines queued for processing
        self.user_config = user_config or UserConfig()
        self.return_variable = None
        self._oqpy_program_stack = [oqpy.Program()]
        self._gate_definitions_processing = []
        self._calibration_definitions_processing = []
        self._qubits_seen = set()
        self._var_idx = 0
        self._has_pulse_control = False

    def make_program(self) -> Program:
        """Makes a Program object using the oqpy program from this conversion context.

        Returns:
            Program: The program object.
        """
        return Program(self.get_oqpy_program(), has_pulse_control=self._has_pulse_control)

    @property
    def qubits(self) -> List[int]:
        """Return a sorted list of virtual qubits used in this program.

        Returns:
            List[int]: The list of virtual qubits, e.g. [0, 1, 2]
        """
        # Can be memoized or otherwise made more performant
        return sorted(list(self._qubits_seen))

    def register_qubit(self, qubit: int) -> None:
        """Register a virtual qubit to use in this program."""
        self._qubits_seen.add(qubit)

    def get_declared_qubits(self) -> Optional[int]:
        """Return the number of qubits to declare in the program, as specified by the user.
        Returns None if the user did not specify how many qubits are in the program.
        """
        return self.user_config.num_qubits

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

    def validate_gate_targets(self, qubits: List[Any], angles: List[Any]) -> None:
        """Validate that the specified gate targets are valid at this point in the program.

        Args:
            qubits (List[Any]): The list of target qubits to validate.
            angles (List[Any]): The list of target angles to validate.

        Raises:
            errors.InvalidGateDefinition: Targets are invalid in the current gate definition.
        """
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
            raise errors.InvalidGateDefinition(
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
    def gate_definition(self, gate_name: str, gate_args: GateArgs) -> None:
        """Sets the program conversion context into a gate definition context.

        Args:
            gate_name (str): The name of the gate being defined.
            gate_args (GateArgs): The list of arguments to the gate.
        """
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
            qubits (Tuple[Qubit]): The list of qubits to the gate.
            angles (Tuple[float]): The angles at which the gate calibration is defined.
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
