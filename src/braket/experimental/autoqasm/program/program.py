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

import enum
import threading
from dataclasses import dataclass
from typing import List, Optional

import oqpy.base

from braket.circuits.serialization import IRType
from braket.experimental.autoqasm import constants

# Prepare to initialize the global program conversion context.
_local = threading.local()
setattr(_local, "program_conversion_context", None)


class ProgramOptions(enum.Enum):
    """All options configurable by the user at program invocation time via keyword arguments
    injected by the aq.function decorator.
    """

    # Note: this is the exact kwarg name that the user must pass,
    # which is later input to UserConfig
    NUM_QUBITS = "num_qubits"


@dataclass
class UserConfig:
    """User-specified configurations that influence program building."""

    num_qubits: Optional[int] = None


class Program:
    """The program that has been generated with AutoQASM. This object can
    be passed to the run() method of a Braket Device."""

    def __init__(self, oqpy_program: oqpy.Program):
        """Initializes an AutoQASM Program object.

        Args:
            oqpy_program (oqpy.Program): The oqpy program object which
                contains the generated program.
        """
        self._oqpy_program = oqpy_program

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
            return self._oqpy_program.to_qasm()

        raise ValueError(f"Supplied ir_type {ir_type} is not supported.")


class ProgramConversionContext:
    """The data structure used while converting a program. Intended for internal use."""

    def __init__(self, user_config: Optional[UserConfig] = None):
        self.oqpy_program_stack = [oqpy.Program()]
        self.subroutines_processing = set()  # the set of subroutines queued for processing
        self.user_config = user_config or UserConfig()
        self._qubits_seen = set()
        self._var_idx = 0

    def make_program(self) -> Program:
        """Makes a Program object using the oqpy program from this conversion context.

        Returns:
            Program: The program object.
        """
        return Program(self.get_oqpy_program())

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

    def get_oqpy_program(self) -> oqpy.Program:
        """Gets the oqpy program from the top of the stack.

        Returns:
            oqpy.Program: The current oqpy program.
        """
        return self.oqpy_program_stack[-1]

    class OqpyProgramContextManager:
        """Context manager responsible for managing the oqpy programs which are used
        by the ProgramConversionContext."""

        def __init__(self, oqpy_program: oqpy.Program, oqpy_program_stack: List[oqpy.Program]):
            self.oqpy_program = oqpy_program
            self.oqpy_program_stack = oqpy_program_stack

        def __enter__(self):
            self.oqpy_program_stack.append(self.oqpy_program)

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.oqpy_program_stack.pop()

    def push_oqpy_program(self, oqpy_program: oqpy.Program) -> OqpyProgramContextManager:
        """Pushes the provided oqpy program onto the stack.

        Args:
            oqpy_program (Program): The oqpy program to push onto the stack.

        Returns:
            OqpyProgramContextManager: A context manager which will pop the provided
            oqpy program from the stack when exited.
        """
        return self.OqpyProgramContextManager(oqpy_program, self.oqpy_program_stack)


class ProgramContextManager:
    """Context responsible for managing the ProgramConversionContext."""

    def __init__(self, user_config):
        self.owns_program_conversion_context = False
        self.user_config = user_config

    def __enter__(self) -> ProgramConversionContext:
        if not _local.program_conversion_context:
            _local.program_conversion_context = ProgramConversionContext(self.user_config)
            self.owns_program_conversion_context = True
        return _local.program_conversion_context

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.owns_program_conversion_context:
            _local.program_conversion_context = None


def build_program(user_config: Optional[UserConfig] = None) -> ProgramContextManager:
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

    Returns:
        ProgramContextManager: The context manager which manages
        the thread-local Program object.
    """
    return ProgramContextManager(user_config)


def in_active_program_conversion_context() -> bool:
    """Indicates whether a program conversion context exists in the current scope,
    that is, whether there is an active ProgramContextManager.

    Returns:
        bool: Whether there is a program currently being built.
    """
    return _local.program_conversion_context is not None


def get_program_conversion_context() -> ProgramConversionContext:
    """Gets the current thread-local ProgramConversionContext object.

    Must be called inside an active ProgramContextManager (that is, while building a program) so
    that there is a valid thread-local ProgramConversionContext object.

    Returns:
        ProgramConversionContext: The thread-local ProgramConversionContext object.
    """
    assert (
        _local.program_conversion_context is not None
    ), "get_program_conversion_context() must be called inside build_program() block"
    return _local.program_conversion_context
