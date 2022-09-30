# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from __future__ import annotations

import io
from copy import deepcopy
from typing import Any, Dict, List, Optional, Set, Union

from oqpy import BitVar, Program
from oqpy.base import OQDurationLiteral
from oqpy.vendor.openpulse import ast
from oqpy.vendor.openpulse.printer import Printer
from oqpy.vendor.openqasm3.ast import DurationLiteral
from oqpy.vendor.openqasm3.printer import PrinterState
from oqpy.vendor.openqasm3.visitor import QASMTransformer

from braket.circuits.free_parameter import FreeParameter
from braket.circuits.free_parameter_expression import (
    FreeParameterExpression,
    FreeParameterExpressionIdentifier,
)
from braket.circuits.parameterizable import Parameterizable
from braket.pulse.frame import Frame
from braket.pulse.pulse_sequence_approximation import PulseSequenceApproximation
from braket.pulse.pulse_sequence_program_parser import _PulseSequenceProgramParser
from braket.pulse.waveforms import Waveform


class PulseSequence:
    """
    A representation of a collection of instructions to be performed on a quantum device
    and the requested results.
    """

    def __init__(self):
        self._capture_v0_count = 0
        self._program = Program()
        # TODO: Remove once oqpy.Program exposes the frames and waveforms
        self._frames = {}
        self._waveforms = {}
        self._free_parameters = set()

    def generate_approximation(self) -> PulseSequenceApproximation:
        """Generate an approximation of this PulseSequence.
        Returns:
            PulseSequenceApproximation: The approximation.
        """
        parser = _PulseSequenceProgramParser(self._program, self._frames)
        return PulseSequenceApproximation(
            amplitudes=parser.amplitudes, frequencies=parser.frequencies, phases=parser.phases
        )

    @property
    def parameters(self) -> Set[FreeParameter]:
        """Returns the set of `FreeParameter`s in the PulseSequence."""
        return self._free_parameters.copy()

    def set_frequency(
        self, frame: Frame, frequency: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to set the frequency of the frame to the specified `frequency` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be set.
            frequency (Union[float, FreeParameterExpression]): frequency value to set
                for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """

        _validate_uniqueness(self._frames, frame)
        self._program.set_frequency(frame=frame, freq=self._format_parameter_ast(frequency))
        self._frames[frame.id] = frame
        return self

    def shift_frequency(
        self, frame: Frame, frequency: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to shift the frequency of the frame by the specified `frequency` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be shifted.
            frequency (Union[float, FreeParameterExpression]): frequency value by which to shift
                the frequency for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.shift_frequency(frame=frame, freq=self._format_parameter_ast(frequency))
        self._frames[frame.id] = frame
        return self

    def set_phase(
        self, frame: Frame, phase: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to set the phase of the frame to the specified `phase` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be set.
            phase (Union[float, FreeParameterExpression]): phase value to set
                for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.set_phase(frame=frame, phase=self._format_parameter_ast(phase))
        self._frames[frame.id] = frame
        return self

    def shift_phase(
        self, frame: Frame, phase: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to shift the phase of the frame by the specified `phase` value.

        Args:
            frame (Frame): Frame for which the phase needs to be shifted.
            phase (Union[float, FreeParameterExpression]): phase value by which to shift
                the phase for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.shift_phase(frame=frame, phase=self._format_parameter_ast(phase))
        self._frames[frame.id] = frame
        return self

    def set_scale(
        self, frame: Frame, scale: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to set the scale on the frame to the specified `scale` value.

        Args:
            frame (Frame): Frame for which the scale needs to be set.
            scale (Union[float, FreeParameterExpression]): scale value to set
                on the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.set_scale(frame=frame, scale=self._format_parameter_ast(scale))
        self._frames[frame.id] = frame
        return self

    def delay(
        self, frames: Union[Frame, List[Frame]], duration: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to advance the frame clock by the specified `duration` value.

        Args:
            frames (Union[Frame, List[Frame]]): Frame(s) on which the delay needs to be introduced.
            duration (Union[float, FreeParameterExpression]): value (in seconds) defining
                the duration of the delay.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        if not isinstance(frames, list):
            frames = [frames]
        if isinstance(duration, FreeParameterExpression):
            for p in duration.expression.free_symbols:
                self._free_parameters.add(FreeParameter(p.name))
            duration = OQDurationLiteral(duration)
        _validate_uniqueness(self._frames, frames)
        self._program.delay(time=duration, qubits=frames)
        for frame in frames:
            self._frames[frame.id] = frame
        return self

    def barrier(self, frames: List[Frame]) -> PulseSequence:
        """
        Adds an instruction to align the frame clocks to the latest time across all the specified
        frames.

        Args:
            frames (List[Frame]): Frames across which the frame clocks need to be aligned.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frames)
        self._program.barrier(qubits=frames)
        for frame in frames:
            self._frames[frame.id] = frame
        return self

    def play(self, frame: Frame, waveform: Waveform) -> PulseSequence:
        """
        Adds an instruction to play the specified waveform on the supplied frame.

        Args:
            frame (Frame): Frame on which the specified waveform signal would be output.
            waveform (Waveform): Waveform envelope specifying the signal to output on the
                specified frame.
        """
        _validate_uniqueness(self._frames, frame)
        _validate_uniqueness(self._waveforms, waveform)
        self._program.play(frame=frame, waveform=waveform)
        if isinstance(waveform, Parameterizable):
            for param in waveform.parameters:
                if isinstance(param, FreeParameterExpression):
                    for p in param.expression.free_symbols:
                        self._free_parameters.add(FreeParameter(p.name))
        self._frames[frame.id] = frame
        self._waveforms[waveform.id] = waveform
        return self

    def capture_v0(self, frame: Frame) -> PulseSequence:
        """
        Adds an instruction to capture the bit output from measuring the specified frame.

        Args:
            frame (Frame): Frame on which the capture operation needs
                to be performed.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        # TODO: Replace with the public method when available.
        self._program._add_function_statement("capture_v0", [frame])
        self._capture_v0_count += 1
        self._frames[frame.id] = frame
        return self

    def make_bound_pulse_sequence(self, param_values: Dict[str, float]) -> PulseSequence:
        """
        Binds FreeParameters based upon their name and values passed in. If parameters
        share the same name, all the parameters of that name will be set to the mapped value.

        Args:
            param_values (Dict[str, Number]):  A mapping of FreeParameter names
                to a value to assign to them.

        Returns:
            PulseSequence: Returns a PulseSequence with all present parameters fixed to
            their respective values.
        """
        program = deepcopy(self._program)
        tree: ast.Program = program.to_ast(include_externs=False, ignore_undeclared=True)
        new_tree: ast.Program = _FreeParameterWalker(param_values).visit(tree)

        new_program = Program()
        new_program.declared_vars = program.declared_vars
        new_program.undeclared_vars = program.undeclared_vars
        for x in new_tree.statements:
            new_program.add_statement(x)

        new_pulse_sequence = PulseSequence()
        new_pulse_sequence._program = new_program
        new_pulse_sequence._frames = deepcopy(self._frames)
        new_pulse_sequence._waveforms = {
            wf.id: wf.bind_values(**param_values) if isinstance(wf, Parameterizable) else wf
            for wf in deepcopy(self._waveforms).values()
        }

        # Update waveforms to bind values
        for v in new_program.undeclared_vars:
            if v in self._waveforms:
                new_program.undeclared_vars[v] = new_pulse_sequence._waveforms[
                    v
                ].to_oqpy_expression()

        new_pulse_sequence._capture_v0_count = self._capture_v0_count
        new_pulse_sequence._free_parameters = set(
            [p for p in self._free_parameters if p.name not in param_values]
        )

        return new_pulse_sequence

    def to_ir(self) -> str:
        """Returns a str representing the OpenPulse program encoding the PulseSequence."""

        program = deepcopy(self._program)
        if self._capture_v0_count:
            register_identifier = "psb"
            program.declare(
                BitVar[self._capture_v0_count](ident=register_identifier), to_beginning=True
            )
            tree = program.to_ast(encal=True, include_externs=False)
            tree = _IRQASMTransformer(register_identifier).visit(tree)
        else:
            tree = program.to_ast(encal=True, include_externs=False)
        return _ast_to_qasm(tree)

    def _format_parameter_ast(self, parameter):
        if isinstance(parameter, FreeParameterExpression):
            for p in parameter.expression.free_symbols:
                self._free_parameters.add(FreeParameter(p.name))
            return FreeParameterExpressionIdentifier(parameter)
        return parameter


# TODO: See if this can be merged with the visualization parser.
class _FreeParameterWalker(QASMTransformer):
    """Walk the AST and evaluate FreeParameterExpressions."""

    def __init__(self, param_values: Dict[str, float]):
        self.param_values = param_values
        super().__init__()

    def visit_FreeParameterExpressionIdentifier(self, identifier: ast.Identifier):
        new_value = identifier.expression.subs(self.param_values)
        if isinstance(new_value, FreeParameterExpression):
            return FreeParameterExpressionIdentifier(new_value)
        else:
            return ast.FloatLiteral(new_value)

    def visit_DurationLiteral(self, duration_literal: DurationLiteral):
        duration = duration_literal.value
        if not isinstance(duration, FreeParameterExpression):
            return duration_literal
        return DurationLiteral(duration.subs(self.param_values), duration_literal.unit)


# TODO: Remove once oqpy introduces these validations.
def _validate_uniqueness(
    mapping: Dict[str, Any], values: Union[Frame, Waveform, List[Frame], List[Waveform]]
):
    if not isinstance(values, list):
        values = [values]

    for value in values:
        if value.id in mapping and mapping[value.id] != value:
            raise ValueError(
                f"{value.id} has already been used for defining {mapping[value.id]} "
                f"which differs from {value}"
            )


class _IRQASMTransformer(QASMTransformer):
    """
    QASMTransformer which walks the AST and makes the necessary modifications needed
    for IR generation. Currently, it performs the following operations:
      * Replaces capture_v0 function calls with assignment statements, assigning the
        readout value to a bit register element.
    """

    def __init__(self, register_identifier: Optional[str] = None):
        self._register_identifier = register_identifier
        self._capture_v0_count = 0
        super().__init__()

    def visit_ExpressionStatement(self, expression_statement: ast.ExpressionStatement):
        if (
            isinstance(expression_statement.expression, ast.FunctionCall)
            and expression_statement.expression.name.name == "capture_v0"
            and self._register_identifier
        ):
            # For capture_v0 nodes, it replaces it with classical assignment statements
            # of the form:
            # b[0] = capture_v0(...)
            # b[1] = capture_v0(...)
            new_val = ast.ClassicalAssignment(
                # Ideally should use IndexedIdentifier here, but this works since it is just
                # for printing.
                ast.Identifier(name=f"{self._register_identifier}[{self._capture_v0_count}]"),
                ast.AssignmentOperator["="],
                expression_statement.expression,
            )
            self._capture_v0_count += 1
            return new_val
        else:
            return expression_statement


class _PulsePrinter(Printer):
    """Walks the AST and prints it to an OpenQASM3 string."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def visit_FreeParameterExpressionIdentifier(
        self, node: ast.Identifier, context: PrinterState
    ) -> None:
        self.stream.write(str(node.expression.expression))

    def visit_DurationLiteral(self, node: DurationLiteral, context: PrinterState):
        duration = node.value
        if isinstance(duration, FreeParameterExpression):
            self.stream.write(f"({duration.expression}){node.unit.name}")
        else:
            super().visit_DurationLiteral(node, context)

    def visit_ClassicalDeclaration(self, node: ast.ClassicalDeclaration, context: PrinterState):
        # Skip port declarations in output
        if not isinstance(node.type, ast.PortType):
            super().visit_ClassicalDeclaration(node, context)


# TODO: Refactor printing functionality to a separate module
def _ast_to_qasm(ast: ast.Program) -> str:
    out = io.StringIO()
    _PulsePrinter(out, indent="    ").visit(ast)
    return out.getvalue().strip()
