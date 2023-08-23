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

import contextlib
import threading
from dataclasses import dataclass
from typing import Any, List, Optional

import oqpy.base

from braket.circuits.serialization import IRType
from braket.experimental.autoqasm import constants, errors

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


class ProgramConversionContext:
    """The data structure used while converting a program. Intended for internal use."""

    def __init__(self, user_config: Optional[UserConfig] = None):
        self.oqpy_program_stack = [oqpy.Program()]
        self.subroutines_processing = set()  # the set of subroutines queued for processing
        self.user_config = user_config or UserConfig()
        self.return_variable = None
        self._gate_definitions_processing = []
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

    def validate_target_qubits(self, qubits: List[Any]) -> None:
        """Validate that the specified qubits are valid target qubits at this point in the program.

        Args:
            qubits (List[Any]): The list of target qubits to validate.

        Raises:
            errors.InvalidGateDefinition: Target qubits are invalid in the current gate definition.
        """
        if self._gate_definitions_processing:
            gate_name = self._gate_definitions_processing[-1]["name"]
            gate_qubit_args = self._gate_definitions_processing[-1]["qubits"]
            for qubit in qubits:
                if not isinstance(qubit, oqpy.Qubit) or qubit not in gate_qubit_args:
                    qubit_name = qubit.name if isinstance(qubit, oqpy.Qubit) else str(qubit)
                    raise errors.InvalidGateDefinition(
                        f'Gate definition "{gate_name}" uses qubit "{qubit_name}" which is not '
                        "an argument to the gate. Gates may only operate on qubits which are "
                        "passed as arguments."
                    )

    def get_oqpy_program(self) -> oqpy.Program:
        """Gets the oqpy program from the top of the stack.

        Returns:
            oqpy.Program: The current oqpy program.
        """
        return self.oqpy_program_stack[-1]

    @contextlib.contextmanager
    def push_oqpy_program(self, oqpy_program: oqpy.Program):
        """Pushes the provided oqpy program onto the stack.

        Args:
            oqpy_program (Program): The oqpy program to push onto the stack.
        """
        try:
            self.oqpy_program_stack.append(oqpy_program)
            yield
        finally:
            self.oqpy_program_stack.pop()

    @contextlib.contextmanager
    def gate_definition(self, gate_name: str, qubits: List[oqpy.Qubit], angles: List[float]):
        """Sets the program conversion context into a gate definition context.

        Args:
            gate_name (str): The name of the gate being defined.
            qubits (List[oqpy.Qubit]): The list of qubit arguments to the gate.
            angles (List[float]): The list of angle arguments to the gate.
        """
        try:
            self._gate_definitions_processing.append(
                {"name": gate_name, "qubits": qubits, "angles": angles}
            )
            with oqpy.gate(self.get_oqpy_program(), qubits, gate_name, angles):
                yield
        finally:
            self._gate_definitions_processing.pop()


@contextlib.contextmanager
def build_program(user_config: Optional[UserConfig] = None):
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